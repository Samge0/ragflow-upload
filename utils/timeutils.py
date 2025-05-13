#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author：samge
# date：2024-07-24 10:38
# describe：
from datetime import datetime
import pytz
import time
import sys
import os

# 时区配置
TIME_ZONE = os.environ.get('TZ', 'Asia/Shanghai')

# 添加scripts目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(os.path.dirname(current_dir), 'scripts')
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

# 计算函数耗时
def monitor(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()  # 记录开始时间
        result = func(*args, **kwargs)  # 执行被装饰的函数
        end_time = time.time()  # 记录结束时间
        duration = end_time - start_time  # 计算耗时
        print_log(f"Function '{func.__name__}' took {duration:.2f} seconds to execute.")
        return result
    return wrapper


def get_now_str():
    """获取当前时间的字符串表示"""
    return datetime.now(pytz.timezone(TIME_ZONE)).strftime('%Y-%m-%d %H:%M:%S')


def print_log(*values: object):
    # 打印带当前年月日 时分秒 的日志
    message = f"{get_now_str()} {' '.join(str(v) for v in values)}"
    print(message)