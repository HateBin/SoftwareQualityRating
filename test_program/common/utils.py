import os
import re
import json
import builtins
import pandas as pd
from test_program import settings


def read_test_case_excel(excel_name):
    backslash_replace_re = {'pattern': re.compile(r'(?<!\\)\\(?![\\n])'), 'repl': r'\\\\'}
    # 初始化用例列表
    test_cases: list[dict] = []
    # 组装用例文件路径
    case_path = os.path.join(settings.EXCEL_CASE_DIR, excel_name)
    # 防御性处理：如果用例文件路径不存在，则抛出异常
    if not os.path.exists(case_path):
        raise FileNotFoundError(f'测试用例文件不存在, {case_path}')

    # 读取excel文件
    df = pd.read_excel(case_path)

    # 遍历每一条用例数据
    for rowIndex, rowData in df.iterrows():

        row_data = {key: value if not pd.isna(value) else None for key, value in rowData.items()}

        for key in ['case_id', 'case_name', 'level', 'direction']:
            if not row_data.get(key):
                raise ValueError(f'文件{excel_name}，用例数据错误，第{rowIndex + 2}行，{key}为空')

        if row_data.get('test_data'):
            try:
                row_data['test_data'] = json.loads(
                    re.sub(
                        string=row_data['test_data'],
                        **backslash_replace_re
                    )
                )
            except json.JSONDecodeError as e:
                raise ValueError(
                    f'文件{excel_name}，用例数据错误，第{rowIndex + 2}行，test_data为json格式错误, 错误信息为：{e}'
                )

        if row_data.get('expect_return_result'):
            try:
                row_data['expect_return_result'] = json.loads(row_data['expect_return_result'])
            except json.JSONDecodeError:
                try:
                    row_data['expect_return_result'] = eval(row_data['expect_return_result'])
                except (NameError, SyntaxError, TypeError):
                    if re.fullmatch(r'^".*?"$', row_data['expect_return_result']):
                        row_data['expect_return_result'] = re.findall(
                            r'^"(.*?)"$', row_data['expect_return_result']
                        )[0]
                    else:
                        where_text: str = row_data['expect_return_result'].replace(' ', '').replace('\n', '').lower()
                        where_datas: dict[str, list or  dict] = {'where': []}
                        if 'get' not in where_text:
                            where_datas['where'].extend(where_text.split('and'))
                            for index, data in enumerate(where_datas['where']):
                                index: int
                                data: str
                                data = data.replace('(', '').replace(')', '')
                                where_datas['where'][index] = {'or': data.split('or')}
                        else:
                            where_datas["where"] = {'get': re.findall(r'get\(["\']?(.*?)["\']?\)', where_text)}

                        row_data['expect_return_result'] = where_datas
            except TypeError:
                row_data['expect_return_result'] = row_data['expect_return_result']

        if row_data.get('inputs'):
            row_data['inputs'] = json.loads(row_data['inputs'])

        if row_data.get('expect_print_result'):
            row_data['expect_print_result'] = json.loads(
                re.sub(
                    string=row_data['expect_print_result'],
                    **backslash_replace_re
                )
            )

        if row_data.get('expect_msg'):
            row_data['expect_msg'] = row_data['expect_msg'].split('\n')

        test_case = {
            'case_id': row_data['case_id'],
            'case_name': row_data['case_name'],
            'level': row_data['level'],
            'direction': row_data['direction'],
            'inputs': row_data.get('inputs'),
            'test_data': row_data['test_data'] if row_data.get('test_data') else {},
            'expect_return_result': row_data.get('expect_return_result'),
            'expect_print_result': row_data['expect_print_result'] if row_data.get('expect_print_result') else [],
            'expect_msg': row_data.get('expect_msg'),
        }

        test_cases.append(test_case)

    return test_cases


def expect_print_result_connect(texts: list[str]):
    print_text = ''
    for text in texts:
        print_text += text + '\n'
    return print_text

def where_data_split_expression(text: str):
    pattern = r'([<>=!]+|\w+)'
    result = re.findall(pattern, text)
    return result

def is_number(value: str):
    try:
        float(value)
        return True
    except ValueError:
        return False

def switch_number(value: str):
    if value.isdigit():
        return int(value)
    try:
        return float(value)
    except ValueError:
        raise False

def truncate_string(text: str, max_length: int = settings.STRING_MAX_LENGTH):
    if len(text) > max_length:
        return text[:max_length] + '...'
    else:
        return text

def check_where(where_datas: list, data: dict or list or tuple):
    check_and_bools = []
    for orWhereData in where_datas:
        or_error_number = 0
        orWhereData: dict[str, list]
        for orWhere in orWhereData['or']:
            orWhere: str
            or_where_split: list = where_data_split_expression(orWhere)
            number_index = [i for i, value in enumerate(or_where_split) if is_number(value)][0]
            comparison_operator = or_where_split[1]
            if number_index == 0:
                or_where_split[0], or_where_split[-1] = or_where_split[-1], or_where_split[0]
                if comparison_operator == '>':
                    comparison_operator = '<'
                elif comparison_operator == '<':
                    comparison_operator = '>'
                elif comparison_operator == '>=':
                    comparison_operator = '<='
                elif comparison_operator == '<=':
                    comparison_operator = '>='
            method = getattr(builtins, or_where_split[0], None)
            if not method:
                raise ValueError(f'{or_where_split[0]} 不是一个函数')
            number = or_where_split[-1]
            if comparison_operator == '>':
                or_error_number += 0 if method(data) > switch_number(number) else 1
            elif comparison_operator == '<':
                or_error_number += 0 if method(data) < switch_number(number) else 1
            elif comparison_operator == '>=':
                or_error_number += 0 if method(data) >= switch_number(number) else 1
            elif comparison_operator == '<=':
                or_error_number += 0 if method(data) <= switch_number(number) else 1
            elif comparison_operator == '=':
                or_error_number += 0 if method(data) == switch_number(number) else 1
            elif comparison_operator == '!=':
                or_error_number += 0 if method(data) != switch_number(number) else 1
            else:
                raise ValueError(f'{comparison_operator} 不是一个比较运算符')
        check_and_bools.append(or_error_number == 0)
    return all(check_and_bools)



if __name__ == '__main__':
    # print(read_test_case_excel('common_print_text_font_case.xlsx'))
    print(read_test_case_excel('ai_result_switch_html_case.xlsx'))
    # print(read_test_case_excel('get_workitem_status_transfer_history_case.xlsx'))
    # data = {
    #     'where_datas': [{'or': ['1<len']}, {'or': ['len!=10']}],
    #     'data': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    # }
    # print(check_where(**data))