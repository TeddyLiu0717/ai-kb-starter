# Wiki Schema

## 页面类型

| 类型 | 目录 | 用途 |
|---|---|---|
| source-summary | wiki/sources/ | 单篇原始资料的摘要页，是所有知识的**根** |
| concept | wiki/concepts/ | 概念、方法、理论、框架 |
| entity | wiki/entities/ | 人物、公司、产品、工具、组织 |
| topic | wiki/topics/ | 跨来源综述、对比、专题 |

## frontmatter（每页必填）

```yaml
---
title: 页面标题
type: source-summary | concept | entity | topic
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: []      # 来源页文件名（不含扩展名）；concept/entity/topic 至少 1 条
tags: []
---
```

## 链接与引用

- 页面之间用 Obsidian 双链 `[[页面名]]`
- 每页至少 2 个内部链接；concept/entity/topic 必须链回至少 1 个 sources 页
- 事实必须有来源；AI 归纳用 `> ⏳ 推断，待确认`；冲突用 `> ⚠️ 矛盾标注`；信息不足用 `> 📌 待核实`

## 更新规则

- raw/ 只读；wiki/ 只做增量更新；每次更新追加 wiki/log.md
- 单次编译上限 10 篇
- 机器生成内容放在 `<!-- AUTO:START -->` / `<!-- AUTO:END -->` 之间
