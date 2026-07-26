---
title: "Retrieval Protocol"
type: "prompt"
---

# 检索协议

1. 保留用户原问题中的时间、行为、原话、关系阶段和安全信息，不只抽取关键词。
2. 首轮检索完整问题；第二轮按缺口分别检索概念、论文或案例，并用 `--type`、`--author`、`--concept` 过滤。
3. 优先级：开放论文与综述 > 原始同行评审研究 > 权威组织/开放教材 > 理论/商业书籍 > 合成案例 > 论坛材料。
4. 同一主张尽量寻找两个独立来源；“作者自己的网站”可说明模型，但不能单独证明疗效。
5. 读取底层来源链接，确认知识卡没有把相关性写成因果、把群体平均写成个人结论。
6. 把无命中、冲突或过期资料作为结果的一部分，不能用模型记忆悄悄填空。
7. 输出时引用知识卡路径和底层来源；精确书中章节只在已核对合法版本时使用。

推荐命令：

```powershell
python -m relationship_kb query "<完整问题>" --top-k 12 --json
python -m relationship_kb query "<核心机制>" --type paper --top-k 6
python -m relationship_kb context "<完整问题>" --top-k 8
```

