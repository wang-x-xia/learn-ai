---
title: "LanceDB：基于 Lance 列式格式的多模态 ML 数据存储"
description: "LanceDB 通过 Lance 列式文件 + Manifest 驱动的版本化数据管理，把向量、标量、多模态 Blob 统一交给文件层管理"
created: "2026-07-22"
updated: "2026-07-22"
tags:
  - vector-db
  - lance
  - data-format
  - storage
  - open-source
review:
---

# LanceDB

??? note "背景知识"
    - **Lance 文件格式**：去 Row Group 化的列式 ML 数据格式，Fragment + 独立分页 → [详见](../infrastructure/structured-data-format.md)
    - **MVCC（多版本并发控制）**：每次写入生成新版本、旧版本保留的并发控制模式
    - **Apache Arrow**[^arrow-2025]：语言无关的列式内存格式，支持零拷贝跨进程 / 跨语言共享 → [详见](../infrastructure/structured-data-format.md)
    - **Blob**：二进制大对象，常见的有图片、音频、视频、PDF 等多模态文件

---

| 属性 | 值 |
|------|-----|
| **开发者** | LanceDB 公司（原 lance-db/lancedb，2023 年成立） |
| **开源协议** | Apache 2.0 |
| **GitHub** | [lancedb/lancedb](https://github.com/lancedb/lancedb) |
| **底层格式** | [lance-format/lance](https://github.com/lance-format/lance)（Rust 实现，Apache 2.0） |
| **语言绑定** | Python / Rust / TypeScript / Java（多语言一等公民） |
| **存储后端** | 本地文件系统 / S3 / Azure Blob / GCS（同一套 Object Store 抽象） |
| **形态** | 嵌入式库 + 托管服务（[LanceDB Cloud](https://lancedb.com)） |

**一句话定位**：LanceDB 把**原始数据（向量、标量、多模态 Blob）、Schema 演进、版本控制统一交给文件层管理**——文件系统 + Manifest + Lance 文件就是整个数据库，没有独立的服务进程（嵌入式形态）或仅一层薄的对象存储适配器（Cloud 形态）。

---

## 核心问题：多模态数据的存储拼装困境[^structured-data-2026]

多模态 ML 工作负载的典型存储需求是：原始大文件（图片、音频、视频）+ 结构化元数据（标签、时间戳、来源）+ 派生特征（embedding、CLIP 向量）。传统方案是把这些拆给不同的子系统：

```
传统多模态数据栈（拼装方案）：

  ┌─────────────┐   ┌──────────────┐   ┌──────────────┐
  │ 对象存储     │   │ 关系数据库   │   │ 向量数据库   │
  │ (S3/MinIO)  │   │ (Postgres)   │   │ (Milvus 等)  │
  └─────────────┘   └──────────────┘   └──────────────┘
   原始图片/视频      元数据/标签         embedding 索引
        │                  │                  │
        └──── 三套一致性协议、两套备份策略、三个监控告警 ────┘
```

三个典型问题：

1. **跨系统一致性**：上传一张图片要先写 S3、再写 Postgres、再写 Milvus，每一步都可能失败留下"孤儿记录"
2. **JOIN 代价**：查询时要在三个系统间做 key 关联，任何一处 schema 漂移都会导致结果错误
3. **备份与生命周期**：三个系统的备份策略、数据湖分层、归档策略需要分别维护

LanceDB 的解法：**让 Lance 文件格式承担一切**。原始 Blob、元数据、向量、统计信息、删除位图全部存进同一套文件系统，靠 Manifest 文件驱动版本化。

---

## 技术亮点

### Lance 文件格式：列存 + Blob 一等公民

LanceDB 的所有数据都存在 [Lance 格式](https://github.com/lance-format/lance)[^lance-format-2025]文件里。Lance 格式继承 Parquet 的列存哲学，但做了三处关键重写（详见 [结构化数据格式文档](../infrastructure/structured-data-format.md)）：

1. **去掉 Row Group 概念**：每列独立分页，宽表只读一列不解析其他列的元数据
2. **Mini-block 压缩**：128 行一组自适应压缩（FSST / RLE / Bit-packing），随机取 1 行只需 1-2 次 IO
3. **原生 Blob 类型**：图片、音频、视频作为 schema 一等公民存储（详见下文 Blob V2 章节）

Lance 文件内部结构：

```
Lance Data File (.lance)
├─ Schema（支持标量 + 向量 + Blob + 嵌套结构）
├─ Column Indexes（每列 min/max/null_count 统计）
├─ Pages（每列独立分页，Mini-block 压缩）
└─ Deletion Vector（标记被删除的行 ID，按行号位图编码）
```

**关键设计决策**：删除是**逻辑删除**——只在文件末尾追加一个 deletion vector，记录被删除的行 ID，原始数据不动。这让"删除"和"插入"一样便宜，避免重写整个大文件。

---

### Manifest + Fragment：版本化数据集的元数据层

单个 Lance 文件只能装下几百 GB 的数据。LanceDB 通过 **Manifest 文件**把多个 Fragment（每个 Fragment = 1 个 Lance 文件 + 1 个 deletion vector）组织成一个完整的"数据集"。

```
my_dataset.lance/                    ← LanceDB 的数据库 / 表目录
├── _versions/                       ← 版本链
│   ├── 1-manifest.uuid.bin
│   ├── 2-manifest.uuid.bin
│   └── 3-manifest.uuid.bin
├── _transactions/                   ← 事务日志（可选，用于审计）
├── data/
│   ├── frag-001.lance              ← Fragment：1 个数据文件
│   ├── frag-001.dv                ← Fragment 1 的删除位图
│   ├── frag-002.lance
│   └── frag-002.dv
└── _indices/
    ├── vector_idx.ivf              ← ANN 索引（向量场景）
    ├── text_idx.inverted           ← 全文索引（Tantivy）
    └── col_a.bloom                 ← Bloom Filter（等值谓词）
```

**Manifest 文件的内容**：

``` rust
struct Manifest {
    version: u64,                   // 自增版本号
    schema: Schema,                  // 当前 schema（支持历史回放）
    fragments: Vec<Fragment>,        // 所有 fragment 的元数据
    indices: Vec<Index>,             // 已构建索引的元数据
    timestamp: i64,
    writer_version: String,
}

struct Fragment {
    id: u64,
    files: Vec<FragmentFile>,        // 物理文件列表
    physical_rows: u64,
    deletion_file: Option<DeletionFile>,
}
```

**每次写入的流程**：

``` mermaid
sequenceDiagram
    participant Client
    participant ObjectStore
    participant Manifest

    Client->>ObjectStore: 1. 写新 fragment（frag-NNN.lance + frag-NNN.dv）
    ObjectStore-->>Client: ok
    Client->>Manifest: 2. 写新 manifest（version = N+1）
    Note over Manifest: 通过 Object Store 的 rename() 原子替换
    Manifest-->>Client: ok
    Client->>Client: 完成，旧 manifest 不删除
```

**核心创新**：版本切换通过对象存储的 **rename 原子性** 实现（S3 / Azure / GCS 都支持 conditional rename），不会留下"manifest 写到一半"的状态。这与 Git 用 ref 文件切换 HEAD 的思路一脉相承。Time travel 因此是免费的：写一个版本号即可读取任意历史快照。

---

### 数据写入：Append / Overwrite / Update / Delete / Merge

LanceDB 在 Manifest 层抽象出五种写入语义，每种都对应一个 manifest 版本：

| 操作 | 行为 | 对旧数据的影响 |
|------|------|---------------|
| **Append** | 追加新 fragment | 完全不动 |
| **Overwrite** | 用新 fragment 集替换 | 旧 fragment 保留为历史版本 |
| **Update** | 写入新 fragment（含更新行）+ 旧 fragment 的删除标记 | 旧 fragment 加 deletion vector |
| **Delete** | 旧 fragment 加 deletion vector | 数据保留，可被 compaction 物理删除 |
| **Merge / Upsert** | Update + Delete 的组合，常用于 RAG 数据去重 | 同 Update + Delete |

**关键的工程权衡**：

- **删除是逻辑的**：不立即回收磁盘，需要配合 Compaction 把带删除标记的 fragment 重写为干净 fragment
- **MVCC 不阻塞读**：所有 reader 通过 manifest 版本号快照隔离，正在写入的新版本对老 reader 不可见
- **多 reader 隔离**：分析师查 v5、训练任务查 v8，两者互不干扰，这是数据湖才有的能力

---

### 配套查询能力（索引层简述）

LanceDB 在文件层之上提供了若干索引能力，用于加速不同形态的查询（**[官方文档](https://lancedb.github.io/lancedb/ann/)[^lancedb-2025-docs]**）：

| 索引类型 | 加速场景 | 备注 |
|---------|---------|------|
| **IVF-PQ / HNSW** | 向量 ANN 检索 | 与 fragment 同目录，由 manifest 管理 |
| **倒排索引（Tantivy）** | 全文检索 | 与 Lance 列存共享 IO |
| **Bloom Filter** | 等值 / IN 谓词 | 列级小文件 |
| **Bitmap** | 低基数列精确过滤 | 列级小文件 |
| **Column Index** | min/max 范围跳过 | 每列内置，无需手动维护 |

由于本篇聚焦数据文件管理，向量索引的算法细节（IVF 聚类、PQ 量化、HNSW 图结构）不展开，详见 [向量检索算法综述](https://lancedb.github.io/lancedb/ann/)。

---

## 多模态 Blob V2：存储策略与最佳实践

Lance 文件格式原生支持 `Blob` 类型，LanceDB 在上层提供四种存储语义（[官方文档](https://lancedb.github.io/lance/blob.html)[^lance-blob-2025]）。这是 LanceDB 多模态场景最关键的设计决策，也是与外挂对象存储方案最本质的差异。

### 四种存储语义的内部机制

| 存储方式 | 文件布局 | 读 IO 模式 |
|---------|---------|-----------|
| **Inline** | Blob 嵌入 Lance 列 page 内，与其他标量列同 IO | 1 次顺序读出整行 |
| **Packed** | 同 fragment 内独立 blob block，紧凑顺序存储 | 1-2 次随机 IO，按行号定位 |
| **Dedicated** | 每个 blob 一个独立 `.lance` 文件 | 1 次 IO 单文件（适合大文件） |
| **External** | 仅存 URI，blob 留在原位（S3/本地） | 0 Lance 端 IO，访问完全外部化 |

### 存储策略选择决策矩阵

**核心判断因素**：blob 大小 + 访问模式 + 存储总量。下面是经过社区实践沉淀的决策表：

| Blob 大小 | 单库总量 | 访问模式 | 推荐策略 | 理由 |
|----------|---------|---------|---------|------|
| < 64KB | 任意 | 单行随机读 | **Inline** | 整行一次读出，避免小文件 IO 与碎片化 |
| 64KB - 几 MB | 数十万 - 数百万 | 批量训练 | **Packed** | 顺序 IO 友好，inode 数可控 |
| 几 MB - 几 GB | 数万 - 数十万 | 单文件随机读 | **Dedicated** | 大文件独立读取，避免拉整个列 |
| 已有 S3 桶 | TB+ | 不重复存储 | **External** | 不复制数据，LanceDB 仅承担元数据 + 索引 |

### Schema 设计模式

LanceDB 多模态表的常见 schema 设计有两种：

**模式 A：元数据 + Blob 同表**（小到中等规模推荐）

```
Table: images
├─ id: int64
├─ created_at: timestamp
├─ tags: list<utf8>
├─ caption: utf8
└─ image: blob            ← Inline 或 Packed
```

适合数十万到数百万行的多模态数据集。所有元数据与 Blob 共用 fragment，列统计可直接加速"最近一周的图片"等过滤。

**模式 B：Blob 外置 + 元数据内联**（大规模推荐）

```
Table: images_meta
├─ id: int64
├─ created_at: timestamp
├─ s3_uri: utf8            ← External 模式存原图 URI
└─ thumbnail: blob         ← Inline 模式存缩略图（< 64KB）
```

适合已有 S3 数据湖、Blob 总量 TB 级的场景。LanceDB 只承担元数据 + 缩略图 + 索引，避免复制 TB 级原始数据。

### 与"外挂对象存储 + 元数据库"方案的对比

| 维度 | 外挂对象存储 + 元数据库 | LanceDB |
|------|----------------------|---------|
| **跨系统一致性** | 写 S3 + 写元数据库两步，需事务或补偿 | 原子写 fragment，天然一致 |
| **备份** | S3 备份 + 元数据库备份两套 | 备份整个 `.lance/` 目录即可 |
| **版本控制** | 元数据库可，Blob 对象存储不可 | MVCC 覆盖元数据 + Blob |
| **删除** | 软删元数据 + 异步删 S3 对象 | Deletion vector + Compaction |
| **多模态 + 元数据 JOIN** | 跨系统，N+1 查询 | 单表，零开销 |
| **碎片化风险** | 数千万 4KB 小文件对 inode 压力大 | Packed 合并存储可控 |

**典型陷阱**：

- **Inline 滥用导致 IO 放大**：把所有图片都设 Inline，单行变成数 MB，列统计失效、范围扫描变慢
- **Packed 文件过度膨胀**：把 50MB 视频也用 Packed，导致 fragment 过大、Compaction 困难
- **External 模式的"假副本"**：在 S3 上删除原始文件，LanceDB 的引用变成"僵尸指针"
- **忽略 Compaction**：持续 Update/Delete 让 deletion vector 标记 > 30% 行，查询时仍要扫这些行，性能下降——周期性 `dataset.optimize.compact_files()` 是必须的

### 生命周期管理

```
数据写入
  ↓
热数据（频繁访问，Packed / Dedicated 优化读性能）
  ↓ [Compaction 整理删除标记]
温数据（按访问频率分离冷热）
  ↓ [Export / Archive]
冷数据（External 模式 → Glacier / 归档 S3）
  ↓
Time Travel 仍可读历史版本（manifest 链保留）
```

---

### 零拷贝 Schema 演进

Schema 演进在 Manifest 层完成，**不需要重写任何 data file**：

| 操作 | 行为 | 数据文件 IO |
|------|------|------------|
| **新增列** | 写入新 fragment，旧 fragment 该列填空 | 0（读取时按 null 补齐） |
| **删除列** | Manifest 删除该列元数据，旧 fragment 不动 | 0（compact 时回收） |
| **重命名列** | Manifest 更新字段名 | 0 |
| **新增嵌套字段** | 同新增列 | 0 |

这与 Parquet 的 schema 演进形成对比——Parquet 改 schema 通常需要全表重写。LanceDB 走的是 "Postgres 表 + 多 fragment" 的路线：旧数据按旧 schema 读，新数据按新 schema 读，schema 差异在 Manifest 层抹平。

多模态场景特别受益：业务初期只有 `image` 列，后期加 `caption_embedding`、`ocr_text`、`thumbnail` 等列无需重写历史数据。

---

## 生态集成

LanceDB 已成为 Python ML 栈的事实标准之一：

- **LangChain / LlamaIndex**：默认向量库选项之一
- **PyTorch**：`LanceDataset` 直接作为 `DataLoader` 数据源（[集成文档](https://lancedb.github.io/lance/integration/pytorch.html)[^lance-pytorch-2025]）
- **DuckDB**：可通过 `duckdb` 直接读 Lance 文件做 SQL 分析
- **Polars**：原生支持读 Lance 文件
- **Apache Arrow**[^arrow-2025]：Lance 文件的读取 / 写入直接走 Arrow buffer，零拷贝对接 DuckDB / Pandas / Spark
- **PyIceberg**：Iceberg 表的底层可换成 Lance 文件

---

## 为什么值得知道

1. **"数据 + 元数据 + 版本化"三位一体的存储哲学**：LanceDB 证明了对于 ML 工作负载，把所有数据层都交给文件系统的对象存储抽象（+ Manifest 驱动版本化）比传统"独立服务子系统"更简洁。这与 DuckDB 用单文件嵌入式 OLAP 引擎挑战 ClickHouse 的思路一脉相承
2. **MVCC 在 ML 数据栈的天然适配**：多模态数据天然只追加（旧数据少修改），这让 MVCC 在 LanceDB 里几乎没有传统 OLTP 的并发开销，却换来了 time travel / 事务回滚 / 多 reader 隔离这些数据湖才有的能力
3. **多模态 RAG 时代的原生存储**：Blob V2 的四种语义让 LanceDB 能成为多模态 RAG 系统的"原生存储"——不需要在外挂一个 MinIO 来管原图，一份 `.lance/` 目录同时承担元数据 + Blob + 向量索引
4. **嵌入式向量库的趋势代表**：与 Chroma 类似的"库形态"向量数据库正在成为新主流——避免维护一个独立服务、版本与代码同步、用文件做版本控制。LanceDB 是这个趋势里最有"系统设计深度"的那个
5. **具身数据栈的落地**：Lance 的 Blob V2 + Manifest 模式直接复用到 LeRobot 数据集 → [lerobot-lancedb](../embodied-infrastructure/lerobot-lancedb.md)，实现 2-5x 训练吞吐提升

---

## 参考资料

[^lance-format-2025]: Lance Authors. *Lance File Format Specification*. 2025. https://lancedb.github.io/lance/format.html
[^lancedb-2025-docs]: LanceDB Authors. *LanceDB User Guide & ANN Index*. 2025. https://lancedb.github.io/lancedb/
[^lance-pytorch-2025]: Lance Authors. *Lance PyTorch Integration*. 2025. https://lancedb.github.io/lance/integration/pytorch.html
[^lance-blob-2025]: Lance Authors. *Lance Blob V2 Specification*. 2025. https://lancedb.github.io/lance/blob.html
[^arrow-2025]: Apache Arrow Authors. *Apache Arrow: A cross-language development platform for in-memory data*. 2025. https://arrow.apache.org/
[^structured-data-2026]: Learn AI. *结构化数据格式与 GPU 亲和性*. 2026. https://github.com/wang-x-xia/learn-ai/blob/main/docs/infrastructure/structured-data-format.md
