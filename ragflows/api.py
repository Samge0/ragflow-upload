#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author：samge
# date：2024-08-23 16:46
# describe：

import time
import requests
from ragflows import configs, ragflowdb
from utils import fileutils, timeutils


def check_api_url() -> tuple[bool, str]:
    """检测配置的 configs.API_URL 是否可以访问
    
    响应内容：
        样式1-成功：{"code":0,"data":"v0.17.2 full","message":"success"}
        样式2-认证失败/未授权：{"code":401,"data":null,"message":"<Unauthorized '401: Unauthorized'>"}
        样式3-API地址配置错误：{"code":100,"data":null,"message":"<NotFound '404: Not Found'>"}
        样式4-不存在的API地址

    Returns:
        bool: 是否可以访问
        str: 提示文本
    """
    url = f"{configs.API_URL}/system/version"
    try:
        r = requests.get(url, headers=configs.get_header())
    except Exception as e:
        return False, f"请求失败，请检查API相关配置后重试，请求异常：{e}"
    
    if r.status_code != 200:
        return False, f"请求失败，请检查API相关配置后重试，请求状态码：{r.status_code}"
    
    response = r.json()
    if is_succeed(response):
        return True, "API地址配置正确"
    
    code = response.get("code")
    message = response.get("message")
    
    if code == 401 or code == 403:
        return False, "认证失败/未授权，请检查 AUTHORIZATION 配置（授权Token）"
    elif code == 100 or '404' in message:
        return False, "API地址配置错误，请检查 API_URL 配置（API地址）"
    else:
        return False, "请求失败，请检查API相关配置后重试"

@timeutils.monitor
def upload_file_to_kb(file_path, kb_name, kb_id, parser_id=None, run=None):
    """上传文件到指定知识库

    Args:
        file_path (str): 上传的文件路径
        kb_name (str): 知识库名称
        parser_id (str, optional): 知识库文档解析方式. Defaults to None.
        run (str, optional): 是否可用状态. Defaults to None.

    Returns:
        dict: 上传结果
    """
    url = f"{configs.API_URL}/document/upload" 
    files = {'file': open(file_path, 'rb')}
    data = {
        'kb_name': kb_name,
        'kb_id': kb_id,
    }
    
    if parser_id:
        data['parser_id'] = parser_id
        
    if run:
        data['run'] = run
        
    response = requests.post(url, files=files, data=data, headers=configs.get_header())
    
    if response.status_code == 200:
        return response.json()
    else:
        return {
            "retcode": response.status_code,
            "retmsg": "Failed to upload file"
        }


@timeutils.monitor
def get_rag_list(kb_id):
    """获取指定知识库的文档列表

    Args:
        kb_id (str): 知识库id

    Returns:
        list: 文档列表
    """
    url = f"{configs.API_URL}/document/list?kb_id={kb_id}&page=1&page_size=1"  # 替换为实际的服务器地址
    response = requests.get(url, headers=configs.get_header())
    if response.status_code == 200:
        return response.json().get('data').get('docs')
    else:
        return []

@timeutils.monitor
def parse_chunks(doc_ids, run=1):
    """解析文档

    Args:
        doc_ids (str): 文档 ID 列表
        run (int, optional): 是否可用状态. Defaults to 1.

    Returns:
        dict: 解析文档后的结果
    """
    url = f"{configs.API_URL}/document/run"  # 替换为实际的服务器地址
    data = {"doc_ids":doc_ids,"run":run}
    response = requests.post(url, json=data, headers=configs.get_header())
    timeutils.print_log(response.text)
    if response.status_code == 200:
        return response.json()
    else:
        return {
            "retcode": response.status_code,
            "retmsg": "Failed to parse_chunks: {doc_ids}"
        }

@timeutils.monitor
def parse_chunks_with_check(filename):
    """解析文档，并仅当文档解析完毕后才返回

    Args:
        filename (str): 文件名，非文件路径

    Returns:
        bool: 是否已上传并解析完毕
    """
    doc_item = ragflowdb.get_doc_item_by_name(filename)
    if not doc_item:
        timeutils.print_log(f'找不到{filename}对应的数据库记录，跳过')
        return False
    
    doc_id = doc_item.get('id')
    r = parse_chunks(doc_ids=[doc_id], run=1)
    
    if not is_succeed(r):
        timeutils.print_log(F'失败 parse_chunks_with_check = {doc_item.get("id")}')
        return False
    
    while True:
        doc_item = ragflowdb.get_doc_item(doc_id)
        if not doc_item:
            return False
        
        progress = doc_item.get('progress')
        if progress < 0:
            msg = f"[{filename}]解析失败，跳过，progress={progress}"
            timeutils.print_log(msg)
            fileutils.save(f"{fileutils.get_cache_dir()}/ragflow_fail.txt", f"{timeutils.get_now_str()} {msg}\n")
            return False
        
        progress_percent = round(progress * 100, 2)
        timeutils.print_log(f"[{filename}]解析进度为：{progress_percent}%")
        if progress == 1:
            return True
        time.sleep(configs.PROGRESS_CHECK_INTERVAL)
    
    
# 是否请求成功
def is_succeed(response):
    # 20250208：增加对code字段的判断，因为新版ragflow返回字段名由retcode改为code了，保留retcode兼容旧版ragflow
    return response.get("retcode") == 0 or response.get("code") == 0
