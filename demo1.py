def requirement_task_statistics(self):
    """
    统计需求关联的子任务数据，计算开发工时并识别关键时间节点

    核心功能：
    1. 遍历所有子任务，分离开发任务和测试任务
    2. 计算开发者总工时和每日工时分布
    3. 记录项目关键时间节点（最早/最晚任务日期、上线日期）
    4. 维护测试相关数据（测试负责人、收件人列表）

    优化点：
    - 使用 defaultdict 简化字典操作
    - 分离开发/测试任务处理逻辑
    - 增加数据校验和异常处理
    - 优化日期比较逻辑
    - 减少嵌套层次提升可读性
    """

    # ==================================================================
    # 阶段1：数据准备
    # ==================================================================
    from collections import defaultdict

    # 使用 defaultdict 自动初始化数据结构
    self.workHours = defaultdict(float)
    self.dailyWorkingHoursOfEachDeveloper = defaultdict(lambda: defaultdict(float))

    # 获取子任务数据（已处理分页逻辑）
    requirement_tasks = ger_requirement_tasks()
    if not requirement_tasks:
        print("警告：未获取到任何子任务数据")
        return

    # ==================================================================
    # 阶段2：遍历处理每个子任务
    # ==================================================================
    for child in requirement_tasks:
        try:
            # 数据校验：确保必需字段存在
            if not all(key in child for key in ('owner', 'begin', 'due', 'effort_completed')):
                print(f"无效任务数据，缺失关键字段：{child.get('id', '未知ID')}")
                continue

            # 数据清洗：去除部门前缀
            raw_owner = child['owner'].replace(";", "")
            processing_personnel = extract_matching(r"{}(.*?)$", raw_owner)[0]

            # 转换数据类型
            effort_completed = self._parse_effort(child.get('effort_completed', 0))
            begin_date = self._parse_date(child['begin'])
            due_date = self._parse_date(child['due'])

        except (ValueError, TypeError) as e:
            print(f"数据处理失败，任务ID：{child.get('id', '未知ID')} - {str(e)}")
            continue

        # ==================================================================
        # 阶段3：任务分类处理
        # ==================================================================
        # 开发者任务处理
        if processing_personnel not in TESTERS:
            self._process_developer_task(
                developer=processing_personnel,
                effort=effort_completed,
                begin=begin_date,
                due=due_date,
                child_data=child
            )
        # 测试任务处理
        else:
            self._process_tester_task(
                due_date=due_date,
                begin_date=begin_date,
                owner=raw_owner
            )

    # ==================================================================
    # 阶段4：后期校验
    # ==================================================================
    if not self.earliestTaskDate or not self.lastTaskDate:
        print("警告：未能识别有效任务时间范围")
    if not self.onlineDate:
        print("警告：未识别到上线日期")


def _parse_effort(self, value) -> float:
    """解析工时数据并校验有效性"""
    try:
        effort = float(value)
        if effort < 0:
            raise ValueError("工时不能为负数")
        return effort
    except (TypeError, ValueError):
        print(f"无效工时数据：{value}，已重置为0")
        return 0.0


def _parse_date(self, date_str) -> datetime.date:
    """日期解析与标准化"""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValueError(f"无效日期格式：{date_str}")


def _process_developer_task(self, developer: str, effort: float, begin: datetime.date,
                            due: datetime.date, child_data: dict):
    """
    处理开发者任务逻辑
    - 累加工时
    - 记录任务时间范围
    - 保存详细工时分布
    """
    # 累加总工时
    self.workHours[developer] += effort

    # 更新任务时间范围
    self._update_date_range(begin, due)

    # 保存子任务引用（用于后续分析）
    child_data['developerName'] = developer

    # 记录每日工时分布（如果存在有效时间）
    if begin and due:
        self._record_daily_hours(developer, effort, begin, due)


def _process_tester_task(self, due_date: datetime.date, begin_date: datetime.date, owner: str):
    """
    处理测试任务逻辑
    - 标记测试任务存在
    - 更新上线日期
    - 维护测试联系人列表
    """
    # 首次遇到测试任务时标记
    if not self.isExistTestTask:
        self.isExistTestTask = True

    # 更新最晚任务日期（使用安全的日期比较）
    if due_date and (not self.lastTaskDate or due_date > self.lastTaskDate):
        self.lastTaskDate = due_date

    # 更新上线日期逻辑优化
    if begin_date and (not self.onlineDate or begin_date > self.onlineDate):
        self.onlineDate = begin_date

    # 维护测试收件人列表（去重处理）
    if owner not in self.testRecipient:
        self.testRecipient.append(owner)


def _update_date_range(self, begin: datetime.date, due: datetime.date):
    """更新项目时间范围记录"""
    # 最早任务日期
    if begin:
        if not self.earliestTaskDate or begin < self.earliestTaskDate:
            self.earliestTaskDate = begin

    # 最晚任务日期（开发者任务维度）
    if due:
        if not self.lastTaskDate or due > self.lastTaskDate:
            self.lastTaskDate = due


def _record_daily_hours(self, developer: str, effort: float,
                        begin: datetime.date, due: datetime.date):
    """
    记录开发者每日工时分布
    算法优化：使用工作日历计算日期范围
    """
    # 获取有效工作日范围
    try:
        work_days = get_days(str(begin), str(due), is_workday=True)
    except ValueError as e:
        print(f"无效日期范围[{begin}-{due}]：{str(e)}")
        return

    if not work_days:
        return

    # 计算日均工时
    daily_effort = effort / len(work_days)

    # 记录到每日工时
    for day in work_days:
        self.dailyWorkingHoursOfEachDeveloper[developer][day] += daily_effort