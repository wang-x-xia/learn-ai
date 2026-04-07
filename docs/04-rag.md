# 检索增强生成 (RAG - Retrieval-Augmented Generation)

> RAG 通过将外部知识检索与大语言模型结合，解决了 LLM 知识截止和幻觉问题，是企业级 AI 应用的核心架构之一。

---

## 1. 概述

### 什么是 RAG

RAG (Retrieval-Augmented Generation) 是一种将**信息检索**与**文本生成**结合的技术框架。核心思想：在生成回答之前，先从外部知识库中检索相关信息，然后基于检索到的内容生成回答。

### 为什么需要 RAG

| 问题 | RAG 解决方案 |
|------|-------------|
| **知识截止** | 检索最新文档，突破训练数据时间限制 |
| **幻觉问题** | 基于真实文档生成，减少编造内容 |
| **领域知识** | 接入企业私有数据，无需重新训练 |
| **可溯源** | 回答可追溯到具体文档来源 |
| **成本效率** | 比微调更快速、更经济 |

### RAG vs 微调 vs 提示工程

| 方法 | 适用场景 | 成本 | 实时性 |
|------|----------|------|--------|
| **提示工程** | 简单任务，信息量小 | 低 | 高 |
| **RAG** | 需要外部知识，知识常变 | 中 | 高 |
| **微调** | 需要特定行为/风格 | 高 | 低 |
| **RAG + 微调** | 最高质量要求 | 最高 | 中 |

原始论文: [Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", 2020](https://arxiv.org/abs/2005.11401)

---

## 2. RAG 架构

### 基本流程

```
┌─────────────────────────────────────────────────────┐
│                    离线阶段 (Indexing)                │
│                                                      │
│  文档 → 分块(Chunking) → 嵌入(Embedding) → 向量数据库  │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                    在线阶段 (Query)                   │
│                                                      │
│  用户提问 → 查询嵌入 → 向量检索 → 上下文组装 → LLM生成  │
└─────────────────────────────────────────────────────┘
```

### 详细流程

```
1. 文档加载 (Document Loading)
   ├── PDF, DOCX, HTML, Markdown, CSV...
   └── API, 数据库, 网页爬取...

2. 文档分块 (Chunking)
   ├── 按固定大小
   ├── 按语义边界
   └── 按文档结构

3. 向量化 (Embedding)
   └── 文本 → 高维向量 (768/1536/3072 维)

4. 索引存储 (Indexing)
   └── 存入向量数据库

5. 查询检索 (Retrieval)
   ├── 向量相似度搜索
   ├── 关键词搜索
   └── 混合搜索

6. 重排序 (Reranking)
   └── 对检索结果精排

7. 生成回答 (Generation)
   └── 将检索内容 + 问题 → LLM → 回答
```

---

## 3. 文档处理与分块 (Chunking)

### 分块策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| **固定大小** | 按字符/token 数切分 | 通用场景 |
| **递归分割** | 按分隔符层级切分 (段落→句子→词) | 大多数文本 |
| **语义分块** | 按语义相似度切分 | 高质量要求 |
| **文档结构** | 按标题/章节切分 | 结构化文档 |
| **Sliding Window** | 滑动窗口+重叠 | 防止信息断裂 |

### 分块最佳实践

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,       # 每块大小 (token)
    chunk_overlap=50,     # 重叠区域
    separators=["\n\n", "\n", "。", ".", " ", ""],
)

chunks = splitter.split_documents(documents)
```

### 关键参数

- **chunk_size**: 通常 256-1024 tokens，取决于嵌入模型和应用场景
- **chunk_overlap**: 通常为 chunk_size 的 10-20%，保持上下文连贯
- **元数据**: 保留文档来源、页码、标题等信息用于过滤和引用

---

## 4. 嵌入模型 (Embedding Models)

### 主流模型对比

| 模型 | 厂商 | 维度 | MTEB 排名 | 特点 |
|------|------|------|-----------|------|
| **text-embedding-3-large** | OpenAI | 3072 | 高 | 性能最强，支持降维 |
| **text-embedding-3-small** | OpenAI | 1536 | 中 | 性价比高 |
| **Cohere Embed v3** | Cohere | 1024 | 高 | 多语言，支持压缩 |
| **BGE-M3** | BAAI | 1024 | 高 | 开源，多语言多粒度 |
| **Jina Embeddings v3** | Jina AI | 1024 | 高 | 开源，长文本支持 |
| **GTE-Qwen2** | 阿里 | 多种 | 高 | 开源，中文优秀 |
| **E5-Mistral** | Microsoft | 4096 | 高 | 基于 Mistral 的嵌入 |

### 使用示例

```python
from openai import OpenAI

client = OpenAI()

response = client.embeddings.create(
    model="text-embedding-3-small",
    input="检索增强生成是一种重要的技术"
)

embedding = response.data[0].embedding  # 1536 维向量
```

### 选择建议

- **追求性能**: text-embedding-3-large 或 Cohere Embed v3
- **控制成本**: text-embedding-3-small 或开源模型
- **中文场景**: BGE-M3 或 GTE-Qwen2
- **本地部署**: sentence-transformers + 开源模型

---

## 5. 向量数据库 (Vector Databases)

### 主流数据库对比

| 数据库 | 类型 | 开源 | 特点 | 适用场景 |
|--------|------|------|------|----------|
| **Pinecone** | 云托管 | 否 | 全托管，开箱即用 | 快速上线 |
| **Weaviate** | 自托管/云 | 是 | 混合搜索，GraphQL | 复杂查询 |
| **Milvus** | 自托管/云 | 是 | 高性能，大规模 | 企业级部署 |
| **Qdrant** | 自托管/云 | 是 | Rust 编写，高效 | 高性能需求 |
| **ChromaDB** | 嵌入式 | 是 | 轻量，易用 | 原型开发 |
| **pgvector** | PG 扩展 | 是 | 基于 PostgreSQL | 已有 PG 基础设施 |
| **FAISS** | 库 | 是 | Meta 开发，纯库 | 研究/自定义 |

### 快速上手 (ChromaDB)

```python
import chromadb

client = chromadb.Client()
collection = client.create_collection("my_docs")

# 添加文档
collection.add(
    documents=["RAG 是一种重要技术", "向量数据库存储嵌入"],
    ids=["doc1", "doc2"],
    metadatas=[{"source": "wiki"}, {"source": "blog"}]
)

# 查询
results = collection.query(
    query_texts=["什么是 RAG？"],
    n_results=2
)
```

---

## 6. 检索策略

### 6.1 稠密检索 (Dense Retrieval)

基于嵌入向量的语义相似度搜索：
```
查询向量 · 文档向量 = 余弦相似度
```

### 6.2 稀疏检索 (Sparse Retrieval)

基于关键词匹配的传统搜索：
- **BM25**: 经典的概率检索模型
- **TF-IDF**: 词频-逆文档频率

### 6.3 混合搜索 (Hybrid Search)

```
最终分数 = α × 稠密检索分数 + (1-α) × 稀疏检索分数
```

混合搜索结合了语义理解和精确匹配的优势，通常效果最好。

### 6.4 重排序 (Reranking)

在初步检索后，使用更精确的模型对结果重新排序：

```python
# 使用 Cohere Reranker
import cohere

co = cohere.Client("your-api-key")
results = co.rerank(
    model="rerank-v3.5",
    query="什么是 RAG？",
    documents=retrieved_docs,
    top_n=3
)
```

常用重排模型：
- **Cohere Rerank**: 商业方案，效果优秀
- **bge-reranker**: 开源，BAAI 出品
- **Cross-Encoder**: sentence-transformers 库

### 6.5 高级检索策略

| 策略 | 说明 |
|------|------|
| **Multi-Query** | 将问题改写为多个查询，合并结果 |
| **Parent Document** | 检索小块，返回其父文档（更完整上下文）|
| **Self-Query** | LLM 自动提取过滤条件和语义查询 |
| **HyDE** | 先生成假设答案，用答案做检索 |
| **Step-back** | 先提出更通用的问题做检索 |

---

## 7. 高级 RAG 技术

### RAG 的三个阶段

```
Naive RAG → Advanced RAG → Modular RAG
 (基础)       (增强)        (模块化)
```

### 7.1 GraphRAG (Microsoft)

将文档构建为**知识图谱**，利用图结构增强检索：

```
文档 → 实体抽取 → 关系抽取 → 知识图谱
                                 ↓
查询 → 图遍历 + 向量检索 → 更丰富的上下文 → 生成
```

优势: 能够回答需要跨文档推理的复杂问题

### 7.2 Agentic RAG

将 Agent 能力与 RAG 结合：

```
用户问题 → Agent 分析 → 决定检索策略
                           ├── 需要搜索：向量检索
                           ├── 需要计算：代码执行
                           ├── 需要最新信息：网络搜索
                           └── 信息充足：直接回答
```

### 7.3 Corrective RAG (CRAG)

检索后评估文档相关性，不相关时触发纠正机制：

```
检索文档 → 评估相关性
              ├── 相关 → 直接使用
              ├── 部分相关 → 提取有用部分 + 补充检索
              └── 不相关 → 换策略重新检索 (如网络搜索)
```

### 7.4 Self-RAG

模型自主决定是否需要检索，并自我评估生成质量：

```
问题 → 是否需要检索？
         ├── 是 → 检索 → 评估文档 → 生成 → 评估答案
         └── 否 → 直接生成 → 评估答案
```

---

## 8. 评估与优化

### 评估指标

| 指标 | 说明 |
|------|------|
| **Faithfulness** | 回答是否忠于检索到的文档 |
| **Answer Relevancy** | 回答与问题的相关性 |
| **Context Precision** | 检索内容中有用信息的比例 |
| **Context Recall** | 是否检索到了所有相关信息 |

### 评估框架

| 框架 | 说明 |
|------|------|
| **RAGAS** | 最流行的 RAG 评估框架 |
| **TruLens** | 可观测性+评估 |
| **DeepEval** | 综合 LLM 评估框架 |
| **LangSmith** | LangChain 的监控和评估平台 |

### RAGAS 使用示例

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

result = evaluate(
    dataset=eval_dataset,
    metrics=[faithfulness, answer_relevancy, context_precision]
)

print(result)
# {'faithfulness': 0.85, 'answer_relevancy': 0.92, 'context_precision': 0.78}
```

### 常见问题与优化

| 问题 | 原因 | 优化方案 |
|------|------|----------|
| 检索不到相关文档 | 分块太大/太小，嵌入不佳 | 调整分块策略，换嵌入模型 |
| 检索到但答案不对 | LLM 未利用上下文 | 优化 prompt，换模型 |
| 答案有幻觉 | 文档不够相关 | 加重排序，提高检索质量 |
| 延迟太高 | 检索+生成时间长 | 缓存、预计算、流式输出 |
| 多文档推理弱 | 上下文不连贯 | GraphRAG，多跳检索 |

---

## 9. 实践指南

### 何时选择 RAG

- 需要最新信息（知识库持续更新）
- 需要引用来源（合规/可信度要求）
- 私有数据不能用于训练
- 需要快速上线
- 知识域较广

### 生产部署考虑

```
1. 数据管道自动化 (文档变更 → 自动重新索引)
2. 多租户隔离 (不同用户/组织的数据隔离)
3. 监控和可观测性 (检索质量、延迟、成本)
4. 缓存策略 (高频查询缓存)
5. 回退机制 (检索失败时的处理)
6. 安全防护 (防止提示注入访问未授权数据)
```

### 成本优化

| 策略 | 说明 |
|------|------|
| 分层检索 | 先粗粒度筛选再精细检索 |
| 缓存嵌入 | 避免重复计算 |
| 批量处理 | 合并多次嵌入请求 |
| 开源替代 | 使用开源嵌入模型降低 API 成本 |
| 按需索引 | 只索引高价值文档 |

---

## 10. 发展趋势

### 10.1 多模态 RAG

不仅检索文本，还检索图像、表格、图表：
- 多模态嵌入（CLIP 等）
- 文档中图表的理解和检索
- 视觉问答 + 检索

### 10.2 长上下文 vs RAG

随着上下文窗口增大 (1M+ tokens)，RAG 是否还有必要？

- 长上下文**并不能替代** RAG
- 长上下文适合: 已知的少量文档深度分析
- RAG 适合: 从大量文档中找到相关内容
- 最佳实践: 用 RAG 检索 + 长上下文深度处理

### 10.3 RAG + Agent

RAG 与 Agent 的融合是大趋势：
- Agent 自主决定检索策略
- 多轮检索和推理
- 自适应检索 (根据问题复杂度调整)

### 10.4 结构化 RAG

- Text-to-SQL RAG (将自然语言转为 SQL 查询)
- Table RAG (专门针对表格数据)
- Code RAG (代码库检索)

---

## 参考资料

- Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", 2020 - [arXiv:2005.11401](https://arxiv.org/abs/2005.11401)
- Gao et al., "Retrieval-Augmented Generation for Large Language Models: A Survey", 2024 - [arXiv:2312.10997](https://arxiv.org/abs/2312.10997)
- Edge et al., "From Local to Global: A Graph RAG Approach", 2024 - [arXiv:2404.16130](https://arxiv.org/abs/2404.16130)
- Yan et al., "Corrective Retrieval Augmented Generation", 2024 - [arXiv:2401.15884](https://arxiv.org/abs/2401.15884)
- RAGAS Documentation: https://docs.ragas.io/
- LangChain RAG Guide: https://python.langchain.com/docs/tutorials/rag/
