import os
import shutil
import subprocess

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
    
    # 复制并重命名配置文件
    example_config_path = "ragflows/configs.demo.py"
    temp_config_path = "dist/configs.py"
    if os.path.exists(example_config_path):
        shutil.copy2(example_config_path, temp_config_path)
        
    # 输出名称
    OUTPUT_NAME = "RagFlowUpload"
    
    # 使用PyInstaller打包启动器
    subprocess.run([
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        # 直接添加需要的文件和目录
        "--add-data", "ragflows;ragflows",
        "--add-data", "utils;utils",
        "--add-data", "__init__.py;.",
        "--add-data", "requirements.txt;.",
        "--add-data", "LICENSE;.",
        "--add-data", "README.md;.",
        "--add-data", f"{temp_config_path};ragflows",
        "--add-data", "scripts/icon.ico;.",  # 将图标文件添加到根目录
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
        # 输出的文件名
        "--name", OUTPUT_NAME,
        "--icon", "scripts/icon.ico",
        "scripts/launcher.py"
    ])
    
    # 清理临时文件
    _clean_file(temp_config_path, False)
    _clean_file(f'{OUTPUT_NAME}.spec', False)
    
    print("打包完成！")
    print(f"可执行文件位置: {os.path.abspath(f'dist/{OUTPUT_NAME}.exe')}")

if __name__ == "__main__":
    build() 