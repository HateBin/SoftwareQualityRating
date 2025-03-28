import os
import sys
import pytest

dateTime = os.popen('date +%Y%m%d_%H%M%S').read().strip()

base_dir = os.path.dirname(os.path.abspath(__file__))

# 生成带时间戳的报告文件名
report_name_dir = os.path.join(base_dir, f"reports/{dateTime}")
report_temp_dir = os.path.join(report_name_dir, "temp")
report_dir = os.path.join(report_name_dir, "report")

add_sys: list[str] = []
sys_argv: list[str] = sys.argv[1:]

if '-m' in sys_argv:
    m_index = sys_argv.index('-m')
    if m_index + 2 <= len(sys_argv):
        add_sys.extend(sys_argv)
else:
    add_sys.extend(["-m", "not get_session_id"])

# 运行 pytest
pytest.main(["-s", "-vv", f"--alluredir={report_temp_dir}"] + add_sys)
os.system(f'allure generate {report_temp_dir} -o {report_dir} --clean')
