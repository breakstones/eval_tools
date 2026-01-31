按照您的要求，我将输出两份独立的文档：一份是面向产品定义的**需求文档 (PRD)**，另一份是面向开发落地的**详细工程实施文档**。

# ---

**文档一：产品需求文档 (PRD)**

**项目名称**：LLM 自动化评测工具 (LLM Eval Studio)

**版本**：V1.0

**日期**：2026-01-30

## **1\. 项目背景与目标**

构建一个轻量级、可视化的 LLM 评测平台，旨在解决大模型应用开发中“提示词效果难以量化”和“回归测试效率低”的问题。核心目标是实现测试用例的高效管理（Excel 集成）和评测过程的自动化与可视化（Diff 对比）。

## **2\. 模块一：用例管理 (Case Management)**

### **2.1 信息结构**

| 实体 | 字段 | 说明 |
| :---- | :---- | :---- |
| **用例集 (Case Set)** | 用例集名称 | 唯一标识一组测试任务 |
|  | System Prompt | 全局适用于该集下所有用例的系统提示词 |
| **测试用例 (Test Case)** | ID | 唯一标识 |
|  | 用例描述 | 测试目的或场景描述 |
|  | 用户输入 (User Input) | 模拟用户的 Prompt |
|  | 预期输出 (Expected) | 用于对比的标准答案（Ground Truth） |

### **2.2 功能需求**

#### **2.2.1 Excel 导入导出**

* **交互方式**：支持 .xlsx 文件上传与下载。  
* **结构约束**：必须在一个 Sheet 页内完成所有信息录入。  
  * **第1行**：解析为“用例集信息”（名称、System Prompt）。  
  * **第2行及之后**：解析为“用例列表”。  
* **校验**：导入时需校验必填字段，若格式不符需给出错误提示。

#### **2.2.2 在线编辑**

* 支持在 Web 端对用例集名称、System Prompt 进行修改。  
* 支持以表格形式（Data Grid）增删改具体的测试用例。

## ---

**3\. 模块二：评测管理 (Evaluation Management)**

### **3.1 信息结构**

| 实体 | 字段/结构 | 说明 |
| :---- | :---- | :---- |
| **评测任务** | 评测对象 | 关联一个具体的“用例集” |
|  | 评估器配置 | 选择使用的评估器（如：精确匹配、LLM打分） |
|  | **执行模型配置** | \- BaseURL \- API Key \- Model Code (e.g., gpt-4) \- **请求模板** (JSON结构) |
| **请求模板规范** | JSON 模板 | {"model": "${model\_name}", "messages": \[ {"role": "system", "content": "${case\_set.system\_prompt}" },{"role": "user", "content": "${case.user\_input}" }\] } |
| **执行记录** | 任务概览 | 执行时间、总用例数、通过数、通过率 |
|  | 单条详情 | 关联用例ID、实际输出、评估结果（Pass/Fail）、差异详情 |

### **3.2 功能需求**

#### **3.2.1 任务执行**

* **新增任务**：用户配置模型参数与模板，启动评测。  
* **流式反馈**：前端需实时展示当前执行进度（例如：正在执行第 5/100 条），且能实时看到已完成用例的结果，无需等待全部完成。

#### **3.2.2 自动化评估器**

* **Code Evaluator (默认)**：基于规则的评估。支持 JSON 结构对比或文本完全匹配。  
* **LLM Evaluator (预留)**：调用大模型进行语义打分。  
* **判定逻辑**：若启用了多个评估器，任意一个评估器判定为“不通过”，则该用例最终结果为“不通过”。

#### **3.2.3 结果可视化 (Diff)**

* 提供“预期输出”与“实际输出”的**高亮差异对比**。  
* 使用红/绿背景色直观显示文本的增加、删除与修改。

# ---

**文档二：详细工程实施文档 (Engineering Guide)**

**技术栈**：Vue 3 (Frontend) \+ Python FastAPI (Backend)

**管理规范**：严格遵循 tasks.md 管理与 TDD (测试驱动开发) 流程。

## **1\. 系统架构设计**

### **1.1 技术选型详情**

* **前端**：  
  * 框架：Vue 3 (Composition API) \+ Vite  
  * UI 库：Element Plus (重点使用 el-table 和 el-form)  
  * Diff 组件：vue-diff (基于 diff-match-patch 算法)  
  * 网络：Axios (常规请求) \+ EventSource (SSE 流式接收)  
* **后端**：  
  * 框架：FastAPI (利用 async/await 处理高并发 I/O)  
  * 数据库：SQLite (开发阶段) / PostgreSQL (生产建议)，ORM 使用 SQLModel 或 SQLAlchemy。  
  * 数据处理：Pandas (处理 Excel), Jinja2 (处理 Prompt 模板渲染)。  
  * HTTP Client：Httpx (异步请求第三方 LLM API)。

### **1.2 数据库设计 (ERD)**

SQL

\-- 1\. 用例集表  
CREATE TABLE case\_sets (  
    id VARCHAR(36) PRIMARY KEY, \-- UUID  
    name VARCHAR(255) NOT NULL,  
    system\_prompt TEXT,  
    created\_at DATETIME DEFAULT CURRENT\_TIMESTAMP  
);

\-- 2\. 测试用例表  
CREATE TABLE test\_cases (  
    id VARCHAR(36) PRIMARY KEY,  
    set\_id VARCHAR(36),  
    case\_uid VARCHAR(50), \-- 用户视角的编号，如 CASE-001  
    description VARCHAR(255),  
    user\_input TEXT NOT NULL,  
    expected\_output TEXT,  
    FOREIGN KEY (set\_id) REFERENCES case\_sets(id)  
);

\-- 3\. 评测历史任务表  
CREATE TABLE eval\_tasks (  
    id VARCHAR(36) PRIMARY KEY,  
    set\_id VARCHAR(36),  
    model\_config JSON, \-- 存储 url, key, template  
    status VARCHAR(20), \-- PENDING, RUNNING, COMPLETED, FAILED  
    summary JSON, \-- {"total": 10, "passed": 8}  
    created\_at DATETIME  
);

\-- 4\. 评测结果详情表  
CREATE TABLE eval\_results (  
    id VARCHAR(36) PRIMARY KEY,  
    task\_id VARCHAR(36),  
    case\_id VARCHAR(36),  
    actual\_output TEXT,  
    is\_passed BOOLEAN,  
    evaluator\_logs JSON, \-- \[{"name": "json\_diff", "reason": "mismatch"}\]  
    FOREIGN KEY (task\_id) REFERENCES eval\_tasks(id)  
);

## ---

**2\. 核心功能实现逻辑**

### **2.1 Excel 导入逻辑 (Pandas 实现)**

* **挑战**：单 Sheet 混合了“集信息”和“列表信息”。  
* **算法**：  
  1. 读取 Excel 第一行 (Header Row) 获取 Case Set Name 和 System Prompt。  
  2. 读取 DataFrame 的全部数据。  
  3. 遍历每一行，提取 Test Case 字段。  
  4. **注意**：Pandas 读取时，若第二行及以后的 Set Name 为空（Excel合并单元格或留空），需兼容处理。  
* **代码伪逻辑**：  
  Python  
  df \= pd.read\_excel(file)  
  \# 假设第一列是 set\_name，第二列是 system\_prompt  
  set\_info \= df.iloc\[0\]   
  cases\_data \= df\[\['case\_id', 'input', 'expected'\]\].to\_dict('records')  
  \# 存入数据库...

### **2.2 评测引擎与 SSE 流式推送**

为了保证实时性，不使用简单的 HTTP 等待，而是使用 Server-Sent Events (SSE)。

1. **Client**: 发起 POST /api/eval/run，获得 task\_id。  
2. **Client**: 立即订阅 GET /api/eval/stream/{task\_id}。  
3. **Server**:  
   * 创建一个异步生成器 (async generator)。  
   * 查询该 Task 下的所有 Cases。  
   * **并发控制**: 使用 asyncio.Semaphore(5) 限制同时请求 LLM 的数量，防止触发 API Rate Limit。  
   * **逐个处理**:  
     1. 渲染模板: template.replace("${case.user\_input}", case.input)。  
     2. await client.post(llm\_url, json=payload)。  
     3. 运行评估器函数对比结果。  
     4. 写入数据库。  
     5. yield f"data: {json\_result}\\n\\n" 推送给前端。

### **2.3 变量替换 (Template Engine)**

后端需编写一个解析器，支持从 JSON 字符串中提取 ${variable} 并进行安全替换。

* **必须处理转义**：如果 user\_input 中包含双引号 "，直接字符串替换会导致 JSON 格式破损。  
* **方案**：先构建 Python 字典对象，再进行值替换，最后 json.dumps 序列化。

## ---

**3\. 开发流程规范 (tasks.md)**

项目根目录必须包含 tasks.md，开发前必须定义任务，开发后必须勾选。

### **3.1 任务清单模板**

Markdown

\# Development Tasks Tracker

\#\# 状态说明  
\- \[ \] Todo  
\- \[x\] WIP (开发中)  
\- \[v\] Verified (单元测试已通过)

\#\# Phase 1: 基础框架与用例管理  
\- \[ \] **\*\*T1-01\*\*** \[BE\] 初始化 FastAPI 项目结构，配置 SQLAlchemy 与 Pytest 环境。  
\- \[ \] **\*\*T1-02\*\*** \[BE\] 实现 CaseSet 与 TestCase 的 Model 定义与 Migration。  
\- \[ \] **\*\*T1-03\*\*** \[BE\] 编写 Excel 解析工具类 \`utils/excel\_parser.py\`。  
    \- *\*Test\**: 必须包含针对空行、非法格式的单元测试 \`tests/test\_excel.py\`。  
\- \[ \] **\*\*T1-04\*\*** \[BE\] 实现导入接口 \`POST /cases/import\`。  
\- \[ \] **\*\*T1-05\*\*** \[FE\] 初始化 Vue3 项目，引入 Element Plus。  
\- \[ \] **\*\*T1-06\*\*** \[FE\] 实现用例列表页与导入组件，联调 T1-04 接口。

\#\# Phase 2: 评测引擎核心  
\- \[ \] **\*\*T2-01\*\*** \[BE\] 实现 EvalTask 数据模型与创建接口。  
\- \[ \] **\*\*T2-02\*\*** \[BE\] 编写模板渲染引擎 \`utils/templater.py\`。  
    \- *\*Test\**: 测试包含引号、换行符的 Input 是否能正确生成 JSON。  
\- \[ \] **\*\*T2-03\*\*** \[BE\] 封装 LLM Client，实现异步调用。  
    \- *\*Test\**: 使用 \`respx\` 库 Mock 外部 API，**\*\*禁止\*\***在单元测试中发起真实网络请求。  
\- \[ \] **\*\*T2-04\*\*** \[BE\] 实现 SSE 流式接口 \`GET /stream/{id}\`。  
\- \[ \] **\*\*T2-05\*\*** \[FE\] 实现评测控制台，接入 EventSource 展示实时进度。

\#\# Phase 3: 评估器与可视化  
\- \[ \] **\*\*T3-01\*\*** \[BE\] 实现 \`ExactMatchEvaluator\` 和 \`JsonCompareEvaluator\`。  
\- \[ \] **\*\*T3-02\*\*** \[FE\] 集成 \`vue-diff\` 组件，实现预期与实际输出的 Diff 高亮。

### **3.2 验收标准 (DoD)**

1. **零报错**：前后端无控制台红字报错。  
2. **测试覆盖**：后端核心逻辑（Excel解析、模板渲染、评估逻辑）测试覆盖率 \> 90%。  
3. **Mock验证**：所有涉及 LLM API 的测试必须通过 Mock 完成，不消耗真实 Token。  
4. **数据闭环**：导入 Excel \-\> 评测 \-\> 结果回显，全流程在本地跑通。

### ---

**下一步建议**

建议您优先创建 **GitHub/GitLab 仓库**，上传 tasks.md，并开始执行 **T1-01** 任务。需要我为您生成具体的 FastAPI 项目目录结构吗？