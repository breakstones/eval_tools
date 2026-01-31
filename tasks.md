# Development Tasks Tracker

## 状态说明
- [ ] Todo - 待办
- [*] WIP - 开发中
- [x] Done - 已完成
- [v] Verified - 单元测试已通过

## Phase 1: 基础框架与用例管理
- [ ] **T1-01** [BE] 初始化 FastAPI 项目结构，配置 SQLAlchemy 与 Pytest 环境
- [ ] **T1-02** [BE] 实现 CaseSet 与 TestCase 的 Model 定义与 Migration
- [ ] **T1-03** [BE] 编写 Excel 解析工具类 `utils/excel_parser.py`
  - **Test**: 必须包含针对空行、非法格式的单元测试 `tests/test_excel.py`
- [ ] **T1-04** [BE] 实现导入接口 `POST /api/cases/import`
- [ ] **T1-05** [BE] 实现用例集CRUD接口 `GET/POST/PUT/DELETE /api/case-sets`
- [ ] **T1-06** [BE] 实现测试用例CRUD接口 `GET/POST/PUT/DELETE /api/test-cases`
- [ ] **T1-07** [BE] 实现Excel导出接口 `GET /api/case-sets/{id}/export`
- [ ] **T1-08** [FE] 初始化 Vue3 项目，引入 Element Plus
- [ ] **T1-09** [FE] 实现用例列表页与导入组件，联调后端接口
- [ ] **T1-10** [FE] 实现用例集管理和用例编辑功能

## Phase 2: 评测引擎核心
- [ ] **T2-01** [BE] 实现 EvalTask 和 EvalResult 数据模型
- [ ] **T2-02** [BE] 编写模板渲染引擎 `utils/templater.py`
  - **Test**: 测试包含引号、换行符的 Input 是否能正确生成 JSON
- [ ] **T2-03** [BE] 封装 LLM Client，实现异步调用
  - **Test**: 使用 `respx` 库 Mock 外部 API，禁止在单元测试中发起真实网络请求
- [ ] **T2-04** [BE] 实现评估器基类和具体实现 `evaluators/`
  - **Test**: 测试各种评估器的判定逻辑
- [ ] **T2-05** [BE] 实现评测任务创建接口 `POST /api/eval/tasks`
- [ ] **T2-06** [BE] 实现 SSE 流式接口 `GET /api/eval/stream/{task_id}`
- [ ] **T2-07** [BE] 实现评测结果查询接口 `GET /api/eval/tasks/{id}/results`
- [ ] **T2-08** [FE] 实现评测控制台页面，接入 EventSource 展示实时进度
- [ ] **T2-09** [FE] 实现评测任务列表和详情页

## Phase 3: 评估器与可视化
- [ ] **T3-01** [BE] 实现 `ExactMatchEvaluator` 精确匹配评估器
- [ ] **T3-02** [BE] 实现 `JsonCompareEvaluator` JSON对比评估器
- [ ] **T3-03** [BE] 实现 `LlmEvaluator` LLM语义评估器（预留）
- [ ] **T3-04** [FE] 集成 `diff2html` 组件，实现预期与实际输出的 Diff 高亮
- [ ] **T3-05** [FE] 实现评测报告统计页面

## Phase 4: 完善与测试
- [ ] **T4-01** [ALL] 完善错误处理和日志记录
- [ ] **T4-02** [ALL] 补全单元测试，确保覆盖率 > 90%
- [ ] **T4-03** [ALL] 端到端测试验证
- [ ] **T4-04** [ALL] 性能优化和并发控制验证
