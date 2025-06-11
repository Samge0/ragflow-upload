## 上传文档到RagFlow知识库
[RagFlow](https://github.com/infiniflow/ragflow)是一个基于 LLM 的问答系统，能够快速构建智能问答平台。然而，RagFlow 默认的知识库上传界面存在一些局限性：每次只能上传有限数量的文件，并且上传后还需手动启动解析流程，当需要上传大量文件时，这样的操作便显得有些繁琐。

为了简化这一过程，我编写了一个脚本，该脚本可以遍历指定目录，自动逐个将文档上传至 RagFlow 知识库，并立即启动解析。当一个文档解析完成后，脚本将自动上传并解析下一个文档。特别是在需要上传大量文件时，这显著减少了人工干预，避免了手动分批上传和解析的等待时间。

（例如，我自己需要将mac中所有备忘录内容导入到知识库中查询）

### 独立客户端
可以在[Releases](https://github.com/Samge0/ragflow-upload/releases)这里的`Assets`中下载编译好的最新版本客户端，打开客户端后根据[issues#2](https://github.com/Samge0/ragflow-upload/issues/2)填写相关配置即可。

如果想要自己构建`windows / MAC / linux`系统下的可执行程序，可参考[scripts/README.md](scripts/README.md)中的说明进行构建。

![image](https://github.com/user-attachments/assets/34ded25d-6fc2-4648-a66f-74464d246d49)

如果需要以源码方式运行，可参考下面几个步骤：

### 使用[miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install#power-shell)创建env环境
```shell
conda create -n ragflow-upload python=3.10.13 -y
```

### 激活环境
```shell
conda activate ragflow-upload
```

### 安装依赖
```shell
pip install -r requirements.txt
```

## 复制并配置[ragflows/configs.py](ragflows/configs.py)
关于配置文件的说明可参考这个：[issues #2](https://github.com/Samge0/ragflow-upload/issues/2)
```shell
cp ragflows/configs.demo.py ragflows/configs.py
```

### 上传文档
```shell
python ragflows/main.py
```

### 常见问题
<details> <summary> 执行脚本提示: ModuleNotFoundError: No module named 'ragflows' </summary>

> 一般在`vscode`/`pycharm`或者其他IDE中执行时不会遇到这个问题，但如果直接在终端窗口中执行时可能会遇到。

解决方法：

在执行脚本前，配置临时环境变量`PYTHONPATH`指向当前项目目录（`.`表示当前所在目录）。
- Linux/macOS系统：
    ```bash
    export PYTHONPATH=.
    python ragflows/main.py
    ```

- Windows系统 (CMD)：
    ```shell
    set PYTHONPATH=.
    python ragflows/main.py
    ```

- Windows系统 (PowerShell)：
    ```shell
    $env:PYTHONPATH = "."
    python ragflows/main.py
    ```
</details>

### 相关截图
![image](https://github.com/user-attachments/assets/13c93d4a-66fd-4083-ab2c-75c93ef94ab0)
![image](https://github.com/user-attachments/assets/aad9dfb0-3231-4b33-8768-08a2d99cf47e)
