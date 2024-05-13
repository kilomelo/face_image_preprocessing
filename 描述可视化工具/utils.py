import logging

def setup_logging():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def is_descriptor_file(filepath):
    # 检查是否为描述文件
    try:
        with open(filepath, 'r') as file:
            first_line = file.readline()
            return "Unique Images:" in first_line
    except Exception as e:
        logging.error(f"Error checking descriptor file: {e}")
        return False