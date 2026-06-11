---
title: "LeRobot Dataset v3：具身数据的可扩展存储格式"
description: "LeRobot Dataset v3 的完整格式规格：目录布局、info.json schema、Parquet 表结构与分片策略、MP4 视频编码参数、episode 元数据索引机制。"
created: "2026-06-11"
updated: "2026-06-11"
tags:
  - embodied
  - dataset
  - robotics
  - data-infrastructure
  - parquet
review: "2026-06-11"
---

# LeRobot Dataset v3：具身数据的可扩展存储格式

??? note "背景知识"
    - **LeRobot**：Hugging Face 开源的机器人学习框架，提供数据集、预训练模型和训练工具 → [GitHub](https://github.com/huggingface/lerobot)
    - **Apache Parquet**：列式存储格式，支持高效压缩和谓词下推过滤 → [详见](../infrastructure/structured-data-format.md)
    - **Open X-Embodiment (OXE)**：Google DeepMind 主导的大规模机器人数据集联盟，汇聚 >400 GB 跨机器人平台数据

---

具身数据集按 **episode**（一次完整的机器人操作轨迹）组织，每个 episode 包含关节状态、动作、多相机视频等多模态时序信号。v3.0 将多个 episode 聚合到少量大文件中，用关系型元数据记录偏移量来定位每个 episode，从而支撑百万级 episode 规模[^hf-2024-v3][^deepwiki-2026-lerobot]。

## 目录布局

```
dataset_root/
├── meta/
│   ├── info.json                              # 全局 schema（唯一必读入口）
│   ├── stats.json                             # 归一化统计
│   ├── tasks.parquet                          # 任务定义
│   └── episodes/
│       └── chunk-000/
│           └── file-000.parquet               # episode 索引（分块）
├── data/
│   └── chunk-000/
│       ├── file-000.parquet                   # 帧级表格数据（多 episode）
│       └── file-001.parquet
└── videos/
    └── observation.images.laptop/
        └── chunk-000/
            ├── file-000.mp4                   # 视频帧（多 episode）
            └── file-001.mp4
```

文件路径由 `info.json` 中的模板决定，支持不同存储后端（本地、Hub、云）：

```json
{
  "data_path": "data/chunk-{chunk_index:03d}/file-{file_index:03d}.parquet",
  "video_path": "videos/{video_key}/chunk-{chunk_index:03d}/file-{file_index:03d}.mp4"
}
```

**分片配置**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `chunks_size` | 1000 | 每个 chunk 目录最大文件数 |
| `data_files_size_in_mb` | 100 | 单个 Parquet 文件上限 |
| `video_files_size_in_mb` | 200 | 单个 MP4 文件上限 |

文件达到上限时自动轮转到新文件，episode 元数据同步更新偏移量。

---

## meta/info.json — 全局 Schema

数据集打开时唯一必读的文件，定义了所有 feature 的 dtype/shape 和存储配置。

```json
{
  "codebase_version": "v3.0",
  "fps": 30,
  "robot_type": "so_follower",
  "total_episodes": 100,
  "total_frames": 50000,
  "total_tasks": 3,
  "chunks_size": 1000,
  "data_files_size_in_mb": 100,
  "video_files_size_in_mb": 200,
  "splits": { "train": "0:80", "test": "80:100" },
  "data_path": "data/chunk-{chunk_index:03d}/file-{file_index:03d}.parquet",
  "video_path": "videos/{video_key}/chunk-{chunk_index:03d}/file-{file_index:03d}.mp4",
  "features": {
    "observation.state": {
      "dtype": "float32",
      "shape": [12],
      "names": ["shoulder_pan", "shoulder_lift", "..."]
    },
    "observation.images.front": {
      "dtype": "video",
      "shape": [480, 640, 3],
      "names": ["height", "width", "channels"],
      "info": {
        "video.codec": "av1", "video.pix_fmt": "yuv420p",
        "video.fps": 30, "video.g": 2, "video.crf": 30,
        "has_audio": false
      }
    },
    "action": { "dtype": "float32", "shape": [7] }
  }
}
```

**features 字段结构**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `dtype` | string | 见下方 dtype 映射表 |
| `shape` | list\[int\] | 维度定义（含义因 dtype 不同，见下表） |
| `names` | list\[string\] \| null | 各维度命名（含义因 dtype 不同，见下表） |
| `info` | dict \| null | 仅 `video` 类型使用（见下表） |

**dtype 不是封闭枚举**——`np.dtype()` 能解析的任何字符串均合法，另有三个特殊类型[^lerobot-2026-feature-utils]：

| dtype | HF Datasets 列类型 | shape | info | Parquet 存储 |
|-------|-------------------|-------|------|-------------|
| numpy 类型（`float32`、`int64`、`bool` 等） | `shape=(1,)` → `Value(dtype)`；1D → `Sequence(length, Value)`；2D-5D → `Array2D`..`Array5D` | 数据维度，如 `[7]` 表示 7 维向量，`[1]` 表示标量 | null | 数值列 |
| `"video"` | **跳过**（`continue`），不写入 Parquet | `[H, W, C]`，如 `[480, 640, 3]` | 编码参数：`video.codec`、`video.pix_fmt`、`video.fps`、`video.g`、`video.crf`、`has_audio` 等 | 存 MP4，HF `datasets` 层注册了 [`VideoFrame`](https://github.com/huggingface/lerobot/blob/main/src/lerobot/datasets/video_utils.py) 类型（`pa.struct({"path": string, "timestamp": float32})`）解析引用 |
| `"string"` | `Value("string")` → Arrow 变长 UTF-8 | `(1,)` | null | 变长字符串列。故意用 numpy 不认的拼写（`np.dtype("string")` 在 Py3 抛异常）绕开定宽 `U` 路径 |
| `"language"` | 仅 `language_persistent` / `language_events` 两个固定列名使用，schema 定义在 [`language.py`](https://github.com/huggingface/lerobot/blob/main/src/lerobot/datasets/language.py) | `(1,)` | null | 嵌套 struct 列 |

`language` 的两个列结构不同：

- **`language_persistent`**：`List(Struct{role, content, style, timestamp, camera, tool_calls})` — persistent 行在 episode 内所有帧广播，自带 `timestamp`（float32）标记生效时间
- **`language_events`**：`List(Struct{role, content, style, camera, tool_calls})` — event 行只出现在触发帧，无 `timestamp`（由帧本身的时间戳代替）

**可扩展性**：用户可自由添加任意 feature key（如 `observation.custom_sensor`），只需在 `features` 中声明 dtype/shape。`DatasetInfo.from_dict()` 会自动过滤未知字段以兼容旧版本。

---

## meta/stats.json — 归一化统计

存储全局 feature 统计量，用于策略训练时的数据归一化：

```json
{
  "observation.state": {
    "mean": [0.5, 0.3, "..."],
    "std":  [0.2, 0.15, "..."],
    "min":  [-1.0, -0.5, "..."],
    "max":  [1.0, 0.8, "..."],
    "count": 50000
  }
}
```

每个 feature 包含 `mean`/`std`/`min`/`max`（shape 与 feature 一致）和 `count`（样本数）。可选字段 `q01`/`q10`/`q50`/`q90`/`q99` 支持基于分位数的归一化。图像/视频 feature 的统计量为 per-channel（shape `[C, 1, 1]`）。

---

## meta/tasks.parquet — 任务定义

将自然语言任务描述映射到整数 ID，用于 task-conditioned 策略训练。

| 列名 | 类型 | 说明 |
|------|------|------|
| `task_index` | int64 | 任务 ID（0-indexed） |
| `task` | string | 自然语言描述（如 `"Pick the red block"`） |

---

## meta/episodes/ — Episode 索引

以分块 Parquet 存储，每行一个 episode，是数据文件和视频文件的"地址簿"。Episode metadata 没有显式 PyArrow schema 定义——`_flush_metadata_buffer()` 用 `pa.Table.from_pydict()` 从 Python 值自动推断类型，所有整数列均为 int64（PyArrow 对 Python `int` 的默认推断），即使 `chunk_index` / `file_index` 值域远小于此。

**固定列**：

| 列名 | 类型 | 说明 |
|------|------|------|
| `episode_index` | int64 | episode ID |
| `length` | int64 | 帧数 |
| `tasks` | list\[string\] | 任务描述 |
| `dataset_from_index` | int64 | 在 data Parquet 中的起始行（含） |
| `dataset_to_index` | int64 | 在 data Parquet 中的结束行（不含） |
| `data/chunk_index` | int64 | 数据文件的 chunk 编号（值域 < `chunks_size`，默认 < 1000） |
| `data/file_index` | int64 | 数据文件的 file 编号（同上） |

**per-camera 列**（每个视频 key 一组）：

| 列名 | 类型 | 说明 |
|------|------|------|
| `videos/{key}/chunk_index` | int64 | MP4 的 chunk 编号 |
| `videos/{key}/file_index` | int64 | MP4 的 file 编号 |
| `videos/{key}/from_timestamp` | float32 | episode 在 MP4 中的起始时间（秒） |
| `videos/{key}/to_timestamp` | float32 | episode 在 MP4 中的结束时间（秒） |

可选 per-episode 统计列 `stats/{feature}/mean|std|min|max|count`，用于 episode 级归一化。

---

## data/ — 帧级表格数据（Parquet）

每行代表一帧，多个 episode 连续存储在同一文件中。

### 固定列（DEFAULT_FEATURES）

| 列名 | 类型 | 说明 |
|------|------|------|
| `index` | int64 | 全局帧 ID（跨 episode 单调递增） |
| `episode_index` | int64 | 所属 episode |
| `frame_index` | int64 | episode 内帧序号（从 0 开始） |
| `timestamp` | float32 | episode 内时间（秒），`frame_index / fps` |
| `task_index` | int64 | 任务 ID（引用 `tasks.parquet`） |

### 用户定义列

由 `info.json` 的 `features` 决定，典型包括：

- `observation.state`（float32，关节角度/末端位姿）
- `action`（float32，控制指令）
- `observation.images.*`（`dtype: "video"` → 不在 Parquet 中，仅视频引用）

### 存储参数

| 参数 | 值 |
|------|-----|
| 压缩 | Snappy（默认） |
| Dictionary 编码 | 启用 |
| Row Group 大小 | PyArrow 默认（~128 MB） |
| 写入方式 | `pq.ParquetWriter` 流式增量写入 |
| 文件上限 | 100 MB（写入每个 episode 前检查，超限则轮转新文件） |

读取时支持 PyArrow **谓词下推**——按 `episode_index` 过滤，只加载相关 Row Group，避免全量扫描。

---

## videos/ — 多相机视频（MP4）

每个相机 key 独立目录，多个 episode 的帧拼接到同一 MP4 中。

### 编码参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 容器 | MP4 | — |
| 编码器 | `libsvtav1`（AV1） | 压缩比最优；可选 `h264`、`hevc`、`auto` |
| 像素格式 | `yuv420p` | `yuv444p` 在 AV1/HEVC 下不兼容，自动降级 |
| GOP size | 2 | 每 2 帧一个关键帧，保证低延迟随机 seek |
| CRF | 30 | 质量因子（0-51，越低越高质量） |
| Preset | 12（libsvtav1） | 编码速度/质量折衷（0-13，越高越快） |
| 音频 | 保留（若有） | 拼接时 stream copy，不重编码 |
| 分辨率 | 无硬限制 | 由相机输入决定 |
| 帧率 | 全局 `fps`（info.json） | 数据集内所有相机统一 |
| 文件上限 | 200 MB | 超限轮转新文件 |

### 硬件编码器回退链（`vcodec="auto"`）

按优先级探测可用编码器，全部不可用时回退到软件编码：

```
h264_videotoolbox → hevc_videotoolbox → h264_nvenc →
hevc_nvenc → h264_vaapi → h264_qsz → libsvtav1（回退）
```

### CRF 跨编码器映射

不同硬件编码器不直接支持 CRF，需要映射：

| 编码器 | 质量参数 | 映射方式 |
|--------|----------|----------|
| libsvtav1 / h264 / hevc | `-crf` | 直接使用 |
| h264_videotoolbox | `-q:v` | `max(1, min(100, 100 - crf * 2))` |
| h264_nvenc | `-qp` + `rc=constqp` | CRF 值作为 QP |
| h264_vaapi / h264_qsz | `-qp` / `-global_quality` | CRF 值映射 |

### Episode 边界定位

帧访问通过 episode 元数据中的时间戳偏移量完成：

```
episode_meta.videos/{key}/from_timestamp = 12.5s
query: frame_index=15 → timestamp = 15/30 = 0.5s
seek position: 12.5 + 0.5 = 13.0s
```

拼接使用 FFmpeg concat demuxer（stream copy，不重编码）。

### 编码模式

- **批量编码**（默认）：帧先存为临时 PNG，`save_episode()` 时编码为 MP4
- **流式编码**（`streaming_encoding=True`）：帧实时推入 per-camera 后台线程编码，`save_episode()` 瞬间完成；队列满时丢弃最旧帧（`encoder_queue_maxsize=30`，约 1s@30fps）

---

## 与 v2.1 对比速览

| 维度 | v2.1 | v3.0 |
|------|------|------|
| 文件组织 | 每 episode 一个文件 | 多 episode 聚合到大文件 |
| Episode 定位 | 文件名匹配 | 元数据偏移量（O(1)） |
| 元数据格式 | 单个 JSON Lines | 分块 Parquet |
| 视频存储 | per-episode MP4 | 拼接 MP4（帧级偏移追踪） |
| 流式访问 | 不支持 | 原生支持（可回溯迭代器） |
| 路径解析 | 硬编码 | 模板化 |
| 数据集合并 | 需重写数据文件 | 仅更新元数据索引 |

---

## 参考资料

[^hf-2024-v3]: Hugging Face. *LeRobot Datasets v3*. 2024. https://huggingface.co/docs/lerobot/lerobot-dataset-v3
[^deepwiki-2026-lerobot]: DeepWiki. *LeRobot Dataset Format and Structure — 源码级格式解析*. 2026. https://deepwiki.com/huggingface/lerobot/2.1-dataset-format-and-structure
[^lerobot-2026-feature-utils]: `feature_utils.py` — dtype 验证（`validate_feature_dtype_and_shape`）与 Parquet schema 映射（`get_hf_features_from_features`）。https://github.com/huggingface/lerobot/blob/main/src/lerobot/datasets/feature_utils.py
