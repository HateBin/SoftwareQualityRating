import pytest
from test_program import settings
from test_program.common import logger


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

    def base_exist_return_common_test(self, case, need_to_test_def):
        case_name = case['case_name']
        test_data = case['test_data']
        expect_result = case['expect_result']
        self.logger.info(f'开始执行用例：{case_name}'.center(self.settings.LINE_LENGTH, '='))
        try:
            if isinstance(expect_result, Exception):
                with pytest.raises(type(expect_result)) as exc_info:
                    need_to_test_def(**test_data)
                # 断言异常信息
                assert str(exc_info.value) == str(expect_result)
            else:
                # 计算BUG数评分
                result = need_to_test_def(**test_data)
                # 断言
                assert result == expect_result
        except Exception as e:
            self.logger.error(f'执行用例：{case_name} 失败，失败原因：{e}')
            raise e
        self.logger.debug(f'执行用例：{case_name} 成功'.center(self.settings.LINE_LENGTH, '='))

