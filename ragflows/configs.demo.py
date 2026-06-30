#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# RAGFlow 配置示例文件
# 使用方法：复制此文件为 configs.py 并修改相应配置

# RAGFlow API 配置
API_URL = 'http://localhost:80/api/v1'  # RAGFlow API 地址
API_KEY = 'ragflow-xxxxxx'  # API 密钥，从 http://localhost:80/user-setting/api 创建
DATASET_ID = ''  # 知识库ID（可选，留空则通过名称查找）
DATASET_NAME = 'my_dataset'  # 知识库名称

# 文档处理配置
CHUNK_METHOD = 'naive'  # 分块方法：naive, general, paper, book, laws, presentation, manual, qa
DOC_DIR = ''  # 文档目录
DOC_SUFFIX = 'md,txt,pdf,docx'  # 支持的文件后缀
DOC_MIN_LINES = 6  # 最小文件行数（低于此行数将被跳过）

# 解析配置
ONLY_UPLOAD = False  # 仅上传不解析
PROGRESS_CHECK_INTERVAL = 5  # 解析进度检查间隔（秒）
ENABLE_PROGRESS_LOG = True  # 启用解析进度日志
FIRST_PARSE_WAIT_TIME = 0  # 首次上传后解析等待时间（秒）

# 元数据配置
METADATA_SUFFIX = '.meta.json'  # 元数据文件后缀


def get_header():
    """获取API请求头"""
    return {'authorization': f'Bearer {API_KEY}'}
