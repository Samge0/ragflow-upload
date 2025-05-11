import customtkinter as ctk
import os
import sys
import importlib.util
from tkinter import scrolledtext
import threading
import traceback

# 设置主题
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ConfigGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 窗口设置
        self.title("RagFlow Upload")
        self.geometry("800x600")
        
        # 版本号
        self.version = "1.0.0"
        
        # 获取应用程序路径
        if getattr(sys, 'frozen', False):
            self.app_path = os.path.dirname(sys.executable)
        else:
            self.app_path = os.path.dirname(os.path.abspath(__file__))
        
        # 配置文件路径
        self.config_dir = os.path.join(self.app_path, "configs")
        self.config_path = os.path.join(self.config_dir, "configs.py")
        self.config_demo_path = os.path.join(self.config_dir, "configs.demo.py")
        
        # 添加项目根目录到Python路径
        if self.app_path not in sys.path:
            sys.path.insert(0, self.app_path)
        
        # 配置项定义
        self.config_definitions = {
            "API_URL": {"type": str, "label": "API地址", "default": "http://localhost:80/v1"},
            "AUTHORIZATION": {"type": str, "label": "授权Token", "default": "your authorization"},
            "DIFY_DOC_KB_ID": {"type": str, "label": "知识库ID", "default": "your kb_id"},
            "KB_NAME": {"type": str, "label": "知识库名称", "default": "your kb_name"},
            "PARSER_ID": {"type": str, "label": "解析方式", "default": "naive"},
            "DOC_DIR": {"type": str, "label": "文档目录", "default": ""},
            "DOC_SUFFIX": {"type": str, "label": "文档后缀", "default": "md,txt,pdf,docx"},
            "MYSQL_HOST": {"type": str, "label": "MySQL主机", "default": "localhost"},
            "MYSQL_PORT": {"type": int, "label": "MySQL端口", "default": "5455"},
            "MYSQL_USER": {"type": str, "label": "MySQL用户名", "default": "root"},
            "MYSQL_PASSWORD": {"type": str, "label": "MySQL密码", "default": "infini_rag_flow"},
            "MYSQL_DATABASE": {"type": str, "label": "MySQL数据库", "default": "rag_flow"},
            "DOC_MIN_LINES": {"type": int, "label": "最小行数", "default": "1"},
            "ONLY_UPLOAD": {"type": bool, "label": "仅上传文件", "default": "False"}
        }
        
        # 创建主框架
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建配置区域
        self.create_config_area()
        
        # 创建日志区域
        self.create_log_area()
        
        # 创建底部信息
        self.create_footer()
        
        # 加载配置
        self.load_config()

    def create_config_area(self):
        config_frame = ctk.CTkFrame(self.main_frame)
        config_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 配置项
        self.config_entries = {}
        
        # 创建滚动框架
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
            # 选择当前配置项应该放在哪一列
            current_frame = left_frame if i < items_per_column else right_frame
            
            frame = ctk.CTkFrame(current_frame)
            frame.pack(fill="x", padx=5, pady=2)
            
            # 创建标签和输入框的容器
            label_frame = ctk.CTkFrame(frame)
            label_frame.pack(side="left", fill="x", expand=True, padx=5)
            
            # 标签
            ctk.CTkLabel(label_frame, text=config["label"], width=100).pack(side="left", padx=5)
            
            if config["type"] == bool:
                # 使用复选框
                entry = ctk.CTkCheckBox(label_frame, text="")
                entry.pack(side="left", padx=5)
                if config["default"].lower() == "true":
                    entry.select()
            else:
                # 使用文本框
                entry = ctk.CTkEntry(label_frame)
                entry.pack(side="left", fill="x", expand=True, padx=5)
                entry.insert(0, config["default"])
            
            self.config_entries[key] = entry
        
        # 按钮框架
        button_frame = ctk.CTkFrame(config_frame)
        button_frame.pack(fill="x", padx=5, pady=5)
        
        # 保存按钮
        save_btn = ctk.CTkButton(button_frame, text="保存配置", command=self.save_config)
        save_btn.pack(side="left", padx=5, pady=5)
        
        # 运行按钮
        run_btn = ctk.CTkButton(button_frame, text="运行", command=self.run_upload)
        run_btn.pack(side="left", padx=5, pady=5)

    def create_log_area(self):
        log_frame = ctk.CTkFrame(self.main_frame)
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text.configure(state="disabled")

    def create_footer(self):
        footer_frame = ctk.CTkFrame(self.main_frame)
        footer_frame.pack(fill="x", padx=5, pady=5)
        
        # GitHub链接
        github_link = ctk.CTkLabel(
            footer_frame,
            text="GitHub",
            text_color="blue",
            cursor="hand2"
        )
        github_link.pack(side="left", padx=5)
        github_link.bind("<Button-1>", lambda e: self.open_github())
        
        # 版本号
        version_label = ctk.CTkLabel(
            footer_frame,
            text=f"版本: {self.version}"
        )
        version_label.pack(side="right", padx=5)

    def load_config(self):
        try:
            # 确保配置文件存在
            if not os.path.exists(self.config_path):
                if os.path.exists(self.config_demo_path):
                    os.makedirs(self.config_dir, exist_ok=True)
                    with open(self.config_demo_path, 'r', encoding='utf-8') as src:
                        with open(self.config_path, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())
                    self.log(f"已从模板创建配置文件: {self.config_path}")
                else:
                    self.log("警告: 配置文件模板不存在，将使用默认配置")
                    return

            # 尝试加载配置文件
            try:
                spec = importlib.util.spec_from_file_location("configs", self.config_path)
                configs = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(configs)
                
                for key, entry in self.config_entries.items():
                    if hasattr(configs, key):
                        value = getattr(configs, key)
                        config_type = self.config_definitions[key]["type"]
                        
                        if isinstance(entry, ctk.CTkCheckBox):
                            if config_type == bool:
                                entry.select() if value else entry.deselect()
                        else:
                            entry.delete(0, "end")
                            entry.insert(0, str(value))
                self.log("配置加载成功")
            except Exception as e:
                self.log(f"加载配置文件失败: {str(e)}")
                self.log("将使用默认配置")
        except Exception as e:
            self.log(f"初始化配置失败: {str(e)}")

    def save_config(self):
        try:
            # 确保目录存在
            os.makedirs(self.config_dir, exist_ok=True)
            
            config_content = "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\n"
            for key, entry in self.config_entries.items():
                config_type = self.config_definitions[key]["type"]
                
                if isinstance(entry, ctk.CTkCheckBox):
                    value = str(entry.get())
                else:
                    value = entry.get()
                    # 根据类型转换值
                    if config_type == int:
                        value = str(int(value))
                    elif config_type == bool:
                        value = str(bool(value.lower() == "true"))
                
                # 根据类型决定是否加引号
                if config_type == str:
                    config_content += f"{key} = '{value}'\n"
                else:
                    config_content += f"{key} = {value}\n"
            
            # 添加get_header函数
            config_content += "\n\ndef get_header():\n    return {'authorization': AUTHORIZATION}\n"
            
            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write(config_content)
            
            self.log(f"配置已保存到: {self.config_path}")
        except Exception as e:
            self.log(f"保存配置失败: {str(e)}")
            self.log("详细错误信息:")
            self.log(traceback.format_exc())

    def run_upload(self):
        def run():
            try:
                self.log("开始运行上传任务...")
                
                # 保存当前配置
                self.save_config()
                
                # 重新加载配置
                self.load_config()
                
                # 导入上传模块
                try:
                    # 尝试直接导入
                    from ragflows.main import main as upload_main
                    from utils import timeutils
                    
                    # 重新加载configs模块
                    import importlib
                    import ragflows.configs
                    importlib.reload(ragflows.configs)
                    
                except ImportError as e:
                    self.log(f"直接导入失败: {str(e)}")
                    self.log("尝试从_internal目录导入...")
                    
                    try:
                        # 尝试从_internal目录导入
                        if getattr(sys, 'frozen', False):
                            internal_path = os.path.join(self.app_path, "_internal")
                            if internal_path not in sys.path:
                                sys.path.insert(0, internal_path)
                            from ragflows.main import main as upload_main
                            from utils import timeutils
                        else:
                            raise ImportError("非打包环境，无法从_internal目录导入")
                    except ImportError as e:
                        self.log(f"从_internal目录导入失败: {str(e)}")
                        self.log("尝试使用importlib导入...")
                        
                        try:
                            # 尝试使用importlib导入
                            if getattr(sys, 'frozen', False):
                                main_path = os.path.join(self.app_path, "_internal", "ragflows", "main.py")
                                utils_path = os.path.join(self.app_path, "_internal", "utils")
                            else:
                                main_path = os.path.join(self.app_path, "ragflows", "main.py")
                                utils_path = os.path.join(self.app_path, "utils")
                            
                            if utils_path not in sys.path:
                                sys.path.insert(0, utils_path)
                            
                            spec = importlib.util.spec_from_file_location("main", main_path)
                            main_module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(main_module)
                            upload_main = main_module.main
                            
                            from utils import timeutils
                        except Exception as e:
                            self.log(f"使用importlib导入失败: {str(e)}")
                            self.log("请确保ragflows目录存在且包含main.py文件")
                            return
                
                # 执行上传任务
                try:
                    # 重定向timeutils.print_log的输出到GUI
                    original_print_log = timeutils.print_log
                    
                    def new_print_log(*args, **kwargs):
                        message = " ".join(str(arg) for arg in args)
                        self.log(message)
                        # 同时保留原始输出
                        original_print_log(*args, **kwargs)
                    
                    # 替换print_log函数
                    timeutils.print_log = new_print_log
                    
                    # 执行上传任务
                    upload_main()
                    
                    # 恢复原始print_log函数
                    timeutils.print_log = original_print_log
                    
                    self.log("上传任务完成")
                except Exception as e:
                    self.log(f"上传任务执行失败: {str(e)}")
                    self.log("详细错误信息:")
                    self.log(traceback.format_exc())
                
            except Exception as e:
                self.log(f"运行失败: {str(e)}")
                self.log("详细错误信息:")
                self.log(traceback.format_exc())
        
        # 在新线程中运行上传任务
        threading.Thread(target=run, daemon=True).start()

    def log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def open_github(self):
        import webbrowser
        webbrowser.open("https://github.com/Samge0/ragflow-upload")


if __name__ == "__main__":
    app = ConfigGUI()
    app.mainloop() 