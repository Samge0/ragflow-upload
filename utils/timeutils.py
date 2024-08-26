#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author：samge
# date：2024-07-24 10:38
# describe：
from datetime import datetime
import pytz
import time

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
    # 获取上海时区时间
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    shanghai_time = datetime.now(shanghai_tz)
    return shanghai_time.strftime("%Y-%m-%d %H:%M:%S")


def print_log(*values: object):
    # 打印带当前年月日 时分秒 的日志
    print(get_now_str(), *values)