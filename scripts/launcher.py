from datetime import datetime
import os
import sys
import customtkinter as ctk
from tkinter import scrolledtext
import importlib.util
from pathlib import Path
import shutil
import threading
import traceback
import pytz
from PIL import ImageTk
from logs import LogHandler

# 创建日志处理器实例 - 用于保存日志
log_save_handler = LogHandler()

# 时区配置
TIME_ZONE = os.environ.get('TZ', 'Asia/Shanghai')

def get_now_str():
    """获取当前时间的字符串表示"""
    return datetime.now(pytz.timezone(TIME_ZONE)).strftime('%Y-%m-%d %H:%M:%S')

def get_config_dir():
    """获取配置文件目录（存于用户目录下）"""
    home_dir = str(Path.home())
    config_dir = os.path.join(home_dir, '.ragflow_upload')
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def get_config_path():
    """获取配置文件路径（存于用户目录下）"""
    return os.path.join(get_config_dir(), "configs.py")


def is_pyinstaller_environment():
    """判断当前环境是否为PyInstaller环境"""
    try:
        return hasattr(sys, '_MEIPASS')
    except Exception:
        return False

def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    # 如果是PyInstaller环境则返回临时文件夹（路径在_MEIPASS中），否则返回当前项目目录
    base_path = sys._MEIPASS if is_pyinstaller_environment() else os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def copy_user_config_to_package(log_func):
    """将用户配置复制到包内配置"""
    try:
        # 获取用户配置路径
        user_config_path = get_config_path()
        if not os.path.exists(user_config_path):
            return False
            
        # 获取包内配置路径
        package_config_path = get_resource_path(os.path.join("ragflows", "configs.py"))
        
        # 复制用户配置到包内配置
        shutil.copy2(user_config_path, package_config_path)
        log_func(f"复制用户配置到包内配置: {user_config_path} -> {package_config_path}")
        
        return True
    except Exception as e:
        log_func(f"复制用户配置失败: {str(e)}")
        return False

class ConfigGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.current_thread = None  # 添加线程跟踪变量
        self.title("RagFlow Upload")
        self.geometry("800x600")
        
        # 自定义图标
        icon_file = get_resource_path('icon.ico') if is_pyinstaller_environment() else 'scripts/icon.ico'
        self.iconpath = ImageTk.PhotoImage(file=icon_file)
        self.wm_iconbitmap()
        self.iconphoto(False, self.iconpath)
        
        # 配置项定义
        self.config_definitions = {
            "API_URL": {"type": str, "label": "API地址", "default": "http://localhost:80/v1"},
            "AUTHORIZATION": {"type": str, "label": "授权Token", "default": "your authorization"},
            "DIFY_DOC_KB_ID": {"type": str, "label": "知识库ID", "default": "your kb_id"},
            "KB_NAME": {"type": str, "label": "知识库名称", "default": "your kb_name"},
            "PARSER_ID": {"type": str, "label": "解析方式", "default": "naive"},
            "DOC_DIR": {"type": str, "label": "文档目录", "default": "your doc dir"},
            "DOC_SUFFIX": {"type": str, "label": "文档后缀", "default": "md,txt,pdf,docx"},
            "MYSQL_HOST": {"type": str, "label": "MySQL主机", "default": "localhost"},
            "MYSQL_PORT": {"type": int, "label": "MySQL端口", "default": "5455"},
            "MYSQL_USER": {"type": str, "label": "MySQL用户名", "default": "root"},
            "MYSQL_PASSWORD": {"type": str, "label": "MySQL密码", "default": "infini_rag_flow"},
            "MYSQL_DATABASE": {"type": str, "label": "MySQL数据库", "default": "rag_flow"},
            "DOC_MIN_LINES": {"type": int, "label": "最小行数", "default": "1"},
            "ONLY_UPLOAD": {"type": bool, "label": "仅上传文件", "default": "False"}
        }
        
        self.create_ui()
        self.load_config()

    def create_ui(self):
        # 主框架
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 配置区域
        config_frame = ctk.CTkFrame(self.main_frame)
        config_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 配置项
        self.config_entries = {}
        scroll_frame = ctk.CTkScrollableFrame(config_frame)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建两列布局
        left_frame = ctk.CTkFrame(scroll_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        right_frame = ctk.CTkFrame(scroll_frame)
        right_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # 计算每列应显示的配置项数量
        total_items = len(self.config_definitions)
        items_per_column = (total_items + 1) // 2
        
        # 将配置项分配到两列
        for i, (key, config) in enumerate(self.config_definitions.items()):
            current_frame = left_frame if i < items_per_column else right_frame
            frame = ctk.CTkFrame(current_frame)
            frame.pack(fill="x", padx=5, pady=2)
            
            label_frame = ctk.CTkFrame(frame)
            label_frame.pack(side="left", fill="x", expand=True, padx=5)
            
            ctk.CTkLabel(label_frame, text=config["label"], width=100).pack(side="left", padx=5)
            
            if config["type"] == bool:
                entry = ctk.CTkCheckBox(label_frame, text="")
                entry.pack(side="left", padx=5)
                if config["default"].lower() == "true":
                    entry.select()
            else:
                entry = ctk.CTkEntry(label_frame)
                entry.pack(side="left", fill="x", expand=True, padx=5)
                entry.insert(0, config["default"])
            
            self.config_entries[key] = entry
        
        # 按钮
        button_frame = ctk.CTkFrame(config_frame)
        button_frame.pack(fill="x", padx=5, pady=5)
        # ctk.CTkButton(button_frame, text="保存配置", command=self.save_config).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="运行", command=self.run_upload).pack(side="left", padx=5, pady=5)
        
        # 日志区域
        log_frame = ctk.CTkFrame(self.main_frame)
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text.configure(state="disabled")

    def log(self, message):
        # 输出到GUI
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{get_now_str()} {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        # 保存到日志文件
        log_save_handler.log(message)

    def load_config(self):
        try:
            config_path = get_config_path()
            self.log(f"加载配置: {config_path}")
            
            # 如果配置文件不存在，从示例配置复制
            if not os.path.exists(config_path):
                demo_config = get_resource_path(os.path.join("ragflows", "configs.demo.py"))
                if os.path.exists(demo_config):
                    shutil.copy2(demo_config, config_path)
                    self.log(f"已从示例配置创建配置文件: {config_path}")
            
            # 存在配置，读取配置展示到GUI界面
            if os.path.exists(config_path):
                spec = importlib.util.spec_from_file_location("configs", config_path)
                configs = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(configs)
                
                for key, entry in self.config_entries.items():
                    if hasattr(configs, key):
                        value = getattr(configs, key)
                        self.log(f"加载配置: {key} = {value}")
                        if isinstance(entry, ctk.CTkCheckBox):
                            entry.select() if value else entry.deselect()
                        else:
                            entry.delete(0, "end")
                            entry.insert(0, str(value))
        except Exception as e:
            self.log(f"加载配置失败: {str(e)}")

    def save_config(self):
        try:
            config_path = get_config_path()
            with open(config_path, "w", encoding="utf-8") as f:
                f.write("# 配置文件\n")
                for key, entry in self.config_entries.items():
                    if isinstance(entry, ctk.CTkCheckBox):
                        value = bool(entry.get())
                    else:
                        value = entry.get()
                        if self.config_definitions[key]["type"] == int:
                            value = int(value)
                    f.write(f"{key} = {repr(value)}\n")
                # 添加get_header函数
                f.write("\n\ndef get_header():\n    return {'authorization': AUTHORIZATION}\n")
            self.log("配置已保存")
        except Exception as e:
            self.log(f"保存配置失败: {str(e)}")

    def run_upload(self):
                
        def run():
            try:
                # 运行前保存一下配置
                self.save_config()
                
                self.log("开始运行上传程序...")
                
                # 在运行前，将用户配置复制到包内配置
                if copy_user_config_to_package(self.log):
                    self.log("已更新包内配置")
                    # 清理所有可能包含配置的模块缓存
                    for module_name in list(sys.modules.keys()):
                        if module_name.startswith('ragflows.') or module_name == 'configs':
                            del sys.modules[module_name]
                    
                    # 重新导入配置模块
                    config_path = get_resource_path(os.path.join("ragflows", "configs.py"))
                    spec = importlib.util.spec_from_file_location("ragflows.configs", config_path)
                    configs_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(configs_module)
                    sys.modules["ragflows.configs"] = configs_module
                    
                    # 重新导入api模块
                    api_path = get_resource_path(os.path.join("ragflows", "api.py"))
                    spec = importlib.util.spec_from_file_location("ragflows.api", api_path)
                    api_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(api_module)
                    sys.modules["ragflows.api"] = api_module
                    
                    # 重置数据库连接
                    try:
                        from ragflows.ragflowdb import reset_connection
                        reset_connection()
                        self.log("数据库连接已重置")
                    except Exception as e:
                        self.log(f"数据库连接失败: {str(e)}，请检查数据库配置后重试")
                        return  # 中断执行
                
                # 动态导入主程序
                main_path = get_resource_path(os.path.join("ragflows", "main.py"))
                spec = importlib.util.spec_from_file_location("main", main_path)
                main_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(main_module)
                
                # 重定向日志输出
                original_print_log = None
                try:
                    from utils import timeutils
                    original_print_log = timeutils.print_log
                    
                    def new_print_log(*args, **kwargs):
                        message = " ".join(str(arg) for arg in args)
                        self.log(message)
                        if original_print_log:
                            original_print_log(*args, **kwargs)
                    
                    timeutils.print_log = new_print_log
                except ImportError:
                    self.log("未找到timeutils模块，将使用默认日志输出")
                
                # 运行主程序
                main_module.main()
                
                # 恢复原始日志输出
                if original_print_log:
                    timeutils.print_log = original_print_log
                
                self.log("程序运行完成")
            except Exception as e:
                self.log(f"运行失败: {str(e)}")
                self.log("详细错误信息:")
                self.log(traceback.format_exc())
        
        # 在新线程中运行上传任务
        self.current_thread = threading.Thread(target=run, daemon=True)
        self.current_thread.start()

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = ConfigGUI()
    app.mainloop()
