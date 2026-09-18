import json
import re
import ast
import subprocess
import tempfile
import os
from typing import Dict, Any, List, Optional
from ..core.llm import get_llm_client

class LabGraderAgent:
    """实验批改智能体 - 语法/AST → 受控执行 → 规则验证 → LLM 分析 → 综合评分"""

    def __init__(self):
        self.llm = get_llm_client()

    async def grade_code(
        self,
        code: str,
        lab_title: str,
        task_description: str = "",
        task_details: str = "",      # 新增：详细任务要求
        reference_answer: str = ""   # 新增：参考答案
    ) -> Dict[str, Any]:
        """
        综合评分：语法/AST → 危险检测 → 受控执行 → 规则验证 → LLM 分析
        """
        # 1. 语法检查（AST）
        syntax_errors = self._check_syntax(code)
        if syntax_errors:
            return {
                "score": max(0, 100 - len(syntax_errors) * 20),
                "passed": False,
                "errors": syntax_errors,
                "suggestions": ["请修正语法错误后重新提交"],
                "comment": "代码存在语法错误，请修正后重试。",
                "syntax_ok": False,
            }

        # 2. 危险代码检测（禁止访问系统资源）
        dangerous = self._check_dangerous_code(code)
        if dangerous:
            return {
                "score": 0,
                "passed": False,
                "errors": dangerous,
                "suggestions": ["请移除危险操作（禁止访问系统资源）"],
                "comment": "代码包含危险操作，已拒绝执行。",
                "syntax_ok": True,
                "dangerous": True,
            }

        # 3. 受控执行（真实运行代码）
        exec_result = self._execute_code(code)

        # 4. 规则验证（核心知识点：是否用 groupby 聚合）
        verify = self._verify_groupby(code)

        # 5. LLM 深度分析（传入执行结果 + 规则验证，综合评分）
        try:
            result = await self._grade_with_llm(
                code, lab_title, task_description, task_details, reference_answer,
                exec_result=exec_result, verify=verify,
            )
            result["syntax_ok"] = True
            result["execution"] = exec_result
            result["verification"] = verify
            return result
        except Exception as e:
            print(f"LLM 批改失败: {e}")
            fb = self._fallback_grade(code, lab_title)
            fb["execution"] = exec_result
            fb["verification"] = verify
            return fb

    async def _grade_with_llm(
        self,
        code: str,
        lab_title: str,
        task_description: str,
        task_details: str,
        reference_answer: str,
        exec_result: Optional[Dict[str, Any]] = None,
        verify: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """使用 DeepSeek 严格批改代码（结合真实执行结果 + 规则验证）。"""

        # 构建任务详情部分
        task_section = ""
        if task_details:
            task_section = f"\n【实验任务详细要求】：\n{task_details}\n"
        elif task_description:
            task_section = f"\n【实验任务】：\n{task_description}\n"

        # 构建参考答案部分
        reference_section = ""
        if reference_answer:
            reference_section = f"""
【参考答案（用于评判，请勿直接告知学生）】：
{reference_answer}
"""

        # 构建执行结果 + 规则验证部分（真实运行证据）
        exec_section = ""
        if exec_result:
            if exec_result.get("ran"):
                exec_section = f"""
【代码真实执行结果】：
运行成功，标准输出：
{exec_result.get("stdout", "")[:500]}
"""
            elif exec_result.get("error"):
                exec_section = f"""
【代码真实执行结果】：
执行失败：{exec_result.get("error")}
"""
            else:
                exec_section = f"""
【代码真实执行结果】：
运行失败（returncode={exec_result.get("returncode")}）
stderr: {exec_result.get("stderr", "")[:300]}
"""

        verify_section = ""
        if verify:
            verify_section = f"""
【规则验证（核心知识点）】：
使用 pandas: {verify.get("uses_pandas")}
使用 groupby: {verify.get("uses_groupby")}
使用聚合函数: {verify.get("uses_agg")}
"""

        system_prompt = (
            "你是一位严谨的Python数据分析课程实验助教，负责批改学生的实验代码。\n"
            "请严格按照以下规则进行批改：\n"
            "\n"
            "**批改维度与扣分规则**：\n"
            "1. 语法正确性（30分）：括号匹配、关键字、语句完整性。每发现一个语法错误扣10分。\n"
            "2. 代码逻辑（30分）：是否实现了任务要求的功能。逻辑错误每处扣10-15分。\n"
            "3. 任务完成度（20分）：是否完成了所有任务要求。未完成的任务每项扣5-10分。\n"
            "4. 代码规范（10分）：命名规范、格式、注释。不规范处每处扣2-5分。\n"
            "5. 输出结果（10分）：是否有正确的输出操作（print/head/describe等）。缺少输出扣10分。\n"
            "\n"
            "**评分要求**：\n"
            "- 60分及以上为通过（passed: true）\n"
            "- 评分必须客观、严格\n"
            "- 错误和建议要具体，指出问题所在\n"
            "\n"
            "严格按照 JSON 格式返回结果。"
        )

        user_prompt = (
            f"实验名称：{lab_title}\n"
            f"{task_section}"
            f"{reference_section}"
            f"{exec_section}"
            f"{verify_section}"
            f"\n"
            f"学生提交的代码：\n"
            f"```python\n"
            f"{code}\n"
            f"```\n"
            f"\n"
            f"请逐行分析这份代码，找出所有问题，并以 JSON 格式返回：\n"
            f"{{\n"
            f'  "score": 0-100 的整数（根据扣分规则严格计算）,\n'
            f'  "passed": true/false（60分及以上为true）,\n'
            f'  "errors": ["错误1（含行号）", "错误2（含行号）"],\n'
            f'  "suggestions": ["具体改进建议1", "具体改进建议2"],\n'
            f'  "comment": "总体评语（20字以内，指出最大问题）"\n'
            f"}}\n"
            f"\n"
            f"注意：只返回 JSON，不要有其他文字。"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = await self.llm.chat(messages, temperature=0.2)  # 降低温度，更稳定

        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                score = result.get("score", 60)
                # 确保评分在合理范围内
                score = max(0, min(100, score))
                return {
                    "score": score,
                    "passed": result.get("passed", score >= 60),
                    "errors": result.get("errors", []),
                    "suggestions": result.get("suggestions", []),
                    "comment": result.get("comment", "批改完成")
                }
        except Exception as e:
            print(f"解析 JSON 失败: {e}")
            print(f"原始响应: {response}")

        return self._extract_from_text(response)

    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """从 LLM 返回的文本中提取信息（容错）"""
        score = 60
        passed = True
        errors = []
        suggestions = []
        comment = "批改完成"

        # 提取评分
        score_match = re.search(r'(\d+)\s*分', text)
        if score_match:
            score = min(100, max(0, int(score_match.group(1))))

        # 提取错误
        error_patterns = [
            r'错误[：:]\s*(.+?)(?:\n|$)',
            r'问题[：:]\s*(.+?)(?:\n|$)',
            r'第\s*(\d+)\s*行[：:]\s*(.+?)(?:\n|$)'
        ]
        for pattern in error_patterns:
            matches = re.findall(pattern, text)
            errors.extend([m if isinstance(m, str) else f"第{m[0]}行：{m[1]}" for m in matches])
            if len(errors) >= 5:
                break

        # 提取建议
        suggest_patterns = [r'建议[：:]\s*(.+?)(?:\n|$)', r'优化[：:]\s*(.+?)(?:\n|$)']
        for pattern in suggest_patterns:
            matches = re.findall(pattern, text)
            suggestions.extend(matches[:3])

        # 提取评语
        comment_match = re.search(r'评语[：:]\s*(.+?)(?:\n|$)', text)
        if comment_match:
            comment = comment_match.group(1).strip()[:50]
        elif len(errors) > 0:
            comment = f"发现 {len(errors)} 个问题，请修正"
        elif suggestions:
            comment = "代码基本正确，仍有优化空间"

        passed = score >= 60

        return {
            "score": score,
            "passed": passed,
            "errors": errors[:5],
            "suggestions": suggestions[:3],
            "comment": comment
        }

    def _fallback_grade(self, code: str, lab_title: str) -> Dict[str, Any]:
        """降级方案：规则匹配批改（Python 数据分析关键词）。"""
        result = {
            "score": 60,
            "passed": True,
            "errors": [],
            "suggestions": [],
            "comment": "使用规则引擎批改（LLM 服务不可用）"
        }

        code_lower = code.lower()
        keywords = ['pandas', 'numpy', 'groupby', 'dataframe', 'read_csv', 'agg']
        missing = [kw for kw in keywords if kw not in code_lower]

        if missing:
            result["errors"].append(f"未使用数据分析核心库/方法: {', '.join(missing[:3])}")
            result["score"] = max(0, 60 - len(missing) * 10)

        lines = [l for l in code.split('\n') if l.strip()]
        if len(lines) < 3:
            result["errors"].append("代码行数太少，请完成实验任务")
            result["score"] = max(0, result["score"] - 20)

        if not any(action in code_lower for action in ['print', 'head', 'describe', 'groupby']):
            result["suggestions"].append("建议添加 print() 或 head() 输出分析结果")

        result["passed"] = result["score"] >= 60

        if result["passed"]:
            result["comment"] = "代码基本正确，可以继续优化。"
        else:
            result["comment"] = "需要补充完整代码。"

        return result

    def _check_syntax(self, code: str) -> List[str]:
        """Python 语法检查（AST，替代旧的手写 val/括号规则）。"""
        errors = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"语法错误（第{e.lineno or '?'}行）: {e.msg}")
        return errors[:5]

    def _check_dangerous_code(self, code: str) -> List[str]:
        """AST 检查危险操作（禁止访问系统资源）。"""
        dangerous = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for n in node.names:
                        if n.name in ('os', 'sys', 'subprocess', 'shutil', 'socket'):
                            dangerous.append(f"禁止导入模块: {n.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module in ('os', 'sys', 'subprocess', 'shutil', 'socket'):
                        dangerous.append(f"禁止导入模块: {node.module}")
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in ('eval', 'exec', 'open', '__import__'):
                        dangerous.append(f"禁止调用: {node.func.id}()")
        except SyntaxError:
            pass
        return dangerous[:5]

    def _execute_code(self, code: str, timeout: int = 5) -> Dict[str, Any]:
        """受控执行 Python 代码（subprocess 隔离 + 超时）。"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            tmp_path = f.name
        try:
            proc = subprocess.run(
                ['python', tmp_path],
                capture_output=True, text=True, timeout=timeout,
            )
            return {
                "ran": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": (proc.stdout or "").strip(),
                "stderr": (proc.stderr or "").strip(),
            }
        except subprocess.TimeoutExpired:
            return {"ran": False, "error": f"执行超时（>{timeout}s）"}
        except Exception as e:
            return {"ran": False, "error": str(e)}
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def _verify_groupby(self, code: str) -> Dict[str, Any]:
        """规则验证：是否使用 Pandas groupby 聚合（核心知识点）。"""
        code_lower = code.lower()
        return {
            "uses_pandas": 'pandas' in code_lower or 'pd.' in code_lower,
            "uses_groupby": 'groupby' in code_lower,
            "uses_agg": any(kw in code_lower for kw in ['agg', 'sum(', 'mean(', 'count(']),
        }


def get_lab_grader() -> LabGraderAgent:
    return LabGraderAgent()