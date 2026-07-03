# 🎓 大师圆桌 —— 个人投资决策智能 Agent（Decision Intelligence）

> 同一只股票，不同的人，应该得到不同的建议。
> 我们分析的不是股票，是"人在当前处境下应该如何决策"。

## 项目简介
市面工具回答"这只股票好不好"；「大师圆桌」回答 **"这个决策适不适合此刻的你"**。
系统将四套经典投资决策框架（以大师人物为 UI 载体降低理解成本）应用于
**同一只股票 + 用户真实处境**，由决策裁判 Agent 完成框架适配与行为偏差诊断，
并通过决策记忆（Decision Memory）实现跨会话的决策连续性。

## 核心功能
1. **四套决策框架并行分析**：Business Quality（商业质量）/ Valuation（估值与安全边际）/ Growth（成长性）/ Risk Control（风险控制）——人物只是界面，运行的是框架
2. **情境注入**：持仓成本、仓位占比、风险偏好、期限、心理纠结作为分析的一等公民
3. **决策裁判**：标注共识与永久分歧（不强行调和）→ 判定本次最适合该用户的框架 → 指出最大**认知风险**（最大风险常常不是股票，而是人的行为偏差）
4. **决策记忆（Decision Memory）**：自动检测目标漂移——"两周前你说长期持有，这次却想止损，是什么信息变了？"
5. **决策档案与复盘（Decision Journal）**：记录每次决策处境与结论，30 天后回填执行情况与反思，沉淀个人投资行为画像
6. **降级兜底**：无 API / API 故障时自动切换离线演示模式，保证评审可运行

## 技术方案（五层架构）
```
UI (Streamlit)
 └─ Orchestration Layer  analyzer.py   多Agent编排：独立分析→裁判合议
     ├─ Framework Layer  masters.py    四套决策框架（可热插拔）
     ├─ Data Layer       data_provider.py  行情抽象层（官方SDK接入点）
     ├─ Memory Layer     memory.py     决策记忆：漂移检测/档案/复盘
     └─ LLM Layer        llm_client.py OpenAI兼容，可换任意算力API
```
**大模型只是推理引擎；产品核心是决策框架、Agent 协作流程与用户长期记忆。**
数据层与 LLM 层均为抽象接口，替换官方 SDK 各只需改 1 个文件。

## 商业模式
C 端：免费限次 → 订阅解锁。长期价值来自**用户决策档案**：一年后用户能看到
自己何时最容易追涨、何时恐慌卖出、哪种框架最适合自己——
**卖的不是分析次数，是长期决策能力。**
B 端：向券商输出投教工具模块（券商有投资者教育合规义务）。

## 部署运行
```bash
pip install -r requirements.txt
# 可选：配置真实 LLM API（不配则进入离线演示模式）
export LLM_API_BASE="https://api.xxx.com/v1"
export LLM_API_KEY="sk-xxx"
export LLM_MODEL="模型名"
streamlit run app.py
```

## 第三方资源声明
- [Streamlit](https://streamlit.io/)（Apache-2.0）、[openai-python](https://github.com/openai/openai-python)（Apache-2.0）
- 行情数据：主办方官方 SDK（赛事授权范围内使用）
- 投资框架整理自公开出版物思想（《聪明的投资者》等），为原创性重述与工程化封装
- 多人格辩论的结构设计参考了开源项目 prism-skill 的公开思路，本项目为独立实现

## 免责声明
本工具输出为 AI 基于公开投资框架生成的分析视角，仅供学习参考，不构成任何投资建议。
