import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys
from datetime import datetime
import pytz

# 时区配置
TIME_ZONE = os.environ.get('TZ', 'Asia/Shanghai')

# 设置日志格式
class CustomTimeZoneFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        _tz = pytz.timezone(TIME_ZONE)
        dt = datetime.fromtimestamp(record.created).astimezone(_tz)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]

# 日志处理器
class LogHandler:
    def __init__(self):
        self.logger = logging.getLogger('RagFlowUpload')
        self.logger.setLevel(logging.INFO)
        
        # 创建logs目录
        self.logs_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'logs')
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # 设置日志文件名格式
        _tz = pytz.timezone(TIME_ZONE)
        current_date = datetime.now(_tz).strftime('%Y-%m-%d')
        log_file = os.path.join(self.logs_dir, f'ragflow_upload_{current_date}.log')
        
        # 创建按天切割的日志处理器
        file_handler = TimedRotatingFileHandler(
            filename=log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # 保留30天的日志
            encoding='utf-8'
        )
        
        formatter = CustomTimeZoneFormatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # 添加处理器到logger
        self.logger.addHandler(file_handler)
    
    def log(self, message):
        self.logger.info(message) 