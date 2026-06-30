#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author：samge
# date：2025-01-30
# describe：RAGFlow v0.26.2版本的API适配模块

import os
import requests
import time
from typing import Optional, Dict, List, Any
from ragflows import configs
from utils import timeutils


class RAGFlowSDKV26:
    """RAGFlow v0.26.2版本的API适配类"""

    def __init__(self):
        """初始化RAGFlow客户端"""
        self.api_url = configs.API_URL
        self.auth_token = configs.API_KEY
        self.headers = configs.get_header()

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """发送HTTP请求

        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE)
            endpoint: API端点
            **kwargs: 其他请求参数

        Returns:
            dict: 响应数据
        """
        url = f"{self.api_url}{endpoint}"

        # 设置默认headers
        headers = kwargs.pop('headers', {})
        headers.update(self.headers)

        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=kwargs.get('params'))
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, **kwargs)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, **kwargs)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, **kwargs)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")

            # 检查响应状态码
            if response.status_code >= 400:
                error_msg = f"HTTP错误: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f", 详情: {error_detail}"
                except:
                    if response.text:
                        error_msg += f", 响应: {response.text[:200]}"
                timeutils.print_log(f"请求失败: {error_msg}")
                return {"code": -1, "message": error_msg}

            # 检查响应内容是否为空
            if not response.content:
                error_msg = f"响应为空 (状态码: {response.status_code})"
                timeutils.print_log(f"请求失败: {error_msg}")
                return {"code": -1, "message": error_msg}

            # 解析JSON响应
            try:
                return response.json()
            except ValueError as json_error:
                error_msg = f"JSON解析失败: {json_error}, 响应内容: {response.text[:200]}"
                timeutils.print_log(f"请求失败: {error_msg}")
                return {"code": -1, "message": error_msg}

        except Exception as e:
            timeutils.print_log(f"请求失败: {e}")
            return {"code": -1, "message": str(e)}

    def check_api_url(self) -> tuple[bool, str]:
        """检测配置的API是否可以访问

        Returns:
            tuple[bool, str]: (是否可以访问, 提示文本)
        """
        url = f"{self.api_url}/system/healthz"
        try:
            # 健康检查端点通常不需要认证
            r = requests.get(url, timeout=10)
        except Exception as e:
            return False, f"请求失败，请检查API相关配置后重试，请求异常：{e}"

        if r.status_code != 200:
            return False, f"请求失败，请检查API相关配置后重试，请求状态码：{r.status_code}"

        try:
            response = r.json()
            # 健康检查端点返回格式：{"status": "ok", "db": "ok", "redis": "ok", ...}
            status = response.get("status")
            if status == "ok":
                return True, "API地址配置正确"
            else:
                return False, f"API服务状态异常：{status}"
        except Exception as e:
            return False, f"解析响应失败：{e}"

    def list_datasets(self, name: Optional[str] = None, id: Optional[str] = None) -> List[dict]:
        """列出知识库

        Args:
            name: 知识库名称（可选）
            id: 知识库ID

        Returns:
            list: 知识库列表
        """
        params = {}
        if name:
            params['name'] = name
        if id:
            params['id'] = id

        response = self._make_request('GET', '/datasets', params=params)

        if response.get('code') == 0:
            return response.get('data', [])
        else:
            timeutils.print_log(f"获取知识库列表失败: {response}")
            return []

    def get_dataset_by_name(self, dataset_name: str) -> Optional[dict]:
        """根据名称获取知识库

        Args:
            dataset_name: 知识库名称

        Returns:
            dict or None: 知识库信息
        """
        datasets = self.list_datasets(name=dataset_name)
        if datasets and len(datasets) > 0:
            return datasets[0]
        return None

    def create_dataset(self, name: str, chunk_method: str = 'naive',
                      parser_config: Optional[dict] = None) -> Optional[dict]:
        """创建知识库

        Args:
            name: 知识库名称
            chunk_method: 分块方法 (默认: naive)
            parser_config: 解析器配置

        Returns:
            dict or None: 创建的知识库信息
        """
        data = {
            "name": name,
            "chunk_method": chunk_method
        }

        if parser_config:
            data["parser_config"] = parser_config

        response = self._make_request('POST', '/datasets', json=data)

        if response.get('code') == 0:
            timeutils.print_log(f"创建知识库成功: {name}")
            return response.get('data')
        else:
            timeutils.print_log(f"创建知识库失败: {response}")
            return None

    def get_or_create_dataset(self, dataset_name: str, dataset_id: str) -> Optional[dict]:
        """获取或创建知识库

        Args:
            dataset_name: 知识库名称
            dataset_id: 知识库ID（用于兼容性检查）

        Returns:
            dict or None: 知识库信息
        """
        # 先尝试通过名称获取知识库
        dataset = self.get_dataset_by_name(dataset_name)

        if dataset:
            timeutils.print_log(f"找到现有知识库: {dataset_name} (ID: {dataset.get('id')})")
            return dataset

        # 知识库不存在，创建新知识库
        timeutils.print_log(f"知识库 {dataset_name} 不存在，创建新知识库")
        return self.create_dataset(dataset_name)

    def upload_document(self, dataset_id: str, file_path: str,
                      parser_id: Optional[str] = None) -> Optional[dict]:
        """上传文档到知识库

        Args:
            dataset_id: 知识库ID
            file_path: 文件路径
            parser_id: 解析器ID（可选）

        Returns:
            dict or None: 上传结果
        """
        if not os.path.exists(file_path):
            timeutils.print_log(f"文件不存在: {file_path}")
            return None

        # 准备文件上传
        files = {'file': open(file_path, 'rb')}

        # 上传到指定知识库
        url = f"{self.api_url}/datasets/{dataset_id}/documents"

        try:
            response = requests.post(url, files=files, headers=self.headers)

            # 检查响应状态码
            if response.status_code >= 400:
                error_msg = f"上传文档HTTP错误: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f", 详情: {error_detail}"
                except:
                    if response.text:
                        error_msg += f", 响应: {response.text[:200]}"
                timeutils.print_log(error_msg)
                return None

            # 检查响应内容是否为空
            if not response.content:
                timeutils.print_log(f"上传文档响应为空 (状态码: {response.status_code})")
                return None

            # 解析JSON响应
            try:
                result = response.json()
            except ValueError as json_error:
                timeutils.print_log(f"上传文档JSON解析失败: {json_error}, 响应内容: {response.text[:200]}")
                return None

            if result.get('code') == 0:
                data = result.get('data')
                if isinstance(data, list) and len(data) > 0:
                    doc_info = data[0]
                    timeutils.print_log(f"上传文档成功: {file_path} -> Document ID: {doc_info.get('id')}")
                    return doc_info
                else:
                    timeutils.print_log(f"上传文档响应格式异常: {data}")
                    return None
            else:
                timeutils.print_log(f"上传文档失败: {result}")
                return None
        except Exception as e:
            timeutils.print_log(f"上传文档异常: {e}")
            return None
        finally:
            # 确保文件被关闭
            if 'file' in files:
                files['file'].close()

    def list_documents(self, dataset_id: str, keywords: Optional[str] = None,
                      page: int = 1, page_size: int = 30) -> List[dict]:
        """列出知识库中的文档

        Args:
            dataset_id: 知识库ID
            keywords: 关键词搜索（可选）
            page: 页码（默认: 1）
            page_size: 每页数量（默认: 30）

        Returns:
            list: 文档列表
        """
        params = {
            'page': page,
            'page_size': page_size
        }

        if keywords:
            params['keywords'] = keywords

        response = self._make_request('GET', f'/datasets/{dataset_id}/documents', params=params)

        if response.get('code') == 0:
            data = response.get('data', {})
            return data.get('docs', [])
        else:
            timeutils.print_log(f"获取文档列表失败: {response}")
            return []

    def get_document_by_name(self, dataset_id: str, filename: str) -> Optional[dict]:
        """根据文件名获取文档

        Args:
            dataset_id: 知识库ID
            filename: 文件名

        Returns:
            dict or None: 文档信息
        """
        documents = self.list_documents(dataset_id, keywords=filename)
        if documents and len(documents) > 0:
            for doc in documents:
                if doc.get('name') == filename:
                    return doc
        return None

    def parse_documents(self, dataset_id: str, document_ids: List[str]) -> dict:
        """解析文档

        Args:
            dataset_id: 知识库ID
            document_ids: 文档ID列表

        Returns:
            dict: 解析结果
        """
        data = {
            "document_ids": document_ids
        }

        response = self._make_request('POST', f'/datasets/{dataset_id}/chunks', json=data)

        if response.get('code') == 0:
            timeutils.print_log(f"开始解析文档: {document_ids}")
        else:
            timeutils.print_log(f"解析文档失败: {response}")

        return response

    def get_document_status(self, dataset_id: str, document_id: str) -> dict:
        """获取文档状态

        Args:
            dataset_id: 知识库ID
            document_id: 文档ID

        Returns:
            dict: 文档状态信息
        """
        # 使用文档列表接口,通过id参数过滤来获取单个文档状态
        # 注意: GET /datasets/{dataset_id}/documents/{document_id} 是下载文档接口,不是状态查询接口
        params = {'id': document_id}
        response = self._make_request('GET', f'/datasets/{dataset_id}/documents', params=params)

        if response.get('code') == 0:
            data = response.get('data', {})
            docs = data.get('docs', [])
            if docs and len(docs) > 0:
                return docs[0]

        # 如果通过id参数过滤失败,尝试从完整文档列表中查找
        documents = self.list_documents(dataset_id)

        for doc in documents:
            if doc.get('id') == document_id:
                return doc

        timeutils.print_log(f"未找到文档: {document_id}")
        return {}

    def wait_for_parse_complete(self, dataset_id: str, document_id: str,
                              filename: str, max_wait: int = 3600) -> bool:
        """等待文档解析完成

        Args:
            dataset_id: 知识库ID
            document_id: 文档ID
            filename: 文件名
            max_wait: 最大等待时间（秒）

        Returns:
            bool: 是否解析成功
        """
        start_time = time.time()

        while time.time() - start_time < max_wait:
            doc_info = self.get_document_status(dataset_id, document_id)

            if not doc_info:
                time.sleep(configs.PROGRESS_CHECK_INTERVAL)
                continue

            run_status = doc_info.get('run')
            progress = doc_info.get('progress', 0)

            if configs.ENABLE_PROGRESS_LOG:
                progress_percent = round(progress * 100, 2)
                timeutils.print_log(f"{filename}解析进度为：{progress_percent}% (状态: {run_status})")

            if run_status == 'DONE':
                timeutils.print_log(f"{filename}解析完成")
                return True
            elif run_status == 'FAIL':
                timeutils.print_log(f"{filename}解析失败")
                return False
            elif run_status == 'CANCEL':
                timeutils.print_log(f"{filename}解析被取消")
                return False

            time.sleep(configs.PROGRESS_CHECK_INTERVAL)

        timeutils.print_log(f"{filename}解析超时")
        return False

    def update_document_metadata(self, dataset_id: str, document_id: str,
                               metadata: dict) -> bool:
        """更新文档元数据

        Args:
            dataset_id: 知识库ID
            document_id: 文档ID
            metadata: 元数据

        Returns:
            bool: 是否更新成功
        """
        data = {
            "meta_fields": metadata
        }

        response = self._make_request('PUT', f'/datasets/{dataset_id}/documents/{document_id}',
                                     json=data)

        if response.get('code') == 0:
            timeutils.print_log(f"设置文档元数据成功: {document_id}")
            return True
        else:
            timeutils.print_log(f"设置文档元数据失败: {response}")
            return False


# 创建全局实例
ragflow_v26 = RAGFlowSDKV26()


def check_api_url() -> tuple[bool, str]:
    """检测API配置（兼容旧接口）"""
    return ragflow_v26.check_api_url()


def upload_file_to_dataset(file_path: str, dataset_name: str, dataset_id: str,
                     parser_id: Optional[str] = None, run: Optional[str] = None) -> dict:
    """上传文件到知识库（兼容旧接口）

    Args:
        file_path: 文件路径
        dataset_name: 知识库名称
        dataset_id: 知识库ID
        parser_id: 解析器ID（可选）
        run: 是否运行（可选）

    Returns:
        dict: 上传结果
    """
    # 获取或创建知识库
    dataset = ragflow_v26.get_or_create_dataset(dataset_name, dataset_id)

    if not dataset:
        return {
            "code": -1,
            "message": f"无法获取或创建知识库: {dataset_name}"
        }

    dataset_id = dataset.get('id')

    # 检查文档是否已存在
    filename = os.path.basename(file_path)
    existing_doc = ragflow_v26.get_document_by_name(dataset_id, filename)

    if existing_doc:
        return {
            "code": 0,
            "data": [existing_doc],
            "message": "文档已存在"
        }

    # 上传文档
    result = ragflow_v26.upload_document(dataset_id, file_path, parser_id)

    if result:
        return {
            "code": 0,
            "data": [result],
            "message": "上传成功"
        }
    else:
        return {
            "code": -1,
            "message": "上传失败"
        }


def list_dataset_documents(dataset_id: str) -> list:
    """获取知识库文档列表（兼容旧接口）

    Args:
        dataset_id: 知识库ID

    Returns:
        list: 文档列表
    """
    # 从数据库中获取对应的知识库名称
    dataset = ragflow_v26.list_datasets(id=dataset_id)

    if not dataset or len(dataset) == 0:
        return []

    resolved_dataset_id = dataset[0].get('id')
    documents = ragflow_v26.list_documents(resolved_dataset_id)

    return documents


def set_document_metadata(doc_id: str, filepath: str) -> bool:
    """设置文档元数据（兼容旧接口）

    Args:
        doc_id: 文档ID
        filepath: 文件路径

    Returns:
        bool: 是否设置成功
    """
    # 检查元数据文件是否存在
    if not configs.METADATA_SUFFIX:
        return False

    filepath_without_ext = os.path.splitext(filepath)[0]
    metadata_filepath = filepath_without_ext + configs.METADATA_SUFFIX

    if not os.path.exists(metadata_filepath):
        timeutils.print_log(f'元数据文件不存在，跳过: {metadata_filepath}')
        return False

    # 读取元数据
    try:
        import json
        with open(metadata_filepath, 'r', encoding='utf-8') as f:
            metadata = f.read().strip()

        # 验证JSON格式
        json.loads(metadata)

        # 获取知识库ID
        dataset_id = configs.DATASET_ID if hasattr(configs, 'DATASET_ID') else None
        if not dataset_id and hasattr(configs, 'DATASET_NAME'):
            dataset = ragflow_v26.get_dataset_by_name(configs.DATASET_NAME)
            if dataset:
                dataset_id = dataset.get('id')

        if not dataset_id:
            timeutils.print_log("无法获取知识库ID")
            return False

        return ragflow_v26.update_document_metadata(dataset_id, doc_id,
                                                   json.loads(metadata))

    except Exception as e:
        timeutils.print_log(f'设置文档元数据失败: {e}')
        return False


def is_succeed(response: dict) -> bool:
    """判断请求是否成功（兼容旧接口）

    Args:
        response: 响应数据

    Returns:
        bool: 是否成功
    """
    return response.get("code") == 0 or response.get("retcode") == 0