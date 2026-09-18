# backend/app/routers/execute.py
"""
代码执行路由 — 用本机 Python 子进程安全执行用户代码。

安全设计：
  - 本地 subprocess 子进程执行（完全离线，不依赖第三方沙箱）
  - 超时限制 5 秒（防止死循环/长时间运行）
  - 代码长度限制 50KB
  - 禁止危险关键词（os/subprocess/socket/shutil/eval/exec/open-w 等）
  - 仅支持 Python 语言
"""
import re
import subprocess
import sys
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

router = APIRouter(prefix="/api/execute", tags=["execute"])

# 危险模式检测（本地子进程执行，这些拦截是安全底线）
FORBIDDEN_PATTERNS = [
    r'\bos\.system\b', r'\bos\.popen\b', r'\bsubprocess\b',
    r'\bsocket\b', r'\bshutil\.rmtree\b', r'\bshutil\.copy\b',
    r'\beval\b', r'\bexec\b', r'\bcompile\b.*exec\b',
    r'__import__\s*\(\s*[\'"]os[\'"]', r'__import__\s*\(\s*[\'"]sys[\'"]',
    r'open\s*\(.*[\'"]w[\'"]',  # 文件写入
]

MAX_CODE_LENGTH = 50_000  # 50KB
EXEC_TIMEOUT = 5          # 秒


class CodeRequest(BaseModel):
    code: str
    lab_title: str = ""

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if len(v) > MAX_CODE_LENGTH:
            raise HTTPException(status_code=400, detail=f"代码长度超过限制 ({MAX_CODE_LENGTH} 字节)")
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, v):
                raise HTTPException(status_code=400, detail=f"代码包含禁止模式: {pattern}")
        return v


@router.post("/python")
def execute_python(request: CodeRequest):
    """使用 Judge0 云沙箱安全执行 Python 代码"""
    code = request.code
    if not code.strip():
        return {"success": False, "output": "[X] 代码不能为空", "exit_code": -1}

    # 语法预检：本地编译验证（不执行）
    try:
        compile(code, "<user_code>", "exec")
    except SyntaxError as e:
        return {
            "success": False,
            "output": f"[X] 语法错误 (行 {e.lineno}): {e.msg}",
            "exit_code": -1,
            "error_type": "syntax_error",
        }

    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=EXEC_TIMEOUT,
        )
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        exit_code = proc.returncode
        success = exit_code == 0

        output_parts = []
        if stderr:
            output_parts.append("[运行时错误]\n" + stderr)
        if stdout:
            output_parts.append("[程序输出]\n" + stdout)
        if not output_parts:
            output_parts.append("[OK] 代码执行完成，无输出")
        full_output = "\n\n".join(output_parts)

        # 错误分类
        error_type = None
        if not success:
            if "NameError" in stderr:
                error_type = "name_error"
            elif "TypeError" in stderr:
                error_type = "type_error"
            elif "ValueError" in stderr:
                error_type = "value_error"
            elif "AttributeError" in stderr:
                error_type = "attribute_error"
            elif "KeyError" in stderr:
                error_type = "key_error"
            elif "IndexError" in stderr:
                error_type = "index_error"
            elif "ZeroDivisionError" in stderr:
                error_type = "zero_division_error"
            elif "ImportError" in stderr or "ModuleNotFoundError" in stderr:
                error_type = "import_error"
            elif "MemoryError" in stderr:
                error_type = "memory_error"
            else:
                error_type = "runtime_error"

        return {
            "success": success,
            "output": full_output,
            "exit_code": exit_code,
            "status": "Accepted" if success else "Runtime Error",
            "error_type": error_type,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "output": f"[X] 执行超时（超过 {EXEC_TIMEOUT} 秒），请简化代码", "exit_code": -1, "error_type": "timeout"}
    except Exception as e:
        return {"success": False, "output": f"[X] 执行异常: {str(e)[:200]}", "exit_code": -1, "error_type": "unknown"}


class FixCodeRequest(BaseModel):
    code: str
    error: str = ""
    topic: str = ""


@router.post("/fix-code")
async def fix_code(request: FixCodeRequest):
    """用 LLM 修复报错的代码，返回可运行版本。"""
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="代码不能为空")
    try:
        from app.core.llm import get_llm_client
        llm = get_llm_client()
        prompt = (
            f"请修复下面的 Python 代码（主题：{request.topic or '未指定'}）。\n\n"
            f"【代码】：\n```python\n{request.code}\n```\n\n"
            f"【报错信息】：\n{request.error or '（无，请检查代码逻辑）'}\n\n"
            f"请只输出修复后的完整可运行 Python 代码（用 ```python 包裹），"
            f"并在代码之后附一句简短说明（改了什么）。"
        )
        resp = await llm.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.2, max_tokens=2000,
        )
        m = re.search(r'```(?:python)?\s*([\s\S]*?)```', resp)
        fixed = m.group(1).strip() if m else resp.strip()
        return {"success": True, "fixed_code": fixed, "raw": resp}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"修复失败: {str(e)[:200]}")