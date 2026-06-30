#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 文件状态存储 - JSON 实现，记录每个文件的独立处理状态

import json
import os
from pathlib import Path


class StateStore:
    """基于 JSON 的文件状态存储，支持原子写入"""

    PENDING = 'pending'      # 待处理
    UPLOADED = 'uploaded'    # 已上传，未解析
    PARSING = 'parsing'      # 解析中
    DONE = 'done'            # 完成（下次运行跳过）
    FAILED = 'failed'        # 失败（下次运行自动重试）

    def __init__(self, cache_key: str):
        """
        Args:
            cache_key: 缓存键，使用 DATASET_ID 或 DATASET_NAME
        """
        config_dir = os.path.join(str(Path.home()), '.ragflow_upload')
        os.makedirs(config_dir, exist_ok=True)
        self.state_filepath = os.path.join(config_dir, f'state_{cache_key}.json').replace(os.sep, '/')
        self._states = self._load()

    def _load(self) -> dict:
        """加载状态文件，损坏或不存在时返回空 dict"""
        if not os.path.exists(self.state_filepath):
            return {}
        try:
            with open(self.state_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _flush(self) -> None:
        """原子写入状态文件（tmp + os.replace）"""
        tmp_path = self.state_filepath + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(self._states, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.state_filepath)

    def get(self, file_path: str) -> str:
        """获取文件状态，默认返回 PENDING"""
        return self._states.get(file_path, self.PENDING)

    def set(self, file_path: str, status: str) -> None:
        """设置文件状态并立即写入磁盘"""
        self._states[file_path] = status
        self._flush()

    def should_process(self, file_path: str) -> bool:
        """判断文件是否需要处理：非 DONE 的都需要处理"""
        return self.get(file_path) != self.DONE

    def reset(self) -> None:
        """清空所有状态：优先删除 state.json，失败则覆盖写入空 dict"""
        self._states = {}
        if os.path.exists(self.state_filepath):
            try:
                os.remove(self.state_filepath)
            except OSError:
                self._flush()
