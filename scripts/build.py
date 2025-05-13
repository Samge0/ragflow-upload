import os
import shutil
import subprocess
import platform

def _clean_file(_path: str, is_dir=False):
    """清理文件或目录"""
    if not os.path.exists(_path):
        return
    if os.path.isfile(_path):
        os.remove(_path)
    elif is_dir and os.path.isdir(_path):
        shutil.rmtree(_path)

def build():
    """执行打包流程"""
    print("开始打包...")
    
    # 清理旧的构建文件
    _clean_file("build", True)
    _clean_file("dist", True)
    
    # 创建dist目录
    os.makedirs("dist", exist_ok=True)
        
    # 输出名称
    OUTPUT_NAME = "RagFlowUpload"
    
    # 区分平台的路径分隔符
    path_separator = ";" if platform.system().lower() == "windows" else ":"
    
    # 图标路径
    icon_path = "scripts/icon.ico"
    
    # 复制并重命名配置文件
    example_config_path = "ragflows/configs.demo.py"
    temp_config_path = "dist/configs.py"
    if os.path.exists(example_config_path):
        shutil.copy2(example_config_path, temp_config_path)
    
    # 构建 PyInstaller 命令
    pyinstaller_cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        # 直接添加需要的文件和目录
        "--add-data", f"ragflows{path_separator}ragflows",
        "--add-data", f"utils{path_separator}utils",
        "--add-data", f"__init__.py{path_separator}.",
        "--add-data", f"requirements.txt{path_separator}.",
        "--add-data", f"LICENSE{path_separator}.",
        "--add-data", f"README.md{path_separator}.",
        "--add-data", f"{temp_config_path}{path_separator}ragflows",
        # 添加必要的依赖
        "--hidden-import", "requests",
        "--hidden-import", "pytz",
        "--hidden-import", "pymysql",
        "--hidden-import", "customtkinter",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.scrolledtext",
        "--hidden-import", "logging",
        "--hidden-import", "importlib",
        "--hidden-import", "importlib.util",
        # 添加 PIL 相关依赖 - 兼容unbuntu的打包跟运行
        "--hidden-import", "PIL",
        "--hidden-import", "PIL._tkinter_finder",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "PIL.ImageTk",
        "--hidden-import", "PIL.ImageDraw",
        "--hidden-import", "PIL.ImageFont",
        # 输出的文件名
        "--name", OUTPUT_NAME,
    ]
    
    # 添加图标（如果存在）
    if os.path.exists(icon_path):
        pyinstaller_cmd.extend(["--add-data", f"{icon_path}{path_separator}."])
        pyinstaller_cmd.extend(["--icon", icon_path])
    
    # 添加启动脚本
    pyinstaller_cmd.append("scripts/launcher.py")
    
    # 执行打包命令
    subprocess.run(pyinstaller_cmd)
    
    # 清理临时文件
    _clean_file(temp_config_path, False)
    _clean_file(f'{OUTPUT_NAME}.spec', False)
    
    print("打包完成！")
    print("可执行文件已保存在: ", os.path.abspath(f'dist'), "目录下")

if __name__ == "__main__":
    build() 