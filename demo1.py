def bug_list_detail(self) -> None:
    """
    获取指定需求关联的缺陷列表及其分类信息

    通过TAPD搜索接口分页获取指定需求的所有缺陷数据，同时提取平台和根源的分类选项信息。
    支持分页请求和动态字段配置，确保获取完整的缺陷数据集。

    功能说明:
        1. 获取缺陷列表基础数据及分类元数据
        2. 遍历缺陷数据进行多维统计
        3. 记录缺陷生命周期关键时间节点
        4. 维护未修复缺陷状态信息

    异常处理:
        ValueError: 当无法获取缺陷数据或数据结构异常时抛出
        KeyError: 当接口返回数据缺失关键字段时抛出

    实现逻辑:
        1. 调用统一接口获取缺陷数据
        2. 初始化统计数据结构
        3. 遍历缺陷记录进行字段解析
        4. 执行多维度数据聚合
        5. 输出基础统计结果
    """
    # 调用API接口获取缺陷基础数据及分类元数据
    platforms, sources, bugs = get_bug_list(self.requirementName)
    platforms: list[str]  # 平台分类选项列表（如iOS/Android）
    sources: list[str]    # 缺陷根源分类选项列表（如代码问题/需求问题）
    bugs: list[dict]      # 缺陷数据字典列表

    # 打印分隔线标识统计区块开始
    print('-' * LINE_LENGTH)

    # 检查缺陷数据获取结果
    if not bugs:  # 无缺陷数据时的处理
        print('未获取BUG数量')
        return

    # 遍历每个缺陷记录进行详细处理
    for bug in bugs:
        # 提取缺陷状态信息，过滤已拒绝状态
        bug_status = bug.get('status')
        if bug_status != 'rejected':  # 仅处理非拒绝状态的缺陷
            # 解析缺陷核心字段
            bug_id = bug.get('id')  # 缺陷唯一标识符
            severity_name: str = bug.get('custom_field_严重等级')  # 严重等级字段值
            bug_source = bug.get('source')  # 缺陷根源分类值
            bug_field_level = bug.get('custom_field_Bug等级')  # BUG等级分类值
            bug_platform = bug['platform'] if bug.get('platform') else '空'  # 平台信息空值处理
            fixer = bug['fixer'] if bug.get('fixer') else '空'  # 修复人信息空值处理

            # 处理严重等级字段格式（去除后缀编号）
            if severity_name:
                severity_name = severity_name.split('-')[0]

            # 统计各严重等级的缺陷数量
            self._statistics_bug_severity_level(severity_name)

            # 统计各缺陷根源的数量
            self._statistics_bug_source(bug_source)

            # 记录缺陷状态变化趋势数据
            self._daily_trend_of_bug_changes_count(bug)

            # 多维度统计：各平台下的缺陷等级分布
            multi_client_data_processing(
                result=self.bugLevelsMultiClientCount,
                sub_key=severity_name,  # 当前缺陷的严重等级
                all_sub_keys=BUG_LEVELS,  # 所有可能的缺陷等级
                key=bug_platform,  # 当前缺陷所属平台
            )

            # 多维度统计：各平台下的缺陷根源分布
            multi_client_data_processing(
                result=self.bugSourceMultiClientCount,
                sub_key=bug_source,  # 当前缺陷的根源分类
                all_sub_keys=sources,  # 所有可能的根源分类
                key=bug_platform,  # 当前缺陷所属平台
            )

            # 处理有效缺陷ID记录
            if bug_id:
                self.bugIds.append(bug_id)  # 添加到全局缺陷ID列表
                # 转换日期字段格式
                created_date = date_time_to_date(bug.get('created'))  # 缺陷创建日期
                resolved_date = date_time_to_date(bug['resolved']) if bug.get('resolved') else None  # 解决日期

                # 统计顽固型缺陷（180天未修复）
                if bug_field_level and bug_field_level == '顽固（180 天）':
                    self.unrepairedBugsData[bug_id] += 1  # 计数器递增

                # 统计上线当天未修复的缺陷
                self._statistics_deploy_prod_day_unrepaired_bug(
                    bug_status, bug_id, severity_name, resolved_date
                )

                # 统计创建当天未修复的缺陷
                self._statistics_on_that_day_unrepaired_bug(
                    bug_status, bug_id, severity_name, created_date, resolved_date
                )

            # 统计缺陷修复人信息
            self.fixers[fixer] = self.fixers.get(fixer, 0) + 1  # 修复人计数器递增

    # 输出各严重等级的缺陷数量统计结果
    for severityName, count in self.bugLevelsCount.items():
        print(f"{severityName}BUG数量：{count}")

    # 记录缺陷总数到类属性
    self.bugTotal = len(self.bugIds)