#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# RAGFlow 文档批量上传工具 - 使用 v0.26.2+ API

import glob
import os
from ragflows import api, configs
from utils import timeutils
from utils.statestore import StateStore


def get_docs_files() -> list:
    """
    获取指定目录及其子目录中的所有文件。

    Returns:
        list: 文件路径列表

    Raises:
        ValueError: 如果指定目录不存在
    """
    if not os.path.exists(configs.DOC_DIR):
        raise ValueError(f"文档目录configs.DOC_DIR（{configs.DOC_DIR}）不存在")

    all_files = []

    for ext in configs.DOC_SUFFIX.split(','):
        # 使用递归通配符 ** 搜索子目录中的文件
        files = glob.glob(f'{configs.DOC_DIR}/**/*.{ext.strip()}', recursive=True)
        all_files.extend(files)

    return all_files


def need_calculate_lines(filepath) -> bool:
    """
    判断是否需要计算文件行数

    Args:
        filepath (str): 文件路径

    Returns:
        bool: 是否需要计算行数
    """
    if not filepath:
        return False
    suffix_lst = "txt,md,html".split(",")
    return filepath.split(".")[-1].lower() in suffix_lst


def get_file_lines(file_path) -> int:
    """
    获取文件行数

    Args:
        file_path (str): 文件路径

    Returns:
        int: 文件行数
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except Exception as e:
        timeutils.print_log(f"打开文件 {file_path} 时出错，错误信息：{e}")
        return 0


def get_document_from_api(filename):
    """
    从 RAGFlow API 获取文档信息

    Args:
        filename (str): 文件名

    Returns:
        dict: 文档信息，如果不存在则返回 None
    """
    # 获取知识库ID
    dataset_id = configs.DATASET_ID
    if not dataset_id:
        dataset = api.ragflow_sdk_v26.ragflow_v26.get_dataset_by_name(configs.DATASET_NAME)
        if dataset:
            dataset_id = dataset.get('id')

    if not dataset_id:
        return None

    # 查找文档
    docs = api.ragflow_sdk_v26.ragflow_v26.list_documents(dataset_id, keywords=filename)
    for doc in docs:
        if doc.get('name') == filename:
            return doc

    return None


def main():
    """主函数，处理文档上传和解析"""

    # 运行前测试API连接
    status, msg = api.check_api_url()
    if not status:
        raise Exception(msg)

    # 使用 glob 模块获取所有文件
    doc_files = get_docs_files() or []

    file_total = len(doc_files)
    if file_total == 0:
        raise ValueError(f"在 {configs.DOC_DIR} 目录下没有找到符合要求文档文件")

    # 初始化状态机（基于知识库ID或名称）
    cache_key = configs.DATASET_ID or configs.DATASET_NAME
    state = StateStore(cache_key)

    # 标记是否是首次上传
    is_first_upload = True

    # 打印找到的所有文件
    for i in range(file_total):

        file_path = doc_files[i]

        # 如果配置了元数据后缀，且文件是元数据后缀，则跳过
        if configs.METADATA_SUFFIX and file_path.endswith(configs.METADATA_SUFFIX):
            continue

        file_path = file_path.replace(os.sep, '/')
        filename = os.path.basename(file_path)

        timeutils.print_log(f"【{i+1}/{file_total}】[{filename}] 正在处理")

        # 状态机检查：DONE 直接跳过
        if not state.should_process(file_path):
            timeutils.print_log(f"[{filename}] 状态为 {state.get(file_path)}，跳过")
            continue

        # 判断文件行数是否小于目标值
        if need_calculate_lines(file_path):
            file_lines = get_file_lines(file_path)
            if file_lines < configs.DOC_MIN_LINES:
                timeutils.print_log(f"[{filename}] 行数低于{configs.DOC_MIN_LINES}，跳过")
                continue

        # 检查文档在 RAGFlow API 中是否已存在（state.json 丢失时作为兜底）
        existing_doc = get_document_from_api(filename)

        if existing_doc:
            doc_id = existing_doc.get('id')
            doc_progress = existing_doc.get('progress', 0)
            doc_status = existing_doc.get('run', 'UNKNOWN')

            # 检查配置并更新元数据
            api.set_document_metadata(doc_id, file_path)

            if configs.ONLY_UPLOAD:
                timeutils.print_log(f"[{filename}] 已存在，仅上传模式，跳过")
                state.set(file_path, StateStore.UPLOADED)
            elif doc_progress == 1 or doc_status == 'DONE':
                timeutils.print_log(f"[{filename}] 已完成切片，跳过")
                state.set(file_path, StateStore.DONE)
            else:
                timeutils.print_log(f'[{filename}] 文件已存在，但未解析，开始切片并等待解析完毕')
                state.set(file_path, StateStore.PARSING)
                status = api.parse_chunks_with_check(filename, doc_id)
                timeutils.print_log(f"[{filename}] 切片状态：{status}")
                state.set(file_path, StateStore.DONE if status else StateStore.FAILED)
            continue

        # 文件不存在，上传文件
        response = api.upload_file_to_dataset(
            file_path=file_path,
            dataset_name=configs.DATASET_NAME,
            dataset_id=configs.DATASET_ID,
            chunk_method=configs.CHUNK_METHOD
        )
        timeutils.print_log(f"[{filename}] upload_file_to_dataset response: {response}")

        if api.is_succeed(response) is False:
            timeutils.print_log(f'[{filename}] 上传失败：{response.get("text")}')
            state.set(file_path, StateStore.FAILED)
            continue

        # 尝试从响应内容中解析doc_id
        data = response.get('data')
        doc_id = None
        if isinstance(data, list) and data and isinstance(data[0], dict):
            doc_id = data[0].get('id')
        elif isinstance(data, dict):
            doc_id = data.get('id')
        else:
            timeutils.print_log(f"[{filename}] 上传文件后返回数据不包含文档id: {data}")

        # 检查配置并更新元数据
        api.set_document_metadata(doc_id, file_path)

        # 仅上传，跳过切片解析
        if configs.ONLY_UPLOAD:
            state.set(file_path, StateStore.UPLOADED)
            continue

        # 如果是首次上传且设置了首次解析等待时间，则等待指定时间
        if is_first_upload and configs.FIRST_PARSE_WAIT_TIME > 0:
            timeutils.print_log(f'[{filename}] 首次上传成功，已配置【首次上传后解析等待时间】，等待 {configs.FIRST_PARSE_WAIT_TIME} 秒后再进行解析...')
            import time
            time.sleep(configs.FIRST_PARSE_WAIT_TIME)
            is_first_upload = False

        # 上传成功，开始切片
        timeutils.print_log(f'[{filename}] 开始切片并等待解析完毕')
        state.set(file_path, StateStore.PARSING)
        status = api.parse_chunks_with_check(filename, doc_id)
        timeutils.print_log(f"[{filename}] 切片状态：{status}")
        state.set(file_path, StateStore.DONE if status else StateStore.FAILED)

    timeutils.print_log('all done')


if __name__ == '__main__':
    main()
