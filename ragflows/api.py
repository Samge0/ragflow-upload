#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# RAGFlow API 封装 - 使用 v0.26.2+ 版本

from ragflows import configs, ragflow_sdk_v26
from utils import timeutils


def check_api_url() -> tuple[bool, str]:
    """检测API连接

    Returns:
        tuple[bool, str]: (是否可以访问, 提示文本)
    """
    return ragflow_sdk_v26.check_api_url()


@timeutils.monitor
def upload_file_to_dataset(file_path, dataset_name=None, dataset_id=None, chunk_method=None):
    """上传文件到指定知识库

    Args:
        file_path (str): 上传的文件路径
        dataset_name (str): 知识库名称
        dataset_id (str): 知识库ID
        chunk_method (str): 分块方法

    Returns:
        dict: 上传结果
    """
    # 使用配置中的默认值
    if not dataset_name:
        dataset_name = configs.DATASET_NAME
    if not dataset_id:
        dataset_id = configs.DATASET_ID
    if not chunk_method:
        chunk_method = configs.CHUNK_METHOD

    return ragflow_sdk_v26.upload_file_to_dataset(
        file_path=file_path,
        dataset_name=dataset_name,
        dataset_id=dataset_id,
        parser_id=chunk_method
    )


@timeutils.monitor
def get_dataset_documents(dataset_id=None, dataset_name=None):
    """获取指定知识库的文档列表

    Args:
        dataset_id (str): 知识库ID
        dataset_name (str): 知识库名称

    Returns:
        list: 文档列表
    """
    if not dataset_id:
        if dataset_name:
            dataset = ragflow_sdk_v26.ragflow_v26.get_dataset_by_name(dataset_name)
            if dataset:
                dataset_id = dataset.get('id')
        elif configs.DATASET_ID:
            dataset_id = configs.DATASET_ID
        elif configs.DATASET_NAME:
            dataset = ragflow_sdk_v26.ragflow_v26.get_dataset_by_name(configs.DATASET_NAME)
            if dataset:
                dataset_id = dataset.get('id')

    if not dataset_id:
        timeutils.print_log("无法获取知识库ID")
        return []

    return ragflow_sdk_v26.ragflow_v26.list_documents(dataset_id)


@timeutils.monitor
def parse_chunks(doc_ids, run=1):
    """解析文档

    Args:
        doc_ids (list): 文档 ID 列表
        run (int): 是否运行

    Returns:
        dict: 解析结果
    """
    # 获取知识库ID
    dataset_id = configs.DATASET_ID
    if not dataset_id:
        dataset = ragflow_sdk_v26.ragflow_v26.get_dataset_by_name(configs.DATASET_NAME)
        if dataset:
            dataset_id = dataset.get('id')

    if not dataset_id:
        return {"code": -1, "message": "无法获取知识库ID"}

    return ragflow_sdk_v26.ragflow_v26.parse_documents(dataset_id, doc_ids)


@timeutils.monitor
def parse_chunks_with_check(filename, doc_id=None):
    """解析文档，并等待解析完成

    Args:
        filename (str): 文件名
        doc_id (str): 文档ID

    Returns:
        bool: 是否解析成功
    """
    # 获取知识库ID
    dataset_id = configs.DATASET_ID
    if not dataset_id:
        dataset = ragflow_sdk_v26.ragflow_v26.get_dataset_by_name(configs.DATASET_NAME)
        if dataset:
            dataset_id = dataset.get('id')

    if not dataset_id:
        timeutils.print_log("无法获取知识库ID")
        return False

    # 开始解析
    response = parse_chunks(doc_ids=[doc_id])

    if response.get('code') != 0:
        timeutils.print_log(f"启动解析失败: {response}")
        return False

    # 等待解析完成
    return ragflow_sdk_v26.ragflow_v26.wait_for_parse_complete(
        dataset_id=dataset_id,
        document_id=doc_id,
        filename=filename
    )


def is_succeed(response):
    """判断请求是否成功

    Args:
        response: 响应数据

    Returns:
        bool: 是否成功
    """
    return response.get("code") == 0


@timeutils.monitor
def set_document_metadata(doc_id, filepath) -> bool:
    """设置文档元数据

    Args:
        doc_id (str): 文档ID
        filepath (str): 文件路径

    Returns:
        bool: 是否成功
    """
    # 获取知识库ID
    dataset_id = configs.DATASET_ID
    if not dataset_id:
        dataset = ragflow_sdk_v26.ragflow_v26.get_dataset_by_name(configs.DATASET_NAME)
        if dataset:
            dataset_id = dataset.get('id')

    if not dataset_id:
        timeutils.print_log("无法获取知识库ID")
        return False

    return ragflow_sdk_v26.set_document_metadata(doc_id, filepath)
