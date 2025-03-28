from test_program.test_case import *

@pytest.mark.common
@pytest.mark.common_input
class TestCommonInput(BaseCase):
    name = '封装公用input方法'
    cases = read_test_case_excel('common_input_case.xlsx')

    @pytest.mark.timeout(settings.PYTEST_TIMEOUT)
    @pytest.mark.parametrize('case', cases, ids=[case['case_id'] for case in cases])
    def test_common_input(self, case, capsys, monkeypatch):
        """
        对封装的公用input方法进行测试
        :param case: 测试用例数据
        :return: 无
        """
        from main_program.SoftwareQualityRating import _input as t
        case_name = case['case_name']
        self.logger.debug(f'测试用例{case_name}开始执行'.center(self.settings.LINE_LENGTH, '='))
        result = self.base_exist_return_common_test(case, t, capsys, monkeypatch)
        try:
            if result['code'] == 2:
                act, exp = result['assert']
                assert act == exp
        except Exception as e:
            assert_type_text = f'类型为：{result["type"]}, ' if result['code'] != 1 else ''
            self.logger.exception(f'测试用例{case_name}执行失败, {assert_type_text}错误信息：{e}')
            raise e
        self.logger.debug(f'测试用例{case_name}执行通过'.center(self.settings.LINE_LENGTH, '='))

@pytest.mark.common
@pytest.mark.common_print_text_font
class TestCommonPrintTextFont(BaseCase):
    name = '封装print字体处理'
    cases = read_test_case_excel('common_print_text_font_case.xlsx')

    @pytest.mark.timeout(settings.PYTEST_TIMEOUT)
    @pytest.mark.parametrize('case', cases, ids=[case['case_id'] for case in cases])
    def test_common_print_text_font(self, case):
        """
        对封装的公用print字体处理方法进行测试
        :param case: 测试用例数据
        :return: 无
        """
        from main_program.SoftwareQualityRating import _print_text_font as t
        case_name = case['case_name']
        self.logger.debug(f'测试用例{case_name}开始执行'.center(self.settings.LINE_LENGTH, '='))
        result = self.base_exist_return_common_test(case, t)
        try:
            if result['code'] == 2:
                act, exp = result['assert']
                assert act == exp
        except Exception as e:
            assert_type_text = f'类型为：{result["type"]}, ' if result['code'] != 1 else ''
            self.logger.exception(f'测试用例{case_name}执行失败, {assert_type_text}错误信息：{e}')
            raise e
        self.logger.debug(f'测试用例{case_name}执行通过'.center(self.settings.LINE_LENGTH, '='))


@pytest.mark.common
@pytest.mark.ai_result_switch_html
class TestAiResultSwitchHtml(BaseCase):
    name = '封装AI结果转换成html'
    cases = read_test_case_excel('ai_result_switch_html_case.xlsx')

    @pytest.mark.parametrize('case', cases, ids=[case['case_id'] for case in cases])
    def test_ai_result_switch_html(self, case):
        """
        对封装的AI结果转换成html方法进行测试
        :param case: 测试用例数据
        :return: 无
        """
        from main_program.SoftwareQualityRating import ai_result_switch_html as t
        case_name = case['case_name']
        self.logger.debug(f'测试用例{case_name}开始执行'.center(self.settings.LINE_LENGTH, '='))
        result = self.base_exist_return_common_test(case, t)
        try:
            if result['code'] == 2:
                act, exp = result['assert']
                assert act == exp
        except Exception as e:
            assert_type_text = f'类型为：{result["type"]}, ' if result['code'] != 1 else ''
            self.logger.exception(f'测试用例{case_name}执行失败, {assert_type_text}错误信息：{e}')
            raise e
        self.logger.debug(f'测试用例{case_name}执行通过'.center(self.settings.LINE_LENGTH, '='))


if __name__ == '__main__':
    pytest.main(['-s', '-vv', '-m', 'common_input'])
