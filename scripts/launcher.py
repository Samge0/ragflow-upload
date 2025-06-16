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
import webbrowser
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
        self.is_running = False  # 添加运行状态标志
        self.should_stop = False  # 添加停止标志
        self.is_stopping = False  # 添加正在停止标志
        self.log_handlers = []  # 添加日志处理器列表
        self.original_print_log = None  # 保存原始的日志打印函数
        self.title("RagFlow Upload")
        self.geometry("800x750")
        
        # 版本和仓库信息
        self.version = "v1.0.4"  # 版本号
        self.github_repo = "https://github.com/Samge0/ragflow-upload"  # GitHub仓库地址
        
        # 自定义图标
        icon_file = get_resource_path('icon.png') if is_pyinstaller_environment() else 'scripts/icon.png'
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
            "PROGRESS_CHECK_INTERVAL": {"type": int, "label": "切片进度查询间隔", "default": "1"},
            "SQL_RETRIES": {"type": int, "label": "SQL查询重试次数", "default": "1"},
            "FIRST_PARSE_WAIT_TIME": {"type": int, "label": "首次解析等待时间", "default": "0"},
            
            "MYSQL_HOST": {"type": str, "label": "MySQL主机", "default": "localhost"},
            "MYSQL_PORT": {"type": int, "label": "MySQL端口", "default": "5455"},
            "MYSQL_USER": {"type": str, "label": "MySQL用户名", "default": "root"},
            "MYSQL_PASSWORD": {"type": str, "label": "MySQL密码", "default": "infini_rag_flow"},
            "MYSQL_DATABASE": {"type": str, "label": "MySQL数据库", "default": "rag_flow"},
            "DOC_MIN_LINES": {"type": int, "label": "最小行数", "default": "1"},
            "ONLY_UPLOAD": {"type": bool, "label": "仅上传文件", "default": "False"},
            "ENABLE_PROGRESS_LOG": {"type": bool, "label": "打印切片进度日志", "default": "True"},
            "UI_START_INDEX": {"type": int, "label": "起始文件序号", "default": "1"},  # 从1开始计数，更符合非编程用户习惯
        }
        
        self.create_ui()
        self.load_config()
        self.load_index_from_cache()  # 加载缓存中的序号

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
        self.run_button = ctk.CTkButton(
            button_frame,
            text="运行",
            command=self.toggle_run,
            fg_color=["#3B8ED0", "#1F6AA5"],  # 默认蓝色
            hover_color=["#36719F", "#144870"],  # 深蓝色
            text_color="white"  # 白色文字
        )
        self.run_button.pack(side="left", padx=5, pady=5)
        
        # 添加清理日志按钮
        self.clear_log_button = ctk.CTkButton(
            button_frame,
            text="清理日志",
            command=self.clear_log,
            fg_color=["#757575", "#616161"],  # 灰色
            hover_color=["#616161", "#424242"],  # 深灰色
            text_color="white"  # 白色文字
        )
        self.clear_log_button.pack(side="left", padx=5, pady=5)
        
        # 日志区域
        log_frame = ctk.CTkFrame(self.main_frame)
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text.configure(state="disabled")
        
        # 添加版本和仓库信息
        info_frame = ctk.CTkFrame(self.main_frame)
        info_frame.pack(fill="x", padx=5, pady=2)
            
        version_label = ctk.CTkLabel(info_frame, text=f"版本: {self.version}  |")
        version_label.pack(side="left", padx=5)
        
        # 使用更显眼的样式显示 GitHub 链接
        repo_label = ctk.CTkLabel(
            info_frame, 
            text=self.github_repo, 
            cursor="hand2",
            text_color="#1E90FF",  # 使用蓝色
            font=("Arial", 12)
        )
        repo_label.pack(side="left", padx=5)
        repo_label.bind("<Button-1>", lambda e: self.open_github())
        
        # 添加分隔符
        separator = ctk.CTkLabel(info_frame, text="| 配置目录:")
        separator.pack(side="left", padx=5)
        
        # 添加打开配置目录的链接
        config_label = ctk.CTkLabel(
            info_frame,
            text=get_config_dir(),
            cursor="hand2",
            text_color="#1E90FF",
            font=("Arial", 11)
        )
        config_label.pack(side="left", padx=5)
        config_label.bind("<Button-1>", lambda e: self.open_config_dir())

    def toggle_run(self):
        """切换运行/停止状态"""
        if not self.is_running:
            if self.current_thread and self.current_thread.is_alive():
                self.log("上一个任务还在运行中，请等待完成或点击停止")
                return
        
            # 运行前时将滚动条设置到底部
            self.log_text.see("end")
            
            self.start_run()
        else:
            if not self.is_stopping:  # 防止重复点击
                self.stop_run()

    def start_run(self):
        """开始运行"""
        # 保存当前序号到缓存
        self.save_index_to_cache()
        
        self.is_running = True
        self.run_button.configure(
            text="停止",
            fg_color="#FF5555",  # 红色
            hover_color="#FF3333",  # 深红色
            text_color="white"  # 白色文字
        )
        self.set_config_entries_state("disabled")
        self.run_upload()

    def stop_run(self):
        """停止运行"""
        if self.current_thread and self.current_thread.is_alive():
            self.is_stopping = True  # 设置正在停止标志
            self.is_running = False
            self.should_stop = True  # 设置停止标志
            self.log("正在停止运行...")
            
            # 禁用停止按钮，防止重复点击
            self.run_button.configure(state="disabled")
            
            # 尝试终止线程
            try:
                import ctypes
                thread_id = self.current_thread.ident
                if thread_id:
                    exc = ctypes.py_object(KeyboardInterrupt)
                    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), exc)
            except Exception as e:
                self.log(f"停止线程时出错: {str(e)}")
            
            # 等待线程真正结束
            def wait_thread_end():
                if self.current_thread:
                    self.current_thread.join()
                # 线程结束后更新UI状态
                self.current_thread = None
                self.is_stopping = False
                self.run_button.configure(
                    text="运行",
                    fg_color=["#3B8ED0", "#1F6AA5"],  # 默认蓝色
                    hover_color=["#36719F", "#144870"],  # 深蓝色
                    text_color="white",  # 白色文字
                    state="normal"  # 恢复按钮状态
                )
                self.set_config_entries_state("normal")
                # 重新加载缓存中的序号
                self.load_index_from_cache()
                self.log("已停止运行")
                # 清理日志处理器
                self.cleanup_log_handlers()
            
            # 在新线程中等待原线程结束
            threading.Thread(target=wait_thread_end, daemon=True).start()

    def set_config_entries_state(self, state):
        """设置配置项的启用/禁用状态"""
        for entry in self.config_entries.values():
            if isinstance(entry, ctk.CTkCheckBox):
                entry.configure(state=state)
            else:
                entry.configure(state=state)

    def setup_log_handler(self):
        """设置日志处理器"""
        try:
            from utils import timeutils
            if self.original_print_log is None:
                self.original_print_log = timeutils.print_log
            
            def new_print_log(*args, **kwargs):
                if self.should_stop:  # 检查是否应该停止
                    raise KeyboardInterrupt("用户请求停止")
                message = " ".join(str(arg) for arg in args)
                self.log(message)
                if self.original_print_log:
                    self.original_print_log(*args, **kwargs)
            
            timeutils.print_log = new_print_log
            return True
        except ImportError:
            self.log("未找到timeutils模块，将使用默认日志输出")
            return False

    def restore_log_handler(self):
        """恢复原始日志处理器"""
        try:
            from utils import timeutils
            if self.original_print_log:
                timeutils.print_log = self.original_print_log
                self.original_print_log = None
        except ImportError:
            pass

    def cleanup_log_handlers(self):
        """清理所有日志处理器"""
        self.restore_log_handler()
        self.log_handlers.clear()

    def run_upload(self):
        def run():
            try:
                # 重置停止标志
                self.should_stop = False
                
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
                        self.should_stop = True  # 设置停止标志
                        return  # 中断执行
                
                # 动态导入主程序
                main_path = get_resource_path(os.path.join("ragflows", "main.py"))
                spec = importlib.util.spec_from_file_location("main", main_path)
                main_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(main_module)
                
                # 设置日志处理器
                if not self.setup_log_handler():
                    self.log("警告：无法设置日志处理器，日志可能不完整")
                
                # 运行主程序
                if not self.should_stop:  # 检查是否应该停止
                    try:
                        # 添加停止检查函数到main模块
                        def check_stop():
                            if self.should_stop:
                                raise KeyboardInterrupt("用户请求停止")
                            return False
                        
                        # 将停止检查函数添加到main模块
                        main_module.check_stop = check_stop
                        
                        # 重置is_first_upload变量
                        main_module.is_first_upload = True
                        
                        # 运行主程序
                        main_module.main()
                    except KeyboardInterrupt:
                        self.log("程序已被用户停止")
                        return  # 直接返回，不抛出异常
                
                if not self.should_stop:  # 只有在非停止状态下才显示完成消息
                    self.log("程序运行完成")
            except Exception as e:
                self.log(f"运行失败: {str(e)}")
                self.log("详细错误信息:")
                self.log(traceback.format_exc())
            finally:
                # 确保在任何情况下都清理日志处理器
                self.cleanup_log_handlers()
                # 确保在任何情况下都更新停止状态
                if self.is_running:  # 如果还在运行状态，说明是异常导致的停止
                    self.is_running = False
                    self.should_stop = True
                    # 更新UI状态
                    self.current_thread = None
                    self.is_stopping = False
                    self.run_button.configure(
                        text="运行",
                        fg_color=["#3B8ED0", "#1F6AA5"],  # 默认蓝色
                        hover_color=["#36719F", "#144870"],  # 深蓝色
                        text_color="white",  # 白色文字
                        state="normal"  # 恢复按钮状态
                    )
                    self.set_config_entries_state("normal")
                    # 重新加载缓存中的序号
                    self.load_index_from_cache()
                    self.log("已停止运行")
        
        # 在新线程中运行上传任务
        self.current_thread = threading.Thread(target=run, daemon=True)
        self.current_thread.start()

    # 创建可点击的链接标签
    def open_github(self):
        webbrowser.open(self.github_repo)
        
    def open_config_dir(self):
        import subprocess
        config_dir = get_config_dir()
        if os.name == 'nt':  # Windows
            os.startfile(config_dir)
        elif sys.platform == 'darwin':  # macOS
            subprocess.run(['open', config_dir])
        else:  # Linux
            subprocess.run(['xdg-open', config_dir])

    def is_scrollbar_at_bottom(self):
        """检查滚动条是否在底部"""
        current_position = self.log_text.yview()[1]
        # 添加一个小的容差值（0.9）来判断是否在底部
        is_at_bottom = current_position >= 0.9
        return is_at_bottom

    def log(self, message):
        # 输出到GUI
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{get_now_str()} {message}\n")
        
        # 只有当滚动条在底部时才自动滚动
        if self.is_scrollbar_at_bottom():
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
                f.write("# 配置文件（注意：若是手动修改该配置文件，需要重新运行程序才能生效）\n")
                for key, entry in self.config_entries.items():
                    if key.startswith("UI_"):   # UI_前缀的配置项表示仅用于ui界面，不不需要保存到configs.py配置文件
                        continue
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

    def clear_log(self):
        """清理UI界面的日志显示"""
        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.configure(state="disabled")
        self.log("日志已清理")

    def get_index_cache_path(self):
        """获取序号缓存文件路径"""
        kb_id = self.config_entries["DIFY_DOC_KB_ID"].get()
        kb_name = self.config_entries["KB_NAME"].get()
        return os.path.join(get_config_dir(), f"index_{kb_id}_{kb_name}.txt")

    def load_index_from_cache(self):
        """从缓存文件加载序号"""
        try:
            index_path = self.get_index_cache_path()
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    index = f.read().strip()
                    if index:
                        self.config_entries["UI_START_INDEX"].delete(0, "end")
                        self.config_entries["UI_START_INDEX"].insert(0, str(index))
                        self.log(f"从 {index_path} 文件中读取文件序号: {index}")
        except Exception as e:
            self.log(f"加载序号缓存失败: {str(e)}")

    def save_index_to_cache(self):
        """保存序号到缓存文件"""
        try:
            index = self.config_entries["UI_START_INDEX"].get()
            if index:
                index = int(index)
                index_path = self.get_index_cache_path()
                os.makedirs(os.path.dirname(index_path), exist_ok=True)
                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write(str(index))
                self.log(f"保存文件序号（{index}）到: {index_path}")
        except Exception as e:
            self.log(f"保存序号缓存失败: {str(e)}")

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = ConfigGUI()
    app.mainloop()
