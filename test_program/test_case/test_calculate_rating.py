from test_program.test_case import *


@pytest.mark.calculate_rating
@pytest.mark.calculate_bug_count_rating
class TestCalculateBugCountRating(BaseCase):
    name = 'BUG密度计算BUG数评分'
    cases = read_test_case_excel('calculate_bug_count_rating_case.xlsx')

    @pytest.mark.parametrize('case', cases, ids=[case['case_id'] for case in cases])
    def test_calculate_bug_count_rating(self, case):
        """
        BUG密度计算BUG数评分
        :param case: 测试用例数据
        :return: 无
        """
        from main_program.SoftwareQualityRating import calculate_bug_count_rating as t
        self.base_exist_return_common_test(case, t)


@pytest.mark.calculate_rating
@pytest.mark.calculate_bug_reopen_rating
class TestCalculateBugReopenRating(BaseCase):
    name = 'BUG重启和未修复数量计算评分'
    cases = read_test_case_excel('calculate_bug_reopen_rating_case.xlsx')

    @pytest.mark.parametrize('case', cases, ids=[case['case_id'] for case in cases])
    def test_calculate_bug_reopen_rating(self, case):
        """
        BUG重启和未修复数计算BUG重启评分
        :param case: 测试用例数据
        :return: 无
        """
        from main_program.SoftwareQualityRating import calculate_bug_reopen_rating as t
        self.base_exist_return_common_test(case, t)


@pytest.mark.calculate_rating
@pytest.mark.calculate_bug_repair_rating
class TestCalculateBugReopenRating(BaseCase):
    name = 'BUG修复情况评分计算'
    cases = read_test_case_excel('calculate_bug_repair_rating_case.xlsx')

    @pytest.mark.parametrize('case', cases, ids=[case['case_id'] for case in cases])
    def test_calculate_bug_repair_rating(self, case):
        """
        BUG修复情况评分计算，计算数据为dict类型，存储上线当天未修复的bugId和创建当天未修复的bugId
        :param case: 测试用例数据
        :return: 无
        """
        from main_program.SoftwareQualityRating import calculate_bug_repair_rating as t
        self.base_exist_return_common_test(case, t)


if __name__ == '__main__':
    pytest.main(['-s', '-v', '-m', 'calculate_bug_repair_rating'])
