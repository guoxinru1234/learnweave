# backend/app/agents/planner_agent.py
import json
import re
from ..core.llm import get_llm_client


class PlannerAgent:
    """规划者：根据讲次内容生成视频分镜脚本（支持重点/易混淆点标记）"""

    def __init__(self):
        print("[INFO] PlannerAgent 初始化 (统一 LLMClient)...")
        self.llm = get_llm_client()

    def _call_llm(self, prompt: str, max_tokens: int = 3000) -> str:
        """同步调用 LLM（底层 LLMClient 自带 3 次重试）"""
        return self.llm.chat_sync(
            [{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=max_tokens,
        )

    def generate_script(self, lecture_data: dict, difficulty: str = "medium") -> dict:
        prompt = f"""
你是一位资深的教育视频导演。请根据以下讲义内容，生成一个教学视频的分镜脚本。

讲义内容：
{json.dumps(lecture_data, ensure_ascii=False, indent=2)}

要求：
1. 将内容分为 12-15 幕，每幕 4-6 秒
2. 为每幕分配 type：
   - intro（引入，1-2幕）
   - explain（解释，4-6幕，把概念和原理拆成多个简短句子）
   - key_point（重点）[Star] 必须来自讲义中的 key_points
   - confusion_point（易混淆点）[?]
   - summary（总结）
3. 重点幕使用金色标记，易混淆点使用红色标记
4. 每幕文字控制在 25 字以内，便于视频显示

输出 JSON 格式：
```json
{{
    "title": "讲次标题",
    "scenes": [
        {{"scene_id": 1, "type": "intro", "text": "画面文字", "duration": 4}},
        ...
    ]
}}
```
只输出 JSON，不要有其他文字。
"""
        try:
            content = self._call_llm(prompt)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content)
        except Exception as e:
            print(f"PlannerAgent API 调用失败，使用备选方案: {e}")
            return self.generate_script_fallback(lecture_data)

    def generate_script_fallback(self, lecture_data: dict) -> dict:
        title = lecture_data.get('title', '课程内容')
        content = lecture_data.get('content', {})

        scenes = []
        scene_id = 1

        scenes.append({
            "scene_id": scene_id,
            "type": "intro",
            "text": f"[intro] {title}",
            "duration": 4
        })
        scene_id += 1

        intro = content.get('introduction', '')
        if intro:
            intro_text = intro[:40] if len(intro) > 40 else intro
            scenes.append({
                "scene_id": scene_id,
                "type": "explain",
                "text": intro_text,
                "duration": 5
            })
            scene_id += 1

        core = content.get('core_knowledge', {})
        concept = core.get('concept', '')
        if concept:
            concept_parts = concept.split('。')
            for part in concept_parts:
                part = part.strip()
                if part and len(part) > 5:
                    part_text = part[:40] + ('...' if len(part) > 40 else '')
                    scenes.append({
                        "scene_id": scene_id,
                        "type": "explain",
                        "text": part_text,
                        "duration": 5
                    })
                    scene_id += 1

        principles = core.get('principles', '')
        if principles:
            principle_parts = re.split(r'\d+\.', principles)
            if len(principle_parts) <= 1:
                principle_parts = re.split(r'[。.；;]', principles)
            for i, part in enumerate(principle_parts):
                part = part.strip()
                if part and len(part) > 5:
                    label = f"原理{i+1}：" if i < len(principle_parts)-1 else ""
                    part_text = (label + part)[:40]
                    scenes.append({
                        "scene_id": scene_id,
                        "type": "explain",
                        "text": part_text,
                        "duration": 5
                    })
                    scene_id += 1

        steps = core.get('steps', [])
        for step in steps[:4]:
            if step:
                step_text = step[:35] if len(step) > 35 else step
                scenes.append({
                    "scene_id": scene_id,
                    "type": "explain",
                    "text": step_text,
                    "duration": 4
                })
                scene_id += 1

        example = core.get('example', '')
        if example:
            example_text = f"示例：{example[:35]}"
            scenes.append({
                "scene_id": scene_id,
                "type": "explain",
                "text": example_text,
                "duration": 5
            })
            scene_id += 1

        key_points = content.get('key_points', [])
        for i, point in enumerate(key_points[:4]):
            if point:
                short_point = point[:40] + ('...' if len(point) > 40 else '')
                scenes.append({
                    "scene_id": scene_id,
                    "type": "key_point",
                    "text": f"[Star] 重点{i+1}：{short_point}",
                    "duration": 6,
                    "emphasis": True
                })
                scene_id += 1

        confusion = content.get('confusion_points', {})
        if confusion and confusion.get('point'):
            confusion_text = confusion.get('point', '')[:35]
            scenes.append({
                "scene_id": scene_id,
                "type": "confusion_point",
                "text": f"[?] 易混淆：{confusion_text}",
                "duration": 5,
                "emphasis": True
            })
            scene_id += 1
            if confusion.get('takeaway'):
                takeaway_text = confusion.get('takeaway', '')[:35]
                scenes.append({
                    "scene_id": scene_id,
                    "type": "confusion_point",
                    "text": f"[OK] 关键区别：{takeaway_text}",
                    "duration": 5,
                    "emphasis": True
                })
                scene_id += 1

        summary = content.get('summary', '')
        if summary:
            summary_text = f"[OK] 总结：{summary[:40]}"
            scenes.append({
                "scene_id": scene_id,
                "type": "summary",
                "text": summary_text,
                "duration": 5
            })
        else:
            scenes.append({
                "scene_id": scene_id,
                "type": "summary",
                "text": "[OK] 学习完成！",
                "duration": 3
            })

        return {"title": title, "scenes": scenes}
