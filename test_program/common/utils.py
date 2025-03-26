import os
import json
import pandas as pd
from test_program import settings

def read_test_case_excel(excel_name):
    test_cases = []
    case_path = os.path.join(settings.EXCEL_CASE_DIR, excel_name)
    if not os.path.exists(case_path):
        raise FileNotFoundError(f'测试用例文件不存在, {case_path}')
    df = pd.read_excel(case_path)
    for rowIndex, rowData in df.iterrows():
        if pd.isna(rowData['test_data']):
            test_data = {}
        else:
            test_data = json.loads(rowData['test_data'])

        try:
            expect_result = json.loads(rowData['expect_result'])
        except json.JSONDecodeError:
            expect_result = eval(rowData['expect_result'])
        except TypeError:
            expect_result = rowData['expect_result']

        test_case = {
            'case_id': rowData['case_id'],
            'case_name': rowData['case_name'],
            'level': rowData['level'],
            'direction': rowData['direction'],
            'test_data': test_data,
            'expect_result': expect_result,
        }

        test_cases.append(test_case)

    return test_cases

if __name__ == '__main__':
    print(read_test_case_excel('calculate_bug_reopen_rating_case.xlsx'))