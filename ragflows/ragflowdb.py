#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author：samge
# date：2024-08-26 10:11
# describe：

from ragflows import configs
from utils.mysqlutils import BaseMySql
from utils import timeutils
import time


rag_db = None

def reset_connection():
    """重置数据库连接"""
    global rag_db
    if rag_db:
        try:
            rag_db.close_connect()
        except Exception as e:
            timeutils.print_log(f'reset_connection error: {e}')
    rag_db = None

def get_db():
    global rag_db
    if not rag_db:
        rag_db = BaseMySql(
            host=configs.MYSQL_HOST,
            user=configs.MYSQL_USER,
            password=configs.MYSQL_PASSWORD,
            database=configs.MYSQL_DATABASE,
            port=configs.MYSQL_PORT
        )
    return rag_db

@timeutils.monitor
def get_doc_list(kb_id):
    """
    根据知识库id获取文档列表
    
    :param kb_id: 知识库id
    :return: 文档列表
    """
    db = get_db()
    sql = f"select id,name,progress from document where kb_id = '{kb_id}'"
    doc_ids = db.query_list(sql)
    return doc_ids

def get_doc_item_by_id(doc_id, max_retries=0, retry_interval=1):
    """根据文档id获取文档信息，支持重试"""
    sql_str = f"select id,name,progress from document where id = '{doc_id}'"
    return _query_doc_item_with_try(
        sql_str=sql_str, 
        max_retries=max_retries, 
        retry_interval=retry_interval
    )

def get_doc_item_by_name(name, max_retries=0, retry_interval=1):
    """根据文档名称获取文档信息，支持重试"""
    kb_id = configs.DIFY_DOC_KB_ID
    
    if kb_id:
        sql_str = f"select id,name,progress from document where kb_id = '{kb_id}' and name = '{name}'"
    else:
        sql_str = f"select id,name,progress from document where name = '{name}'"
        
    return _query_doc_item_with_try(
        sql_str=sql_str, 
        max_retries=max_retries, 
        retry_interval=retry_interval
    )

def _query_doc_item_with_try(sql_str, max_retries=0, retry_interval=1):
    """
    根据文档名称获取文档信息，支持重试
    
    :param sql_str: 查询语句
    :param max_retries: 最大重试次数，0表示不重试
    :param retry_interval: 重试间隔（秒）
    
    :return: 文档信息 或 None
    """
    db = get_db()
    
    results = db.query_list(sql_str)
    
    # 如果有值或者 max_retries为<=0，直接返回查询结果
    if results or max_retries <= 0:
        return results[0] if results else None
        
    # 否则执行重试逻辑
    for attempt in range(1, max_retries + 1):
        where_str = sql_str.split('where ')[1] if 'where' in sql_str else ""
        timeutils.print_log(f"查询{where_str}无结果，第{attempt}次重试...")
        time.sleep(retry_interval)
        
        results = db.query_list(sql_str)
        if results:
            return results[0]
            
    return None

def exist(doc_id):
    """根据文档id判断文档是否存在"""
    return get_doc_item_by_id(doc_id) is not None

def exist_name(name):
    """根据文档名称判断文档是否存在"""
    return get_doc_item_by_name(name) is not None


if __name__ == '__main__':
    doc_list = get_doc_list(configs.DIFY_DOC_KB_ID) or []
    for item in doc_list:
        timeutils.print_log(item.get('id'), item.get('name'), item.get('progress'))
        
    doc_id = 'workspace-invite-and-manage-members-邀请与管理成员.md'
    timeutils.print_log('是否存在：', exist_name(doc_id))
        