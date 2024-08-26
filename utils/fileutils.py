#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author：samge
# date：2024-08-23 11:10
# describe：


import os


def get_root_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace(os.sep, '/')


def get_cache_dir(sub_dir=""):
    root_dir = get_root_dir()
    cache_dir = f"{root_dir}/.cache"
    if sub_dir:
        cache_dir = f"{cache_dir}/{sub_dir}"
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def read(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def save(filepath, context, mode='w'):
    file_dir = os.path.dirname(filepath)
    if not os.path.exists(file_dir):
        os.makedirs(file_dir, exist_ok=True)
    with open(filepath, mode, encoding='utf-8') as f:
        f.write(context)