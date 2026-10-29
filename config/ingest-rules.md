# 入库规则（Capture & Ingest）

## 默认不写入

普通问答、讨论、排查过程一律不入库。只有用户明确说「入库 / 保存 / 沉淀 / 留档 / 收进知识库」才写入。

## 内容路由

| 内容 | 默认位置 |
|---|---|
| 网页 / 公众号文章原文 | raw/web/ |
| 飞书/Notion 文档导出 | raw/docs/ |
| 本地文件解析结果 | raw/local-files/ |
| 视频转写 | raw/videos/ |
| 随手链接、灵感 | inbox/links、inbox/captures |
| 图片/PDF 附件 | attachments/ |

## Capture 质量门

- 正文完整、来源链接/作者/日期齐全
- 图片、表格、引用的外部文档逐项检查，文末列「附件清单」
- frontmatter 标 `needs_ingest: true`

## Ingest 质量门

- 先查重复刻建页；来源摘要先行，概念/实体不许「无源之页」
- 核心观点是语义摘要，不是正文前几句机械截断
- 双链可解析；index.md 已注册；log.md 已追加
- 具体数字/日期必须能在 raw 原文找到，找不到就删除或标「待核实」
