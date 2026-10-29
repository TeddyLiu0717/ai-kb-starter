---
title: RAG 综述：给普通人的检索增强生成指南
source_type: article
source_url: https://example.com/rag-guide
author: 示例作者
captured_at: 2026-10-28
needs_ingest: true
status: raw
---

# RAG 综述：给普通人的检索增强生成指南

## 原文要点（示例资料，非真实文章）

RAG（Retrieval-Augmented Generation，检索增强生成）让大模型在回答前先去一个外部知识库里检索相关片段，再基于片段生成答案，从而减少幻觉、支持私有知识问答。

典型的 RAG 系统分四步：文档切分（chunking）、向量化（embedding）、入库（向量数据库）、检索后拼接进提示词。它的短板是：问答是一次性的，知识不会沉淀成结构；检索错了答案就错；多文档之间的关系无法表达。

相比之下，「笔记优先」的做法把每篇资料编译成带出处的结构化页面，问答与长期沉淀共用同一套知识层，任何结论都能回溯到原文。
