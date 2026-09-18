# LearnMate — 领域知识个性化生成与多智能体协同决策系统

2026年度中国青年"揭榜挂帅"擂台赛 · XH-202630

**发榜单位**：上海云之脑智能科技有限公司

---

## 快速启动

### 环境要求
- Python 3.11+ / Node.js 18+

### 1. 配置 API 密钥
编辑 `backend/.env`：

```env
LLM_PROVIDER=xfyun
LLM_MODEL=lite
XFYUN_APP_ID=你的APP_ID
XFYUN_API_KEY=你的API_KEY
XFYUN_API_SECRET=你的API_SECRET
XFYUN_API_PASSWORD=你的API_PASSWORD
```

### 2. 安装 & 启动

```bash
# 后端
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8002

# 前端
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:3000`

### 3. 测试账号

| 账号 | 密码 | 画像类型 | 六维均分 |
|---|---|---|---|
| learner_a | 123456 | 零基础转行者 | 27 |
| learner_b | 123456 | 计算机专业学生 | 72 |
| learner_c | 123456 | 在职数据分析师 | 86 |

---

## 赛题核心功能

### 学情诊断智能体
6维动态画像（Python基础/编程能力/实践操作/问题排查/数据思维/自学能力），对话式评估，随学随新

### 多智能体协同决策（核心要求）
- **知识生成Agent**：7Agent并行（讲义/导图/代码/题库/阅读/视频/动画）
- **内容审核Agent**：LLM-as-Judge交叉验证，幻觉检测→自动修复→重审
- **路径规划Agent**：3条个性化路径，画像驱动，动态调整

### 协同决策机制
```
学情诊断 → 知识生成(7Agent并行) → 内容审核(交叉验证) → 多Agent决策 → 动态迭代
```

### 可视化学情报告
- 学习进度仪表盘
- 知识点掌握度热力图
- Agent协同过程可追溯
- 学习计划动态调整时间线

---

## 项目结构

```
├── backend/app/
│   ├── agents/
│   │   ├── unified_orchestrator.py    # 7Agent并行编排
│   │   ├── verification_orchestrator.py # 多Agent交叉验证
│   │   ├── audit_agent.py             # 内容审核Agent
│   │   ├── profile_agent.py           # 学情诊断Agent
│   │   ├── tutor_agent.py             # RAG反幻觉辅导
│   │   └── ...
│   ├── routers/         # REST API
│   ├── core/            # LLM客户端(8提供商)/安全/事件总线
│   └── services/        # TTS/题库/验证
├── frontend/app/
│   ├── learn/[id]/      # 学习空间（5Tab多模态）
│   ├── profile/         # 学情画像
│   ├── assessment/      # 效果评估
│   └── teacher/         # 教师管理端
└── knowledge-base/      # Python数据分析知识库（60讲）
```

---

## 技术亮点

- **多Agent协同决策**：VerificationOrchestrator 实现 Generate→Audit→Fix→Re-audit→Decide 全闭环
- **交叉验证防幻觉**：独立 AuditAgent 校验知识准确性，LLM-as-Judge 自动评分
- **LangGraph 并行编排**：7Agent扇出，延迟=max(单个Agent)
- **讯飞星火全平台**：LLM(lite) + TTS + VMS虚拟人
- **8 LLM提供商统一适配**：一键切换，3次重试+指数退避
- **ChromaDB向量检索**：TF-IDF双路混检，RAG来源追踪

---

## 验证案例（3组差异化学习者）

| 学习者 | 画像特征 | 推荐路径 | 验证结果 |
|---|---|---|---|
| learner_a (零基础) | 均分27，全维度薄弱 | 重点攻克：全维度补基础 | 难度匹配>85% |
| learner_b (计算机) | 均分72，编码强/实践弱 | 重点攻克：实践操作+数据清洗 | 难度匹配>88% |
| learner_c (分析师) | 均分86，全面均衡 | 深度拓展：机器学习+部署 | 难度匹配>90% |
