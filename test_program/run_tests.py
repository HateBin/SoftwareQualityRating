import os
import sys
import pytest

dateTime = os.popen('date +%Y%m%d_%H%M%S').read().strip()
# 生成带时间戳的报告文件名
report_name = os.path.join(f"./reports/{dateTime}/temp")

# 运行 pytest
pytest.main(["-s", "-v", f"--alluredir={report_name}"] + sys.argv[1:])
os.system(f'allure generate ./reports/{dateTime}/temp -o ./reports/{dateTime}/report --clean')
