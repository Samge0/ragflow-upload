import os
import shutil
import subprocess
import sys

def build_executable():
    """使用PyInstaller打包可执行文件"""
    try:
        # 确保dist目录存在
        if os.path.exists("dist"):
            shutil.rmtree("dist")
        
        # PyInstaller命令
        cmd = [
            "pyinstaller",
            "--name=ragflow-upload",
            "--windowed",  # 不显示控制台窗口
            "--add-data=ragflows;ragflows",  # 添加数据文件
            "--add-data=ragflows/configs.demo.py;ragflows",  # 确保配置文件模板被包含
            "--add-data=ragflows/main.py;ragflows",  # 确保main.py被包含
            "--add-data=utils;utils",  # 添加utils目录
            "--clean",  # 清理临时文件
            "--noconfirm",  # 不询问确认
            "--hidden-import=ragflows.main",  # 确保main模块被包含
            "--hidden-import=ragflows.api",  # 确保api模块被包含
            "--hidden-import=ragflows.configs",  # 确保configs模块被包含
            "--hidden-import=ragflows.ragflowdb",  # 确保ragflowdb模块被包含
            "--hidden-import=utils.timeutils",  # 确保timeutils模块被包含
            "main.py"  # 主程序入口
        ]
        
        # 执行打包命令
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("打包失败！错误信息：")
            print(result.stderr)
            sys.exit(1)
        else:
            print("打包成功！")
            print("可执行文件位于 dist/ragflow-upload/ragflow-upload.exe")
            
            # 复制配置文件到dist目录
            dist_config_dir = os.path.join("dist", "ragflow-upload", "configs")
            if not os.path.exists(dist_config_dir):
                os.makedirs(dist_config_dir)
            
            if os.path.exists("ragflows/configs.demo.py"):
                shutil.copy2("ragflows/configs.demo.py", os.path.join(dist_config_dir, "configs.demo.py"))
                print("已复制配置文件模板到dist目录")
            
    except Exception as e:
        print(f"打包过程中出现错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("开始打包过程...")
    build_executable() 