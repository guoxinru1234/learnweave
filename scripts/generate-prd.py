#!/usr/bin/env python3
"""从竞赛要求 + UI设计规范生成 Ralph PRD"""
import json, sys, os

OUTPUT = sys.argv[1]

prd = {
    "project": "LearnMate",
    "branchName": "feature/learnmate-core",
    "description": "第十五届中国软件杯 A3赛题：基于大模型的个性化资源生成与学习多智能体系统",
    "stories": [
        {
            "id": "S01",
            "passes": False,
            "priority": 1,
            "title": "后端 FastAPI 健康检查 + 知识库 API",
            "description": "实现 /health 端点和 /api/knowledge/lectures 列表接口，返回知识库 index.json 内容。",
            "acceptance": ["GET /health 返回 200", "GET /api/knowledge/lectures 返回讲座列表"],
            "files": ["backend/app/main.py"],
            "tests": ["tests/test_health.py::test_backend_structure"]
        },
        {
            "id": "S02",
            "passes": False,
            "priority": 1,
            "title": "RAG 检索引擎实现",
            "description": "基于 ChromaDB 实现向量检索，从知识库 Markdown 文件构建向量索引，支持语义搜索。",
            "acceptance": ["RAGEngine.search('Shuffle') 返回相关讲座", "支持 top_k 参数控制返回数量"],
            "files": ["backend/app/rag/engine.py", "backend/app/rag/__init__.py"],
            "tests": ["tests/test_health.py::test_rag_module"]
        },
        {
            "id": "S03",
            "passes": False,
            "priority": 1,
            "title": "学习者画像 API + 对话式构建",
            "description": "实现 LearnerProfile 模型的 CRUD API，以及对话式画像构建的 6 轮问答逻辑。",
            "acceptance": ["POST /api/profile/dialogue/start 开始对话", "POST /api/profile/dialogue/answer 处理答案并更新画像"],
            "files": ["backend/app/models/profile.py", "backend/app/agents/profile_agent.py"],
            "tests": ["tests/test_health.py"]
        },
        {
            "id": "S04",
            "passes": False,
            "priority": 2,
            "title": "学习路径规划 Agent",
            "description": "基于 6 维画像生成个性化学习路径，包括模块排序、时间预估、薄弱点加强。",
            "acceptance": ["输入画像数组返回路径 JSON", "薄弱维度自动标记加强建议"],
            "files": ["backend/app/agents/path_planner.py"],
            "tests": ["tests/test_health.py"]
        },
        {
            "id": "S05",
            "passes": False,
            "priority": 2,
            "title": "LangGraph 多Agent 编排器",
            "description": "实现 6 Agent 的 LangGraph 工作流：画像→路径→资源→出题→辅导→评估，支持流式输出。",
            "acceptance": ["编排器可执行完整流程", "每步输出阶段状态"],
            "files": ["backend/app/agents/orchestrator.py", "backend/app/agents/__init__.py"],
            "tests": ["tests/test_health.py"]
        },
        {
            "id": "S06",
            "passes": False,
            "priority": 3,
            "title": "Next.js Dashboard 页面",
            "description": "实现 Bento Grid 布局的 Dashboard，包含欢迎卡片、统计卡片、课程进度、资源推荐。使用 lucide-react 图标，Fira Sans 字体。",
            "acceptance": ["4 列统计卡片", "课程进度条 29%", "新建学习计划按钮"],
            "files": ["frontend/src/app/page.tsx"],
            "tests": []
        },
        {
            "id": "S07",
            "passes": False,
            "priority": 3,
            "title": "Next.js 学习空间页面",
            "description": "实现三栏布局：学习路径树 + 5 Tab 多模态内容(讲义/导图/代码/视频/练习) + AI 助手聊天。",
            "acceptance": ["路径树可折叠", "5 Tab 切换正常", "代码编辑器带行号和复制"],
            "files": ["frontend/src/app/learn/page.tsx"],
            "tests": []
        },
        {
            "id": "S08",
            "passes": False,
            "priority": 3,
            "title": "Next.js 画像页面 + 雷达图",
            "description": "实现 6 维雷达图(Canvas/SVG) + 画像详情卡片 + 对话式更新聊天面板。",
            "acceptance": ["雷达图渲染 6 维数据", "对话回答后雷达图动画更新"],
            "files": ["frontend/src/app/profile/page.tsx"],
            "tests": []
        },
        {
            "id": "S09",
            "passes": False,
            "priority": 3,
            "title": "Next.js 题库 + AI答疑 + 评估页面",
            "description": "实现题库(知识点分类/错题/模拟) + AI答疑(流式打字) + 评估(Bullet Chart)。",
            "acceptance": ["题库按知识点分类", "AI答疑流式打字效果", "评估页 Bullet Chart"],
            "files": ["frontend/src/app/quiz/page.tsx", "frontend/src/app/tutor/page.tsx", "frontend/src/app/assessment/page.tsx"],
            "tests": []
        },
        {
            "id": "S10",
            "passes": False,
            "priority": 4,
            "title": "深色模式 + 移动端响应式",
            "description": "全局深色/浅色模式切换(localStorage 持久化) + 768px 以下移动端抽屉侧边栏 + 底部 TabBar。",
            "acceptance": ["Ctrl+J 切换主题", "移动端侧边栏滑出", "底部 TabBar 显示"],
            "files": ["frontend/src/app/layout.tsx", "frontend/src/components/"],
            "tests": []
        },
        {
            "id": "S11",
            "passes": False,
            "priority": 4,
            "title": "多Agent 生成流水线 UI",
            "description": "实现创建课程 → 弹出 5 Agent 流水线动画(逐步完成) → 完成提示的完整交互。",
            "acceptance": ["流水线 5 步逐步完成动画", "每步显示 Agent 名称和产出"],
            "files": ["frontend/src/components/PipelineModal.tsx"],
            "tests": []
        },
        {
            "id": "S12",
            "passes": False,
            "priority": 5,
            "title": "新手引导 + 搜索 + 错误处理",
            "description": "首次访问 4 步引导 Tour + 搜索框实时建议下拉 + 错误横幅和重试卡片组件。",
            "acceptance": ["首次访问弹出引导", "搜索输入实时筛选", "错误横幅可关闭"],
            "files": ["frontend/src/components/"],
            "tests": []
        },
    ]
}

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(prd, f, ensure_ascii=False, indent=2)

print(f"PRD 已生成: {OUTPUT}")
print(f"故事总数: {len(prd['stories'])}")
print(f"优先级分布: P1={sum(1 for s in prd['stories'] if s['priority']==1)}, P2={sum(1 for s in prd['stories'] if s['priority']==2)}, P3={sum(1 for s in prd['stories'] if s['priority']==3)}, P4={sum(1 for s in prd['stories'] if s['priority']==4)}, P5={sum(1 for s in prd['stories'] if s['priority']==5)}")
