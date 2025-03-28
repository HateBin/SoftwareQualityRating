import pytest
import builtins
from test_program import settings
from test_program.common import logger
from test_program.common.utils import expect_print_result_connect, check_where

class BaseCase:
    name = None
    logger = logger
    settings = settings

    @classmethod
    def setup_class(cls):
        cls.logger.info("=========={}测试开始==========".format(cls.name))

    @classmethod
    def teardown_class(cls):
        cls.logger.info("=========={}测试结束==========".format(cls.name))

    @pytest.fixture(scope='module')
    def login(self):
        from main_program.SoftwareQualityRating import get_session_id
        try:
            get_session_id()
        except SystemExit as e:
            self.logger.error(f'登录失败，请检查账号密码是否正确, 错误信息：{e}')
            raise e

    @classmethod
    def base_exist_return_common_test(cls, case, need_to_test_def, capsys=None, monkeypatch=None):
        result_data = {
            'code': 1,
            'type': '',
            'assert': [],
            'return': None
        }
        print_result = ''
        test_data = case.get('test_data', {})
        expect_result = case['expect_return_result']
        if case.get('inputs'):
            monkeypatch.setattr('builtins.input', lambda _: case['inputs'].pop(0))
        try:
            if isinstance(expect_result, Exception):
                try:
                    with pytest.raises(type(expect_result)) as exc_info:
                        need_to_test_def(**test_data)
                    act_raise = exc_info.value
                except Exception as e:
                    act_raise = e
                except pytest.fail.Exception:
                    act_raise = ''
                if str(act_raise) != str(expect_result) or type(act_raise) != type(expect_result):
                    result_data['code'] = 2
                    result_data['type'] = 'raise'
                    result_data['assert'] = [act_raise ,expect_result]
                    return result_data
            else:
                return_result = need_to_test_def(**test_data)
                if return_result is not None:
                    if isinstance(expect_result, dict):
                        if 'where' in expect_result:
                            if isinstance(expect_result['where'], list):
                                if not check_where(expect_result['where'], return_result):
                                    result_data['code'] = 3
                                    result_data['type'] = 'where.and'
                                    result_data['return'] = return_result
                                    return result_data
                            elif isinstance(expect_result['where'], dict):
                                if 'get' in expect_result['where']:
                                    for getKey in expect_result['where']['get']:
                                        if not return_result.get(getKey):
                                            result_data['code'] = 3
                                            result_data['type'] = f'where.get.{getKey}'
                                            result_data['return'] = return_result
                                            return result_data
                        else:
                            pass
                    elif return_result != expect_result:
                        result_data['code'] = 2
                        result_data['type'] = 'return'
                        result_data['assert'] = [return_result, expect_result]
                        return result_data
            if capsys is not None:
                print_result = capsys.readouterr().out
            if print_result or case.get('expect_print_result'):
                from main_program.SoftwareQualityRating import _print_text_font
                expect_print_result = expect_print_result_connect(
                    [_print_text_font(**data) for data in case['expect_print_result']]
                )
                if print_result != expect_print_result:
                    result_data['code'] = 2
                    result_data['type'] = 'print'
                    result_data['assert'] = [print_result, expect_print_result]
                    return result_data
        except SystemExit as e:
            result_data['code'] = 2
            result_data['type'] = 'sysExit'
            result_data['assert'] = [str(e), case['expect_print_result']]
            return result_data
        else:
            return result_data