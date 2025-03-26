import os
import time

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EXCEL_CASE_DIR = os.path.join(BASE_DIR, 'test_data')

LINE_LENGTH = 50

# 测试用例路径
TEST_CASE_DIR = os.path.join(BASE_DIR, 'test_cases')


# 日志配置
LOG_CONFIG = {
    'name': "testlog",
    'filename': os.path.join(BASE_DIR, 'logs/testlog{}.log'.format(time.strftime('%Y%m%d'))),
    'mode': 'a',
    'encoding': 'utf-8',
    'debug': True
}