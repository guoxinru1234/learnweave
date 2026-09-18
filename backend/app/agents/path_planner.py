"""路径规划 Agent — LLM 驱动的个性化学习路径生成"""
import json
import re
from typing import List, Dict

from ..core.llm import get_llm_client
from ..core.database import list_labs

PATH_SYSTEM_PROMPT = """你是一位资深教育路径规划专家。

根据学生的 6 维学情画像，生成个性化学习路径。要求：
1. 分析 6 个维度的强弱分布，找出最需要加强的 2-3 个维度
2. 为每个模块分配学习时长和重点等级（strengthen / normal / fast）
3. 薄弱维度要给出具体的改进建议和推荐资源
4. 学习节奏要匹配学生整体水平
5. 输出严格的 JSON 格式

输出 JSON 结构（必须包含 3-5 条不同路径）：
{
  "overall_assessment": "对学生的综合评估（50-80字）",
  "paths": [
    {
      "name": "路径名称：如「稳健基础路线」「快速进阶路线」「实战强化路线」",
      "description": "这条路径适合什么类型的学生（20-30字）",
      "suitable_for": "适合画像特征（如：理论基础强但实践弱）",
      "verification": "验证说明：因为学生X维度仅Y分(最弱)，Z维度W分(最强)，所以推荐此路径（30-50字）",
      "total_hours": 18.0,
      "modules": [
        {"module": "模块名", "lectures": [1,2], "hours": 3.0, "focus": "strengthen", "reason": "安排理由"}
      ]
    }
  ],
  "weak_focus": [
    {"dimension": "维度名", "current_score": 45, "suggestion": "提升建议", "expected_improvement": "预期效果"}
  ]
}

要求：
- 最少生成 3 条路径，最多 5 条
- 每条路径针对不同的学习风格和画像特征
- 路径之间要有明显差异（不是简单调顺序）
- 每条路径附验证说明（为什么推荐这条路径）"""


class PathPlannerAgent:
    """LLM 驱动的路径规划 Agent。

    根据 6 维画像分数，调用 LLM 生成个性化学习路径和薄弱点改进建议。
    同时融合硬编码模块结构作为基础参考。
    """

    # 维度名称映射
    DIM_NAMES = ["理论基础", "编程能力", "实践操作", "问题排查", "数据思维", "自学能力"]

    def __init__(self):
        self.llm = get_llm_client()
        self.modules = [
            {"id": 1, "name": "Python基础", "lectures": [1, 2], "priority": 1},
            {"id": 2, "name": "NumPy与Pandas", "lectures": [3, 4, 5, 6, 7, 8], "priority": 2},
            {"id": 3, "name": "数据可视化与实战", "lectures": [9, 10, 11, 12], "priority": 3},
        ]

    def plan(self, profile: List[int]) -> Dict:
        """LLM 驱动的路径规划。

        先用规则计算基础数据，再交由 LLM 做深度分析和建议生成。
        若 LLM 不可用，回退到规则计算。
        """
        dim_scores = dict(zip(self.DIM_NAMES, profile))
        overall = sum(s for s in profile if s > 0) / max(1, len([s for s in profile if s > 0]))

        # 构建 LLM prompt
        prompt = self._build_prompt(dim_scores, overall)

        try:
            raw = self.llm.chat_sync(
                [{"role": "system", "content": PATH_SYSTEM_PROMPT},
                 {"role": "user", "content": prompt}],
                temperature=0.4, max_tokens=1500,
            )
            parsed = self._parse_json(raw)
            if parsed:
                return self._enrich_with_labs(parsed, profile)
        except Exception as e:
            print(f"[PathPlanner] LLM 调用失败，回退规则计算: {e}")

        return self._fallback_plan(profile)

    def _build_prompt(self, dim_scores: dict, overall: float) -> str:
        """构建 LLM 输入 prompt。"""
        dim_lines = "\n".join([
            f"- {name}: {score} 分"
            for name, score in dim_scores.items()
        ])

        module_lines = "\n".join([
            f"- {m['name']}（讲次 {min(m['lectures'])}-{max(m['lectures'])}）"
            for m in self.modules
        ])

        return f"""请根据以下学生画像生成个性化学习路径。

【6 维画像分数】（满分 100）：
{dim_lines}

综合分数：{overall:.0f} 分

【可用课程模块】：
{module_lines}

【出路径要求】：
- 学习节奏根据综合分数：<40 放慢、40-60 正常、>60 可加快
- 薄弱维度（分数最低的 2-3 个）对应的模块标记为 strengthen
- 每个模块给出预估学习时长和学习理由
- 每个薄弱维度给出具体的提升建议

只输出 JSON。"""

    def _parse_json(self, raw: str) -> dict | None:
        """从 LLM 回复中提取 JSON。"""
        try:
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
            # 容错处理
            m = re.search(r'\{[\s\S]*\}', raw)
            if m:
                return json.loads(m.group())
        except (json.JSONDecodeError, IndexError):
            pass
        return None

    def _enrich_with_labs(self, parsed: dict, profile: list) -> dict:
        """用实验数据丰富 LLM 生成的路径。适配 paths（多条路径）格式。"""
        labs = list_labs()
        paths = parsed.get("paths", [])
        if not paths:
            # 兼容旧格式
            old_path = parsed.get("path", [])
            if old_path:
                paths = [{"name": "推荐路径", "description": "", "modules": old_path}]
                parsed["paths"] = paths

        for p in paths:
            for item in p.get("modules", []):
                mod_lectures = []
                for m in self.modules:
                    if m["name"] == item.get("module"):
                        mod_lectures = m["lectures"]
                        break
                item["labs"] = [
                    lab for lab in labs
                    if any(lid in mod_lectures for lid in lab.get("lecture_ids", []))
                ][:3]

        # 确保至少 3 条路径
        while len(paths) < 3 and len(paths) < 5:
            paths.append({
                "name": ["稳健基础路线", "快速进阶路线", "实战强化路线", "综合平衡路线", "考试冲刺路线"][len(paths)],
                "description": "额外备选路径",
                "suitable_for": "不同学习偏好",
                "total_hours": 15.0,
                "modules": [
                    {"module": m["name"], "lectures": m["lectures"],
                     "hours": round(len(m["lectures"]) * 1.5, 1),
                     "focus": "normal", "reason": "基础模块学习"}
                    for m in self.modules
                ],
            })

        parsed["profile_based"] = True
        parsed["lab_integrated"] = True
        parsed["generated_by"] = "llm"
        parsed["overall_score"] = round(
            sum(s for s in profile if s > 0) / max(1, len([s for s in profile if s > 0])), 1
        )
        return parsed

    def _fallback_plan(self, profile: List[int]) -> dict:
        """LLM 不可用时的规则回退方案。"""
        indexed = list(enumerate(profile))
        indexed.sort(key=lambda x: x[1])
        weak_indices = [i for i, _ in indexed[:2]]
        overall = sum(s for s in profile if s > 0) / max(1, len([s for s in profile if s > 0]))

        if overall < 40:
            time_scale, rhythm = 1.8, "slow"
        elif overall < 60:
            time_scale, rhythm = 1.3, "normal"
        else:
            time_scale, rhythm = 0.6, "fast"

        # 薄弱维度 → 对应模块
        dim_module_map = {
            0: [1], 1: [1, 2], 2: [2, 3], 3: [2], 4: [2, 3], 5: [1, 2, 3],
        }
        focus_ids = set()
        for wi in weak_indices:
            focus_ids.update(dim_module_map.get(wi, []))

        labs = list_labs()
        plans = []
        for mod in self.modules:
            mid = mod["id"]
            plans.append({
                "module": mod["name"],
                "lectures": mod["lectures"],
                "estimated_hours": round(len(mod["lectures"]) * 1.5 * time_scale, 1),
                "focus": "strengthen" if mid in focus_ids else "normal",
                "priority": mod["priority"],
                "reason": f"模块{mod['name']}，节奏{rhythm}" if mid not in focus_ids else "薄弱维度关联模块，需加强",
                "labs": [lab for lab in labs if any(lid in mod["lectures"] for lid in lab.get("lecture_ids", []))][:3],
            })

        weak_info = [
            {"dimension": self.DIM_NAMES[wi], "current_score": profile[wi],
             "suggestion": f"重点加强{self.DIM_NAMES[wi]}相关课程学习",
             "expected_improvement": "预计提升 10-20 分"}
            for wi in weak_indices
        ]

        return {
            "overall_assessment": f"综合分数 {overall:.0f}，节奏 {rhythm}",
            "learning_rhythm": rhythm,
            "pace_reason": "基于综合分数自动判定",
            "path": plans,
            "weak_focus": weak_info,
            "profile_based": True,
            "lab_integrated": True,
            "generated_by": "fallback_rules",
            "overall_score": round(overall, 1),
        }
