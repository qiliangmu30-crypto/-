# Relationship Knowledge Base / 关系心理学知识库

一个本地优先、Git 可版本化、Obsidian 可浏览、AI 可检索的关系心理学 RAG。它把知识组织成概念网络，而不是把商业书籍全文堆在一起；每条材料都要保留来源、证据等级、适用边界和版权状态。

> [!important]
> 本库用于教育、反思与信息整理，不替代心理治疗、医疗、法律或危机服务。依恋风格是研究模型，不是凭一段聊天就能给人的固定诊断。存在暴力、威胁、控制、跟踪或自伤风险时，优先联系当地紧急服务和专业支持。

## 当前交付

- 概念、作者、书籍、论文、案例、对话、框架、数据集均为独立 Markdown，支持 Obsidian `[[wikilinks]]`。
- 书籍卡只使用公开书目信息与短篇原创导读；不收录盗版 PDF、整书转录或虚构章节引用。
- 论文卡记录 DOI/PMCID、开放状态、核心发现与“相关不等于因果”等方法限制。
- `SQLite FTS5 + 向量 + Reciprocal Rank Fusion` 混合检索，支持类型、作者和概念过滤。
- 默认离线 `hashing-v1` 多语言向量，零模型下载即可运行；可切换真正的 Sentence Transformers 语义嵌入。
- 构建时从 Wikilink 自动生成 `index/graph.json`；导入时自动提取 DOI、URL 和已知概念候选。
- `AGENTS.md` 与 `Prompt/` 规定 AI 必须先检索、再按七层框架回答。

## 目录

```text
Relationship-KnowledgeBase/
├── Books/             # 合法的书籍导读卡，不存商业书全文
├── Papers/            # 论文元数据、摘要性综述、发现与限制
├── Concepts/          # 以概念为中心的知识图谱节点
├── Authors/           # 作者、理论体系与局限
├── Cases/             # 去标识或合成教学案例
├── Conversations/     # 对话片段的多理论分析
├── Frameworks/        # EFT、Gottman、NVC、七层回答框架等
├── Research/          # 研究议程、知识图谱与导入收件箱
├── Datasets/          # 数据集卡与许可审查
├── References/        # 来源目录、GitHub 搜索报告、伦理规范
├── Images/            # 自有或许可明确的图像
├── Prompt/            # AI 系统提示、检索协议、回答模板
├── Templates/         # 新增内容的规范模板
├── src/               # RAG 实现
├── tests/             # 自动测试
└── index/             # 生成的 SQLite/向量/图索引（默认不入 Git）
```

## 作为 Codex Skill 跨电脑使用

仓库内置 `relationship-knowledge-base` Skill。目标电脑需要安装 Git、Python 3.10 或更高版本，并拥有本私有 GitHub 仓库的读取权限。

在目标电脑的 Codex 中输入：

```text
$skill-installer 请从私有 GitHub 仓库 qiliangmu30-crypto/- 的 main 分支安装 `.agents/skills/relationship-knowledge-base`，使用 auto 方法。
```

安装完成后重启 Codex，然后可在任意项目中调用：

```text
$relationship-knowledge-base 分析：我们每次谈钱，一方追问，一方沉默，我该如何理解和行动？
```

首次调用会通过本机 Git 凭据把完整知识库下载到 Codex 缓存，后续调用会复用并尝试快进更新；它不会在当前项目中创建知识库文件，缓存也可删除后重新获取。若私有仓库认证失败，请先在目标电脑登录 GitHub 并为 Git 配置凭据；不要把访问令牌粘贴到聊天中。也可将 `RELATIONSHIP_KB_HOME` 指向已有的完整仓库副本。

## 5 分钟开始

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m relationship_kb build
python -m relationship_kb query "伴侣说没事，但明显在疏远，我该怎么理解？"
python -m relationship_kb context "伴侣说没事，但明显在疏远，我该怎么理解？" --top-k 8
```

默认索引完全离线。需要更强的中英文语义检索时：

```powershell
python -m pip install -e ".[semantic]"
python -m relationship_kb build --backend sentence-transformers
```

默认模型是 `paraphrase-multilingual-MiniLM-L12-v2`。第一次构建需要联网下载模型；索引会记录实际后端，查询必须使用同一后端。

## 检索能力

```powershell
# 混合检索
python -m relationship_kb query "追逃循环如何修复" --top-k 10

# 按内容类型过滤
python -m relationship_kb query "communication satisfaction" --type paper

# 按作者或概念过滤
python -m relationship_kb query "conflict repair" --author "John Gottman"
python -m relationship_kb query "安全感" --concept "Emotional Safety"

# 机器可读结果
python -m relationship_kb query "依恋焦虑" --json

# 给 Codex/GPT 的防注入上下文包
python -m relationship_kb context "我们总为回复速度吵架" > work-context.md

# 查看索引状态与检查断链
python -m relationship_kb stats
python -m relationship_kb lint --strict
```

索引将标题、章节、正文、作者和概念写入 FTS5，同时将每个分块写成向量。查询侧分别排序后使用 RRF 融合，避免假设两类分数在同一尺度。默认 hashing 向量是可复现的离线基线，不等同于神经语义模型；生产使用建议启用 Sentence Transformers。

## 新增 PDF、论文、Markdown 或 Obsidian 文件

```powershell
python -m pip install -e ".[documents]"
python -m relationship_kb ingest "D:\Sources\paper.pdf" --kind paper --title "Paper title" --source-url "https://doi.org/..."
python -m relationship_kb lint
python -m relationship_kb build
```

导入器支持 `.md`、`.txt`、`.pdf`、`.docx`，并会：

1. 计算源文件 SHA-256，记录来源路径与导入日期；
2. 提取 DOI、URL，并按概念词典生成候选标签；
3. 用 `<source_text>` 隔离原文，标记为“待人工审查”；
4. 要求人工检查隐私、版权、解析错误和提示注入后再正式使用；
5. 重建索引时自动更新全文、向量与知识图谱。

不要把“自动导入”理解为“自动获得再分发权”。详见 [[References/LEGAL_AND_ETHICS|版权、隐私与伦理边界]]。

## 知识卡规范

所有卡片使用 UTF-8 Markdown 和 JSON 风格的扁平 frontmatter：

```yaml
---
title: "Emotional Safety（情绪安全）"
type: "concept"
authors: ["Sue Johnson", "John Gottman"]
concepts: ["Attachment", "Trust", "Validation"]
source_url: "https://..."
evidence_level: "review-and-theory"
review_status: "seed-reviewed"
last_reviewed: "2026-07-26"
---
```

扁平字段是有意设计：标准库解析器无需 PyYAML，Obsidian 也能读取。详细结构见 `Templates/`。

## AI 回答协议

Codex 在仓库内工作时应自动读取 `AGENTS.md`。其他 AI 应使用 `Prompt/SYSTEM_PROMPT.md`。核心流程：

1. 检索并评估证据覆盖；
2. 区分事实、当事人陈述、推测和未知；
3. 依次分析情绪/需求、依恋系统、沟通模式、认知偏差和理论交叉验证；
4. 明确证据冲突与外推限制；
5. 提供 A/B/C 方案，各自写前提、优点、风险和可能结果；
6. 用知识卡路径与底层 DOI/URL 引用，不伪造书中页码或章节。

## 证据与版权策略

- **Tier A**：系统综述、元分析、预注册或高质量纵向/实验研究。
- **Tier B**：同行评审的单项研究、权威开放教材、专业组织资料。
- **Tier C**：理论著作、临床模型、商业书籍、专家教育材料。
- **Tier D**：公开论坛、个人案例、未验证总结；只能用于提出假设，不能证明因果。

商业书卡不是学术证据的替代品。`Hold Me Tight`、`Attached`、`The Seven Principles...` 等内容只做可核验导读和概念导航；精确措辞、练习与章节请查阅合法购得的原书。

## 持续维护

建议每次变更遵循：

```powershell
python -m relationship_kb lint --strict
python -m pytest
python -m relationship_kb build
python -m relationship_kb query "secure attachment conflict repair"
git status --short
```

论文引用次数会变化，因此卡片必须同时记录计数平台和检索日期。新的公开来源先进入 `Research/Inbox/`；完成许可、隐私、事实和链接审查后，再迁移到正式目录。

## 项目边界

本版提供的是可靠的“可扩展种子库 + 可运行 RAG”，不是宣称已经数字化了全部关系科学。来源发现与筛选记录见 [[References/GITHUB_DISCOVERY|GitHub 来源调研]] 和 [[References/SOURCE_CATALOG|开放来源目录]]；尚待补充的问题见 [[Research/Research-Agenda|研究议程]]。
