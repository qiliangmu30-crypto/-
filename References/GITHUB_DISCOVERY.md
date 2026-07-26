---
title: "GitHub Source Discovery Report"
type: "reference"
concepts: ["Attachment", "Conflict Repair", "Knowledge Graph"]
source_url: "https://github.com/search"
review_status: "seed-reviewed"
last_reviewed: "2026-07-26"
---

# GitHub 来源调研（2026-07-26）

## 搜索范围

按需求对以下词组做了组合搜索与主题页筛选：`Relationship Psychology`、`Attachment Theory`、`Adult Attachment`、`Relationship Therapy`、`Emotionally Focused Therapy`、`Communication Skills`、`Conflict Resolution`、`Relationship Research`、`Psychology Books/Notes/Knowledge Base`、`Obsidian Psychology Vault`、`Markdown Psychology`、`Relationship/Attachment Dataset`、`Relationship Case Study`、`Psychology Papers`、`Interpersonal Communication`，以及指定书名和作者名。

筛选标准不是“搜索结果里出现关键词”就复制，而是依次检查：相关性、最后更新、来源可追溯性、是否区分学术与自助内容、仓库许可证、数据同意范围、个人信息风险、是否可能来自受版权保护的整书。

## 推荐借鉴或登记

| 仓库 | 可用价值 | 许可/状态 | 本库处理 |
|---|---|---|---|
| [Ar9av/obsidian-wiki](https://github.com/Ar9av/obsidian-wiki) | AI 维护互链 Markdown、lint 与检索的工程模式 | MIT（页面核验） | 仅借鉴工作流，不复制内容 |
| [cognitivetech/Psychology-Summaries](https://github.com/cognitivetech/Psychology-Summaries) | 有依恋与心理学书籍的 Markdown/LLM 总结 | 仓库标 CC0；但底层商业书版权链仍需逐项审查 | 只登记，不批量导入；本库独立撰写卡片 |
| [mitmedialab/persona-conflicts-corpus-emnlp-2025](https://github.com/mitmedialab/persona-conflicts-corpus-emnlp-2025) | 5,772 条熟人关系冲突的**合成**对话及人工标注 | MIT（页面核验） | 建立数据集卡；不默认复制数据 |
| [JiaQiSJTU/DialogueRelationClassification](https://github.com/JiaQiSJTU/DialogueRelationClassification) | DDRel 双人对话关系分类任务与代码 | 仓库页未显示许可证 | 仅登记论文和入口；授权明确前不下载/再分发 |
| [psych-ds/example-datasets](https://github.com/psych-ds/example-datasets) | 心理学数据的 FAIR 元数据组织范例 | 每个上游数据集需单独核验 | 借鉴数据卡字段，不合并数据 |
| [awesomedata/awesome-public-datasets](https://github.com/awesomedata/awesome-public-datasets) | 高质量公共数据入口索引 | MIT（索引仓库） | 作为发现入口；不把“公开可见”等同于可训练 |
| [thu-coai/Emotional-Support-Conversation](https://github.com/thu-coai/Emotional-Support-Conversation) | 情绪支持对话策略研究 ESConv | 需按仓库与论文说明复核 | 仅登记为相邻任务，不把支持对话等同于伴侣治疗 |
| [ncase/trust](https://github.com/ncase/trust) | 互惠与信任的交互式教育模型 | CC0（项目说明需再次核验具体资产） | 可作为机制教育入口，不能替代关系研究 |
| [obsidianmd/obsidian-help](https://github.com/obsidianmd/obsidian-help) | Wikilink 与 Obsidian 格式规范 | 以仓库许可证为准 | 用于格式兼容性参考 |
| [heathersherry/Knowledge-Graph-Tutorials-and-Papers](https://github.com/heathersherry/Knowledge-Graph-Tutorials-and-Papers) | 知识图谱论文/教程索引 | 需核验许可证及各链接 | 作为工程研究入口 |

## 明确不采用的来源类型

- 名称含 `ebook`、`book PDF` 但未提供作者授权或开放许可的商业书扫描件。
- 无许可的整书 LLM 转录、出版社预览抓取镜像或绕过付费墙的链接。
- 含私人 Facebook/WhatsApp/短信记录、但没有所有参与者明确同意和去标识说明的仓库。
- 把依恋测试当临床诊断、没有量表来源或验证信息的应用。
- 只靠 Reddit 帖子推导疗效或普遍规律的项目。

## 搜索结论

GitHub 更适合找到知识管理工程模式、开放数据入口和可复现代码，不是商业关系心理学书籍的合法全文来源。知识内容的基线应优先来自开放论文、DOI 元数据、开放教材与专业组织页面；GitHub 内容只有在许可证与来源链清楚时才进入正文。

相关：[[References/SOURCE_CATALOG|开放来源目录]]、[[References/LEGAL_AND_ETHICS|版权、隐私与伦理边界]]、[[Datasets/PersonaConflicts-Corpus|PersonaConflicts Corpus]]。

