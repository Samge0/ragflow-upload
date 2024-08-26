
        
import glob
import os
from ragflows import api, config, ragflowdb
from utils import timeutils


def get_docs_files():
    
    if not os.path.exists(config.DOC_DIR):
        raise ValueError(f"文档目录config.DOC_DIR（{config.DOC_DIR}）不存在")
    
    all_files = []
    
    for ext in config.DOC_SUFFIX.split(','):
        files = glob.glob(f'{config.DOC_DIR}/*.{ext.strip()}', recursive=True)
        all_files.extend(files)

    return all_files


if __name__ == '__main__':
    
    # 使用 glob 模块获取所有 .md 文件
    doc_files = get_docs_files()

    # 打印找到的所有 .md 文件
    for file_path in doc_files:
        file_path = file_path.replace(os.sep, '/')
        
        filename = os.path.basename(file_path)
        
        # 如果文件已存在，则判断是否已经对文件进行了切片解析
        if ragflowdb.exist_name(filename):
            doc_item = ragflowdb.get_doc_item_by_name(filename)
            if doc_item.get('progress') == 1:
                timeutils.print_log(f"{file_path} 已上传，跳过")
            else:
                status = api.parse_chunks_with_check(doc_item)
                timeutils.print_log("切片状态：", status)
            continue
        
        # 文件不存在，上传文件=>切片=>解析并等待解析完毕
        response = api.upload_file_to_kb(
            file_path=file_path, 
            kb_name=config.KB_NAME, 
            kb_id=config.DIFY_DOC_KB_ID,
            parser_id=config.PARSER_ID, 
            run="1"
        )
        timeutils.print_log(response)
        if api.is_succeed(response) is False:
            timeutils.print_log(f'上传失败：{response.get("text")}')
            continue
        
        timeutils.print_log(f'{filename}，开始切片并等待解析完毕')
        status = api.parse_chunks_with_check(filename)
        timeutils.print_log(filename, "切片状态：", status)
    
    timeutils.print_log('all done')