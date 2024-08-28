
        
import glob
import os
from ragflows import api, configs, ragflowdb
from utils import timeutils


def get_docs_files():
    if not os.path.exists(configs.DOC_DIR):
        raise ValueError(f"文档目录configs.DOC_DIR（{configs.DOC_DIR}）不存在")
    
    all_files = []
    
    for ext in configs.DOC_SUFFIX.split(','):
        # 使用递归通配符 ** 搜索子目录中的文件
        files = glob.glob(f'{configs.DOC_DIR}/**/*.{ext.strip()}', recursive=True)
        all_files.extend(files)

    return all_files 


def get_file_lines(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return len(f.readlines())


if __name__ == '__main__':
    
    # 使用 glob 模块获取所有 .md 文件
    doc_files = get_docs_files() or []

    file_total = len(doc_files)
    if file_total == 0:
        raise ValueError(f"在 {configs.DOC_DIR} 目录下没有找到符合要求文档文件") 
    
    # 打印找到的所有 .md 文件
    for i in range(file_total):
        
        file_path = doc_files[i]
        file_path = file_path.replace(os.sep, '/')
        filename = os.path.basename(file_path)
        
        timeutils.print_log(f"【{i+1}/{file_total}】正在处理：{file_path}")
        
        # 判断文件行数是否小于 目标值
        file_lines = get_file_lines(file_path)
        if file_lines < configs.DOC_MIN_LINES:
            timeutils.print_log(f"行数低于{configs.DOC_MIN_LINES}，跳过：{file_path}")
            continue
        
        # 如果文件已存在，则判断是否已经对文件进行了切片解析
        if ragflowdb.exist_name(filename):
            doc_item = ragflowdb.get_doc_item_by_name(filename)
            if doc_item.get('progress') == 1:
                timeutils.print_log(f"{file_path} 已上传，跳过")
            else:
                status = api.parse_chunks_with_check(doc_item)
                timeutils.print_log(f"{file_path} 切片状态：", status)
            continue
        
        # 文件不存在，上传文件=>切片=>解析并等待解析完毕
        response = api.upload_file_to_kb(
            file_path=file_path, 
            kb_name=configs.KB_NAME, 
            kb_id=configs.DIFY_DOC_KB_ID,
            parser_id=configs.PARSER_ID, 
            run="1"
        )
        timeutils.print_log(response)
        if api.is_succeed(response) is False:
            timeutils.print_log(f'{file_path} 上传失败：{response.get("text")}')
            continue
        
        timeutils.print_log(f'{file_path}，开始切片并等待解析完毕')
        status = api.parse_chunks_with_check(filename)
        timeutils.print_log(file_path, "切片状态：", status)
    
    timeutils.print_log('all done')