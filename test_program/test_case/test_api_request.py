import time

from test_program.test_case import *

from main_program import SoftwareQualityRating as s
from urllib.parse import unquote


@pytest.mark.api
@pytest.mark.get_session_id
class TestGetSessionId(BaseCase):
    name = "调用tapd登录接口获取会话"

    cases = read_test_case_excel('get_session_id_case.xlsx')

    @pytest.fixture()
    def init_cookies(self):
        """
        用于执行测试脚本前清空cookie
        :return: None
        """
        s.scraper.cookies.clear()  # 清空cookies

    @pytest.mark.timeout(settings.PYTEST_TIMEOUT)
    @pytest.mark.parametrize('case', cases, ids=[case['case_id'] for case in cases])
    def test_get_session_id(self, case, init_cookies):
        """
        对封装的登录获取session的方法进行测试
        :param case: 测试用例数据
        :param init_cookies: 每一条测试用例执行前都清空cookies
        :return: None
        """
        from main_program.SoftwareQualityRating import get_session_id as t
        test_data: dict[str, str] = {}
        case_name: str = case['case_name']
        expect_msgs = case['expect_msg']
        self.logger.debug(f'测试用例{case_name}开始执行'.center(self.settings.LINE_LENGTH, '='))
        if case.get("test_data"):
            test_data.update(case.pop("test_data"))
        s.ACCOUNT = test_data.get('account', '')
        s.PASSWORD = test_data.get('password', '')

        result = self.base_exist_return_common_test(case, t)
        try:
            if result['code'] == 2:
                act, exp = result['assert']
                assert act == exp
            s_cookies = s.scraper.cookies.get_dict()
            if expect_msgs:
                for msg in expect_msgs:
                    if 't_cloud_login' in msg:
                        t_cloud_login = unquote(s_cookies.get("t_cloud_login"))
                        assert t_cloud_login == s.ACCOUNT
                    elif 'cookie' in msg:
                        assert s_cookies
        except Exception as e:
            assert_type_text = f'类型为：{result["type"]}, ' if result['code'] != 1 else ''
            self.logger.exception(f'测试用例{case_name}执行失败, {assert_type_text}错误信息：{e}')
            raise e

        self.logger.debug(f'测试用例{case_name}执行通过'.center(self.settings.LINE_LENGTH, '='))


@pytest.mark.api
@pytest.mark.get_workitem_status_transfer_history
class TestGetWorkitemStatusTransferHistory(BaseCase):
    name = "调用tapd获取工作项状态流转历史接口"
    cases = read_test_case_excel('get_workitem_status_transfer_history_case.xlsx')

    @pytest.mark.parametrize('case', cases, ids=[case['case_id'] for case in cases])
    def test_get_workitem_status_transfer_history(self, case, login):
        """
        对封装的调用tapd获取工作状态流程历史接口方法进行测试
        :param case: 测试用例数据
        :param login: 整个py文件的测试脚本中只执行一次登录获取session
        :return: None
        """
        from main_program.SoftwareQualityRating import get_workitem_status_transfer_history as t
        case_name = case['case_name']
        self.logger.debug(f'测试用例{case_name}开始执行'.center(self.settings.LINE_LENGTH, '='))
        result = self.base_exist_return_common_test(case, t)
        try:
            if result['code'] == 3:
                raise Exception(
                    'return值不符合预期条件\n'
                    f'where: {case["expect_return_result"]}\n'
                    f'return: {truncate_string(str(result["return"]))}'
                )
        except Exception as e:
            assert_type_text = f'类型为：{result["type"]}, ' if result['code'] != 1 else ''
            self.logger.exception(f'测试用例{case_name}执行失败, {assert_type_text}错误信息：{e}')
            raise e
        self.logger.debug(f'测试用例{case_name}执行通过'.center(self.settings.LINE_LENGTH, '='))


@pytest.mark.api
@pytest.mark.get_requirement_list_config
class TestGetRequirementListConfig(BaseCase):
    name = "调用tapd获取子需求列表的显示字段配置"
    cases = read_test_case_excel('get_requirement_list_config_case.xlsx')

    @pytest.mark.parametrize('case', cases, ids=[case['case_id'] for case in cases])
    def test_get_requirement_list_config(self, case, login):
        """
        对封装的调用tapd获取子需求列表显示字段配置的方法进行测试
        :param case: 测试用例数据
        :param login: 整个py文件的测试脚本中只执行一次登录获取session
        :return: None
        """
        from main_program.SoftwareQualityRating import get_requirement_list_config as t
        case_name = case['case_name']
        self.logger.debug(f'测试用例{case_name}开始执行'.center(self.settings.LINE_LENGTH, '='))
        result = self.base_exist_return_common_test(case, t)
        try:
            if result['code'] == 3:
                raise Exception(
                    'return值不符合预期条件\n'
                    f'where: {case["expect_return_result"]}\n'
                    f'return: {truncate_string(str(result["return"]))}'
                )
        except Exception as e:
            assert_type_text = f'类型为：{result["type"]}, ' if result['code'] != 1 else ''
            self.logger.exception(f'测试用例{case_name}执行失败, {assert_type_text}错误信息：{e}')
            raise e
        self.logger.debug(f'测试用例{case_name}执行通过'.center(self.settings.LINE_LENGTH, '='))

@pytest.mark.api
@pytest.mark.edit_requirement_list_config
class TestEditRequirementListConfig(BaseCase):
    name = "调用tapd编辑子需求列表的显示字段配置"
    cases = read_test_case_excel('edit_requirement_list_config_case.xlsx')

    @pytest.fixture()
    def get_old_config(self):
        from main_program.SoftwareQualityRating import get_requirement_list_config
        try:
            self.get_r = get_requirement_list_config
            self.old_configs = self.get_r()
        except Exception as e:
            self.logger.exception(f'获取子需求列表的显示字段配置失败, 错误信息：{e}')
            raise e

    @pytest.mark.parametrize('case', cases, ids=[case['case_id'] for case in cases])
    def test_edit_requirement_list_config(self, case, login, get_old_config):
        """
        对封装的调用tapd编辑子需求列表的显示字段配置的方法进行测试
        :param case: 测试用例数据
        :param login: 整个py文件的测试脚本中只执行一次登录获取session
        :param get_old_config: 每次执行脚本前调用一次获取初始配置方法
        :return: None
        """
        from main_program.SoftwareQualityRating import edit_requirement_list_config as t
        case_name = case['case_name']
        self.logger.debug(f'测试用例{case_name}开始执行'.center(self.settings.LINE_LENGTH, '='))
        result = self.base_exist_return_common_test(case, t)
        try:
            if result['code'] == 2:
                act, exp = result['assert']
                assert act == exp
            if not isinstance(case['expect_return_result'], Exception):
                exp_configs: list[str] = case['test_data']['custom_fields'].replace(" ", "").split(';')
                act_configs: list[str] = self.get_r()
                assert act_configs == exp_configs
        except Exception as e:
            assert_type_text = f'类型为：{result["type"]}, ' if result['code'] != 1 else ''
            self.logger.exception(f'测试用例{case_name}执行失败, {assert_type_text}错误信息：{e}')
            raise e
        finally:
            old_config_str = ';'.join(self.old_configs)
            t(old_config_str)
        self.logger.debug(f'测试用例{case_name}执行通过'.center(self.settings.LINE_LENGTH, '='))


@pytest.mark.api
@pytest.mark.get_query_filtering_list_config
class TestGetQueryFilteringListConfig(BaseCase):
    name = "调用tapd获取查询过滤列表的显示字段配置"
    cases = read_test_case_excel('get_query_filtering_list_config_case.xlsx')

    @pytest.mark.parametrize('case', cases, ids=[case['case_id'] for case in cases])
    def test_get_query_filtering_list_config(self, case, login):
        """
        对封装的调用tapd获取查询过滤列表显示字段配置的方法进行测试
        :param case: 测试用例数据
        :param login: 整个py文件的测试脚本中只执行一次登录获取session
        :return: None
        """
        from main_program.SoftwareQualityRating import get_query_filtering_list_config as t
        case_name = case['case_name']
        self.logger.debug(f'测试用例{case_name}开始执行'.center(self.settings.LINE_LENGTH, '='))
        result = self.base_exist_return_common_test(case, t)
        try:
            if result['code'] == 3:
                raise Exception(
                    'return值不符合预期条件\n'
                    f'where: {case["expect_return_result"]}\n'
                    f'return: {truncate_string(str(result["return"]))}'
                )
        except Exception as e:
            assert_type_text = f'类型为：{result["type"]}, ' if result['code'] != 1 else ''
            self.logger.exception(f'测试用例{case_name}执行失败, {assert_type_text}错误信息：{e}')
            raise e
        self.logger.debug(f'测试用例{case_name}执行通过'.center(self.settings.LINE_LENGTH, '='))

@pytest.mark.api
@pytest.mark.edit_query_filtering_list_config
class TestEditQueryFilteringListConfig(BaseCase):
    name = "调用tapd编辑查询过滤列表的显示字段配置"
    cases = read_test_case_excel('edit_query_filtering_list_config_case.xlsx')

    @pytest.fixture()
    def get_old_config(self):
        from main_program.SoftwareQualityRating import get_query_filtering_list_config
        try:
            self.get_q = get_query_filtering_list_config
            self.old_configs = self.get_q()
        except Exception as e:
            self.logger.exception(f'获取查询过滤列表的显示字段配置失败, 错误信息：{e}')
            raise e

    @pytest.mark.parametrize('case', cases, ids=[case['case_id'] for case in cases])
    def test_edit_query_filtering_list_config(self, case, login, get_old_config):
        """
        对封装的调用tapd编辑查询过滤列表的显示字段配置的方法进行测试
        :param case: 测试用例数据
        :param login: 整个py文件的测试脚本中只执行一次登录获取session
        :param get_old_config: 每次执行脚本前调用一次获取初始配置方法
        :return: None
        """
        from main_program.SoftwareQualityRating import edit_query_filtering_list_config as t
        case_name = case['case_name']
        self.logger.debug(f'测试用例{case_name}开始执行'.center(self.settings.LINE_LENGTH, '='))
        result = self.base_exist_return_common_test(case, t)
        try:
            if result['code'] == 2:
                act, exp = result['assert']
                assert act == exp
            if not isinstance(case['expect_return_result'], Exception):
                exp_configs: list[str] = case['test_data']['custom_fields'].replace(" ", "").split(';')
                act_configs: list[str] = self.get_q()
                assert act_configs == exp_configs
        except Exception as e:
            assert_type_text = f'类型为：{result["type"]}, ' if result['code'] != 1 else ''
            self.logger.exception(f'测试用例{case_name}执行失败, {assert_type_text}错误信息：{e}')
            raise e
        finally:
            old_config_str = ';'.join(self.old_configs)
            t(old_config_str)
        self.logger.debug(f'测试用例{case_name}执行通过'.center(self.settings.LINE_LENGTH, '='))


@pytest.mark.api
@pytest.mark.get_user_detail
class TestGetUserDetail(BaseCase):
    name = "调用tapd获取当前用户信息"
    cases = read_test_case_excel('get_user_detail_case.xlsx')

    @pytest.mark.parametrize('case', cases, ids=[case['case_id'] for case in cases])
    def test_get_user_detail(self, case, login):
        """
        对封装的调用tapd获取当前用户信息的方法进行测试
        :param case: 测试用例数据
        :param login: 整个py文件的测试脚本中只执行一次登录获取session
        :return: None
        """
        from main_program.SoftwareQualityRating import get_user_detail as t
        case_name = case['case_name']
        self.logger.debug(f'测试用例{case_name}开始执行'.center(self.settings.LINE_LENGTH, '='))
        result = self.base_exist_return_common_test(case, t)
        try:
            if result['code'] == 3:
                raise Exception(
                    'return值不符合预期条件\n'
                    f'where: {case["expect_return_result"]}\n'
                    f'return: {truncate_string(str(result["return"]))}'
                )
        except Exception as e:
            assert_type_text = f'类型为：{result["type"]}, ' if result['code'] != 1 else ''
            self.logger.exception(f'测试用例{case_name}执行失败, {assert_type_text}错误信息：{e}')
            raise e
        self.logger.debug(f'测试用例{case_name}执行通过'.center(self.settings.LINE_LENGTH, '='))



if __name__ == '__main__':
    pytest.main(['-s', '-vv', '-m', 'get_session_id'])
