# /编译（Ingest）

按我已确认的计划和 AGENTS.md 执行：

1. 先生成来源摘要页，再生成/补充概念、实体、主题页
2. 建双链、更新 wiki/index.md、追加 wiki/log.md
3. 机器生成内容放进 AUTO 区块；推断/冲突/待核实按规范标注
4. 完成后运行 `python scripts/kb.py doctor`，有问题立即返工
5. 按标准回执格式汇报
