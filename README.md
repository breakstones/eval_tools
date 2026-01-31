# LLM Eval Studio

> LLM 自动化评测工具 - 实现测试用例的高效管理（Excel 集成）和评测过程的自动化与可视化

## 功能特性

### 1. 用例管理

- **Excel 导入/导出**：
  - 支持从 Excel 文件批量导入测试用例
  - 导入到现有用例集，支持按用例编号去重覆盖
  - 导出用例集为 Excel 文件

- **用例集管理**：
  - 创建、编辑（名称）、删除用例集
  - 自动选中第一个用例集
  - 测试用例批量删除

- **测试用例 CRUD**：完整的用例增删改查操作

- **用例字段**：
  - 用例编号 (CASE-001)
  - 用例描述
  - 用户输入/提示词
  - 预期输出

### 2. 模型管理

- **多提供商支持**：支持配置多个 LLM 服务提供商
- **模型配置**：为每个提供商配置多个模型
- **灵活的 API 配置**：
  - Base URL
  - API Key
  - 模型代码
  - 显示名称

### 3. 评测管理

- **任务配置**：
  - 任务名称（必填，可编辑）
  - 选择用例集和模型
  - 配置系统提示词
  - 自定义请求模板（JSON 格式）
  - 配置并发数量（1-20）
  - 显示当前用例集名称（只读）

- **并发评测**：支持同时运行多个评测请求，提高效率

- **实时进度**：通过 WebSocket 实时推送评测进度

- **运行历史**：支持同一评测任务的多次运行，历史记录可追溯

- **结果详情**：
  - 用例编号
  - 预期输出 vs 实际输出
  - Diff 对比高亮显示（Beyond Compare 风格）
  - 评估器执行详情
  - 评估通过/失败状态
  - 统计信息：通过数/失败数/总数（颜色区分）

### 4. 评估器

**内置评估器**：
- **精确匹配评估器**：字符串精确匹配
- **JSON 比较评估器**：JSON 结构深度比较，支持自动修复 LLM 输出的畸形 JSON

**LLM 评估器**：
- **审核规则评估器（LLM Judge）**：使用 LLM 对输出进行智能评估
  - 自定义审核规则
  - 灵活的评分标准
  - 详细的评估原因

**评估器管理**：
- 创建、编辑、删除评估器
- 为评测任务配置多个评估器
- 评估结果合并：任意一个不通过则整体不通过

### 5. 模板变量系统

请求模板支持以下变量：

| 变量 | 说明 |
|------|------|
| `${model_name}` | 模型名称 |
| `${system_prompt}` | 系统提示词 |
| `${task_config.base_url}` | API 地址 |
| `${task_config.api_key}` | API Key |
| `${task_config.model_code}` | 模型代码 |
| `${case_set.name}` | 用例集名称 |
| `${case.user_input}` | 用例输入 |
| `${case.case_uid}` | 用例ID |
| `${case.description}` | 用例描述 |

### 6. Excel 导入格式

```
| 用例集名称 | [填写用例集名称] |
| 系统提示词 | [填写系统提示词，可选] |
| | | | | |
| 用例编号 | 描述 | 用户输入 | 预期输出 |
| CASE-001 | 测试用例1 | 用户的问题 | 预期的回答 |
| CASE-002 | 测试用例2 | 用户的问题 | 预期的回答 |
```

## 技术栈

### 后端
- **Python 3.11+**
- **FastAPI** - Web 框架
- **SQLAlchemy** - ORM
- **SQLite** - 数据库
- **Pytest** - 测试框架
- **Pandas** - Excel 处理
- **Jinja2** - 模板渲染
- **Httpx** - 异步 HTTP 客户端

### 前端
- **Vue 3** (Composition API)
- **TypeScript**
- **Vite** - 构建工具
- **Element Plus** - UI 组件库
- **Pinia** - 状态管理
- **Axios** - HTTP 客户端
- **diff-match-patch** - 文本对比

## 快速开始

### 后端启动

```bash
cd backend
pip install -r requirements.txt
python -m app.main
# 或使用 uvicorn
uvicorn app.main:app --reload
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

### 运行测试

```bash
cd backend
pytest
```

## 项目结构

```
eval_tools_v2/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── api/               # API 路由
│   │   ├── evaluators/        # 评估器
│   │   ├── models/            # 数据模型
│   │   ├── schemas/           # Pydantic 模式
│   │   ├── services/          # 业务逻辑
│   │   └── utils/             # 工具函数
│   ├── tests/                 # 测试代码
│   └── requirements.txt
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── api/               # API 封装
│   │   ├── components/        # 组件
│   │   │   └── DiffViewer.vue # Diff 对比组件
│   │   ├── stores/            # 状态管理
│   │   ├── types/             # 类型定义
│   │   ├── views/             # 页面视图
│   │   │   ├── CaseManagement.vue   # 用例管理
│   │   │   ├── Evaluation.vue        # 评测管理
│   │   │   └── EvaluatorManagement.vue # 评估器管理
│   │   └── router/            # 路由配置
│   └── package.json
└── README.md
```

## API 端点

### 用例管理
- `GET /api/cases/sets` - 获取所有用例集
- `POST /api/cases/sets` - 创建用例集
- `GET /api/cases/sets/{id}` - 获取单个用例集
- `PUT /api/cases/sets/{id}` - 更新用例集
- `DELETE /api/cases/sets/{id}` - 删除用例集
- `GET /api/cases/sets/{id}/cases` - 获取测试用例列表
- `POST /api/cases` - 创建测试用例
- `POST /api/cases/import` - 导入 Excel

### 模型管理
- `GET /api/models/providers` - 获取提供商列表
- `POST /api/models/providers` - 创建提供商
- `GET /api/models` - 获取模型列表
- `POST /api/models` - 创建模型

### 评估器管理
- `GET /api/evaluators` - 获取评估器列表
- `POST /api/evaluators` - 创建评估器
- `GET /api/evaluators/{id}` - 获取单个评估器
- `PUT /api/evaluators/{id}` - 更新评估器
- `DELETE /api/evaluators/{id}` - 删除评估器
- `GET /api/evaluators/tasks/{task_id}/evaluators` - 获取任务的评估器
- `PUT /api/evaluators/tasks/{task_id}/evaluators` - 设置任务的评估器

### 评测管理
- `GET /api/eval/tasks` - 获取评测任务列表
- `GET /api/eval/tasks/{id}` - 获取单个评测任务
- `POST /api/eval/tasks` - 创建评测任务
- `PUT /api/eval/tasks/{id}` - 更新评测任务
- `DELETE /api/eval/tasks/{id}` - 删除评测任务
- `POST /api/eval/tasks/{id}/rerun` - 重新运行评测
- `GET /api/eval/tasks/{id}/runs` - 获取运行历史
- `GET /api/eval/runs/{run_id}/results` - 获取运行结果
- `WS /api/eval/ws/eval/{task_id}` - WebSocket 实时进度

## 开发规范

1. **TDD 开发**：核心逻辑必须有单元测试，覆盖率 > 90%
2. **API 设计**：遵循 RESTful 规范
3. **类型安全**：前端使用 TypeScript 类型定义
4. **提交前检查**：确保 `pytest` 通过

## 许可证

MIT License
