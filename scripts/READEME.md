## Ragflow Upload打包脚本

### 功能说明
该脚本用于将`Ragflow Upload`项目打包成可执行文件。打包过程会生成一个独立的客户端程序文件，包含所有必要的依赖和资源文件。

### 打包环境要求
- python 3.10+
- pyInstaller
- customtkinter
- 项目所需的其他依赖包（见requirements.txt）

### 打包流程
1. 清理旧的构建文件（build和dist目录）
2. 创建新的dist目录
3. 复制并处理配置文件
4. 使用PyInstaller打包，包含以下内容：
   - 主程序文件
   - 配置文件
   - 资源文件
   - 依赖库
   - 图标文件

### 使用方法
1. 确保已安装所有依赖（项目根目录执行）：
   ```bash
   pip install -r requirements.txt
   pip install -r scripts/requirements.txt
   ```

2. 运行打包脚本（项目根目录执行）：
   ```bash
   python scripts/build.py
   ```

3. 打包完成后，可执行文件将输出到`dist`目录，程序运行时将从用户目录（`~/.ragflow_upload`）下读取/保存配置

### 注意事项
- 打包过程会自动处理配置文件，将`configs.demo.py`复制并重命名为`configs.py`
- 打包后的程序包含完整的依赖，无需额外安装Python环境
- 程序图标使用`scripts/icon.png`
- 打包过程会自动包含以下目录和文件：
  - ragflows目录
  - utils目录
  - requirements.txt
  - LICENSE
  - README.md
  - 其他必要文件/依赖

### 常见问题
1. 如果打包失败，请检查：
   - Python环境是否正确
   - 是否已安装所有依赖
   - 是否有足够的磁盘空间
   - 是否有文件被其他程序占用

2. 如果运行打包后的程序出现问题，请检查：
   - 配置文件是否正确
   - 是否有必要的系统权限
   - 是否被杀毒软件拦截

3. linux平台下运行前需要添加可执行权限
   ```shell
   sudo chmod +x RagFlowUpload-xxx
   ```

4. mac平台下运行前会可能提示`无法打开“RagFlowUpload”，因为它来自身份不明的开发者。`，可在`系统偏好设置-安全性与隐私-通用-允许`中选择`允许`，然后重新运行。

5. 目前测试过正常运行的系统版本有：`windows10`、`mac14（intel）`、`ubuntu24.04`，其他版本的系统若发现存在兼容问题，请改为源码方式运行。