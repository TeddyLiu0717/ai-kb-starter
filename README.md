# AI 知识库脚手架（Obsidian + AI 智能体）

一个「会自己长大」的个人知识库最小模板：**Obsidian 负责阅读，AI 智能体负责增量维护，纯 Markdown 文件夹，数据完全属于你。**

## 它解决什么问题

- 资料散落在微信、网页、飞书/Notion、视频里，收藏即吃灰
- 直接用 RAG/向量库：问完就忘，没有可积累的知识结构，答案无法回溯
- 手工整理：坚持不过两周

这套模板把知识库拆成 **raw 证据层 → wiki 知识层 → 索引/状态层 → Obsidian 阅读层**，让 AI 按固定协议（`AGENTS.md`）做「捕获 → 编译 → 对账」，你只负责阅读和拍板。

## 5 分钟跑起来

1. 安装 [Obsidian](https://obsidian.md/)（免费），用「打开本地仓库」打开本文件夹
2. 准备一个支持读写本地文件的 AI 智能体（Trae / Claude Code / Cursor / Codex 均可），让它在本目录工作
3. 对它说第一句话：

   > 阅读 AGENTS.md，然后熟悉一下这个知识库

4. 以后只需要两个动词：
   - **「入库」**：把一篇资料存进 `raw/`（只读证据，不做加工）
   - **「编译」**：把 raw 资料编译成 `wiki/` 里的来源摘要 / 概念 / 实体 / 主题页，自动建双链、更新索引

## 目录职责

```text
.
├── AGENTS.md          # 知识库宪法：AI 必须遵守的红线与工作流（最重要）
├── raw/               # 【只读】原始证据：网页、文档原文、转写，只追加不改写
├── inbox/             # 临时收件箱：随手存的链接、灵感，待编译
├── wiki/              # 正式知识层
│   ├── sources/       #   每份 raw 资料对应一页来源摘要（知识的根）
│   ├── concepts/      #   概念 / 方法 / 框架，一个概念一页
│   ├── entities/      #   人物 / 公司 / 产品 / 工具
│   ├── topics/        #   跨来源的主题综述
│   ├── index.md       #   全局索引（每次编译后必须更新）
│   └── log.md         #   变更日志（只追加）
├── templates/         # 四类页面模板
├── config/            # Schema 与入库规则（AI 只读）
├── prompts/           # 可直接复用的指令：捕获 / 编译 / 体检 / 每日增量
├── scripts/kb.py      # 零依赖体检工具：断链 / frontmatter / 孤立页 / 索引覆盖
├── attachments/       # 图片、PDF 等附件
└── drafts/            # 你的私人草稿（AI 只读）
```

## 常用命令

```bash
python scripts/kb.py doctor       # 体检：断链、空摘要、孤立页、索引缺失
python scripts/kb.py stats        # 各层页面数量
```

Windows 每天自动体检（可选）：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-daily-task.ps1
```

## 三条最重要的设计（踩坑换来的）

1. **raw 永远只读、只追加。** AI 会幻觉，而且敢把数字编得有模有样。只要原文在，任何结论都能回溯；新版资料只追加 revision，绝不覆盖旧版。
2. **人机内容分区。** AI 生成内容统一放在 `<!-- AUTO:START -->` / `<!-- AUTO:END -->` 之间，区块外是你的人工作文，AI 不得覆盖。
3. **小批量 + 质量门。** 单次编译 ≤ 10 篇，编译完必过体检（双链可解析、摘要非占位、索引已更新），不达标当场返工，不许把「部分完成」报成「完成」。

## 与 AI 工具的搭配建议

- **Trae / Cursor / Claude Code**：直接在本目录开对话，用 `prompts/` 里的指令
- **定时自动增量**：让智能体的定时任务每天执行 `prompts/04-daily-increment.md`（需要联网拉取你的来源，如飞书/Notion API；纯本地仓库用 Windows 任务计划 + `kb.py doctor` 做每日体检即可）

## 示例内容

`wiki/` 与 `raw/web/` 下有一组「AI 知识库」主题的示例页，看完效果后可整组删除，换成你自己的资料。
