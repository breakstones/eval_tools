# LLM Eval Studio - Claude 开发指南

## 项目概述
LLM 自动化评测工具，实现测试用例的高效管理（Excel 集成）和评测过程的自动化与可视化（Diff 对比）。

## 技术栈
- **后端**: Python 3.11+ / FastAPI / SQLAlchemy / SQLite / Pytest
- **前端**: Vue 3 (Composition API) / Vite / Element Plus / Axios
- **工具**: Pandas (Excel处理) / Jinja2 (模板渲染) / Httpx (异步HTTP)

## 项目结构
```
eval_tools_v2/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI 应用入口
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # 数据库连接
│   │   ├── models/            # SQLAlchemy 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── case_set.py
│   │   │   ├── test_case.py
│   │   │   ├── eval_task.py
│   │   │   └── eval_result.py
│   │   ├── schemas/           # Pydantic 数据模式
│   │   │   ├── __init__.py
│   │   │   ├── cases.py
│   │   │   └── eval.py
│   │   ├── api/               # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── cases.py       # 用例管理接口
│   │   │   └── eval.py        # 评测管理接口
│   │   ├── services/          # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── case_service.py
│   │   │   ├── excel_service.py
│   │   │   └── eval_service.py
│   │   ├── evaluators/        # 评估器
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── exact_match.py
│   │   │   └── json_compare.py
│   │   └── utils/             # 工具函数
│   │       ├── __init__.py
│   │       ├── excel_parser.py
│   │       ├── templater.py
│   │       └── llm_client.py
│   ├── tests/                 # 测试代码
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_excel_parser.py
│   │   ├── test_templater.py
│   │   └── test_evaluators.py
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── components/        # 组件
│   │   │   ├── CaseList.vue
│   │   │   ├── CaseEditor.vue
│   │   │   ├── ImportExcel.vue
│   │   │   ├── EvalConsole.vue
│   │   │   └── DiffViewer.vue
│   │   ├── views/             # 页面视图
│   │   │   ├── CaseManagement.vue
│   │   │   └── Evaluation.vue
│   │   ├── api/               # API 封装
│   │   │   ├── index.ts
│   │   │   ├── cases.ts
│   │   │   └── eval.ts
│   │   ├── stores/            # Pinia 状态管理
│   │   │   ├── cases.ts
│   │   │   └── eval.ts
│   │   └── types/             # TypeScript 类型
│   │       ├── cases.ts
│   │       └── eval.ts
│   ├── package.json
│   └── vite.config.ts
├── tasks.md                    # 任务跟踪
└── Claude.md                   # 本文件
```

## 开发规范
1. 严格遵循 TDD (测试驱动开发)
2. 所有核心逻辑必须有单元测试，覆盖率 > 90%
3. 涉及外部 API 的测试必须使用 Mock（respx）
4. 提交前确保 `pytest` 通过
5. 前端使用 TypeScript 类型定义
6. API 接口遵循 RESTful 规范

## 核心设计要点

### Excel 导入格式
- 第1行：用例集信息（名称、System Prompt）
- 第2行及之后：用例列表（ID、描述、用户输入、预期输出）

### SSE 流式推送
- 客户端订阅 `GET /api/eval/stream/{task_id}`
- 服务端实时推送评测进度和结果
- 并发控制：Semaphore(5) 限制同时请求数

### 评估器规则
- 多评估器判定：任意一个不通过则整体不通过
- 支持扩展：可添加新的评估器实现

## 快速启动

### 后端
```bash
cd backend
pip install -r requirements.txt
pytest                    # 运行测试
uvicorn app.main:app --reload
```

### 前端
```bash
cd frontend
npm install
npm run dev
```

## 当前状态
项目初始化阶段，正在执行 Phase 1 任务。
