# RAGFlow 文档批量上传工具

基于 [RAGFlow](https://github.com/infiniflow/ragflow) v0.26.2+ API 的文档批量上传、解析工具。

RagFlow 默认知识库上传界面存在部分局限性：每次只能上传有限数量的文件，当需要上传大量文件时，操作可能有点繁琐。

为了简化这一过程，我编写了本工具，可以自动遍历指定目录及子目录，逐个将文档上传至 RagFlow 知识库并解析。在需要上传大量文件时，可减少手动分批上传和解析的等待耗时，解放双手。

（例如，我自己需要将mac中所有备忘录内容导入到知识库中）

## 功能特性

- ✅ **批量上传** - 支持批量上传文档到 RAGFlow 知识库
- ✅ **自动解析** - 上传后自动进行文档切片和解析
- ✅ **进度监控** - 实时监控文档解析进度
- ✅ **元数据管理** - 支持为文档设置自定义元数据
- ✅ **处理进度记录** - 自动记录每个文件的处理状态，中断后重新运行会跳过已完成的文件
- ✅ **纯 API / SDK 模式** - 无需数据库依赖，完全基于 RAGFlow API / SDK

## 独立客户端

可以在 [Releases](https://github.com/Samge0/ragflow-upload/releases) 下载编译好的最新版本客户端。根据 [这个issues](https://github.com/Samge0/ragflow-upload/issues/44) 填写相关配置即可。

> **版本选择说明**（本次 `v1.0.7+ragflow0.26.2` 距上一版 `v1.0.6-alpha` 发布相差 11 个月，跨度较大，请按所使用的 RAGFlow 版本选择对应的客户端）
>
> - **RAGFlow v0.26.2+** 用户：请下载最新版 `v1.0.7+ragflow0.26.2`，本工具已基于新版 API / SDK 重构。
> - **RAGFlow 老版本（约 v0.19）** 用户：由于 RAGFlow API 变更较大，新版本客户端不再兼容，请继续使用 [v1.0.6-alpha](https://github.com/Samge0/ragflow-upload/releases/tag/v1.0.6-alpha)（最后更新于 2025-07-22）。

如果想要自己构建 `Windows / macOS / Linux` 系统下的可执行程序，可参考 [scripts/README.md](scripts/README.md) 中的说明进行构建。

## 系统要求

- Python 3.14+
- RAGFlow v0.26.2+

## 安装

### 1. 克隆项目

```bash
git clone https://github.com/Samge0/ragflow-upload.git
cd ragflow-upload
```

### 2. 创建环境

```bash
# 使用 miniconda
conda create -n ragflow-upload python=3.14 -y
conda activate ragflow-upload

# 或使用 uv
uv venv --python 3.14
# Windows: .\.venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

> 注：以下配置方式适用于**源码运行**。如果使用 [Releases](https://github.com/Samge0/ragflow-upload/releases) 中的打包客户端，启动后直接在图形界面填写配置即可，无需手动编辑配置文件。

源码运行时，先将 `ragflows/configs.demo.py` 复制为 `ragflows/configs.py`，然后编辑 `configs.py`：

```python
# RAGFlow API 配置
API_URL = 'http://localhost:80/api/v1'           # API服务器地址
API_KEY = 'ragflow-xxxxxx'                         # API密钥
DATASET_ID = 'dataset-12345'                       # 知识库ID
DATASET_NAME = 'my_dataset'                        # 知识库名称

# 文档处理配置
CHUNK_METHOD = 'naive'                            # 分块方法
DOC_DIR = '/path/to/documents'                     # 文档目录
DOC_SUFFIX = 'md,txt,pdf,docx'                     # 支持的文件后缀
DOC_MIN_LINES = 6                                  # 最小文件行数

# 解析配置
ONLY_UPLOAD = False                                # 仅上传不解析
PROGRESS_CHECK_INTERVAL = 5                        # 解析进度检查间隔
ENABLE_PROGRESS_LOG = True                         # 启用进度日志
FIRST_PARSE_WAIT_TIME = 0                          # 首次解析等待时间

# 元数据配置
METADATA_SUFFIX = '.meta.json'                    # 元数据文件后缀
```

### 获取 API 密钥

获取路径：点击Ragflow首页右上角用户头像 -> 左下角【API】 -> 点击【API KEY】 -> 点击【创建新密钥】 -> 复制`ragflow-`开头的密钥即可

访问 [{Ragflow首页URL}/user-setting/api](http://localhost:80/user-setting/api) 页面创建 API KEY，然后将其配置到 `API_KEY` 项。

## 使用方法

### 基本使用

在项目根目录执行：

```bash
# Python 方式
python -m ragflows.main

# uv 方式
uv run python -m ragflows.main
```

### 准备文档

1. 将文档放入配置的 `DOC_DIR` 目录
2. 支持的文件格式：`.md`, `.txt`, `.pdf`, `.docx`
3. （可选）为文档添加元数据文件

### 元数据文件

如需为文档添加元数据，创建同名但以 `.meta.json` 结尾的文件：

```
documents/
├── report.pdf
├── report.pdf.meta.json    # report.pdf 的元数据
├── manual.docx
└── manual.docx.meta.json   # manual.docx 的元数据
```

元数据文件格式：

```json
{
  "author": "张三",
  "category": "技术文档",
  "tags": ["API", "开发指南"],
  "version": "1.0"
}
```

## 分块方法

RAGFlow 支持多种分块方法：

| 方法 | 说明 | 适用场景 |
|------|------|----------|
| `naive` | 简单分块 | 通用文档 |
| `general` | 通用分块 | 混合内容 |
| `paper` | 论文分块 | 学术论文 |
| `book` | 书籍分块 | 长篇书籍 |
| `laws` | 法律条文 | 法律文档 |
| `presentation` | 演示文稿 | PPT 幻灯片 |
| `manual` | 手册分块 | 技术手册 |
| `qa` | 问答分块 | 问答对 |

## 处理进度记录

工具会自动记录每个文件的处理状态（待处理/已上传/解析中/完成/失败），中断后重新运行会自动跳过已完成的文件，仅继续处理未完成或失败的文件。

如需重新开始，删除缓存文件：

```bash
# Windows
del ~/.ragflow_upload/state_*.json

# Linux/Mac
rm ~/.ragflow_upload/state_*.json
```

## 常见问题

<details>
<summary>执行脚本提示: ModuleNotFoundError: No module named 'ragflows'</summary>

一般在 `vscode`/`pycharm` 或者其他 IDE 中执行时不会遇到这个问题，但如果直接在终端窗口中执行时可能会遇到。

解决方法：

**推荐**：在项目根目录使用 `-m` 方式运行（无需配置 `PYTHONPATH`）：

```bash
python -m ragflows.main
```

**或者**：手动配置临时环境变量 `PYTHONPATH` 指向当前项目目录（`.` 表示当前所在目录）。

- Linux/macOS 系统：
  ```bash
  export PYTHONPATH=.
  python ragflows/main.py
  ```

- Windows 系统 (CMD)：
  ```bash
  set PYTHONPATH=.
  python ragflows/main.py
  ```

- Windows 系统 (PowerShell)：
  ```bash
  $env:PYTHONPATH = "."
  python ragflows/main.py
  ```
</details>

<details>
<summary>认证失败或 API 连接错误</summary>

检查 `API_KEY` 配置是否正确，确保密钥有效且未过期。检查 `API_URL` 是否正确配置。
</details>

<details>
<summary>知识库不存在</summary>

- 请先在 RAGFlow Web 界面手动创建知识库
</details>

## 相关截图

![上传界面](https://github.com/user-attachments/assets/13c93d4a-66fd-4083-ab2c-75c93ef94ab0)
![配置界面](https://github.com/user-attachments/assets/aad9dfb0-3231-4b33-8768-08a2d99cf47e)

## 技术支持

- GitHub: https://github.com/Samge0/ragflow-upload
- RAGFlow 官方文档: https://ragflow.io/docs

## 许可证

MIT License
