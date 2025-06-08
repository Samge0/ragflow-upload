#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author：samge
# date：2024-08-26 10:11
# describe：

from ragflows import configs
from utils.mysqlutils import BaseMySql
from utils import timeutils


rag_db = None

def reset_connection():
    """重置数据库连接"""
    global rag_db
    if rag_db:
        try:
            rag_db.close_connect()
        except:
            pass
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
    db = get_db()
    sql = f"select id,name,progress from document where kb_id = '{kb_id}'"
    doc_ids = db.query_list(sql)
    return doc_ids

# @timeutils.monitor
def get_doc_item(doc_id):
    db = get_db()
    sql = f"select id,name,progress from document where id = '{doc_id}'"
    results = db.query_list(sql)
    return results[0] if results else None

# @timeutils.monitor
def get_doc_item_by_name(name):
    db = get_db()
    kb_id = configs.DIFY_DOC_KB_ID
    if kb_id:
        # 这里同时查询kb_id和name，如果document表中的数据量很大，需要增加kb_id和name的组合索引：CREATE INDEX document_kb_id_name ON document(kb_id, name);
        sql = f"select id,name,progress from document where kb_id = '{kb_id}' and name = '{name}'"
    else:
        sql = f"select id,name,progress from document where name = '{name}'"
    results = db.query_list(sql)
    return results[0] if results else None

def exist(doc_id):
    return get_doc_item(doc_id) is not None

def exist_name(name):
    return get_doc_item_by_name(name) is not None


if __name__ == '__main__':
    doc_list = get_doc_list(configs.DIFY_DOC_KB_ID) or []
    for item in doc_list:
        timeutils.print_log(item.get('id'), item.get('name'), item.get('progress'))
        
    doc_id = 'workspace-invite-and-manage-members-邀请与管理成员.md'
    timeutils.print_log('是否存在：', exist_name(doc_id))
        