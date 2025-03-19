def _charts_to_html(self, charts: list) -> None:
    """
    将图表数据转换为标准化的HTML表格结构

    本方法处理多维数据表格的生成逻辑，主要功能包括：
    1. 解析图表元数据生成表格标题
    2. 动态构建表头结构
    3. 生成数据行并计算汇总值
    4. 处理排序逻辑
    5. 应用统一样式规范

    处理流程:
        1. 表格结构初始化
        2. 表头动态生成
        3. 数据行遍历处理
        4. 汇总行计算
        5. 样式统一应用

    参数:
        charts: 图表数据列表，包含图表路径和表格元数据

    异常处理:
        KeyError: 当输入数据缺少必要字段时抛出
        TypeError: 当数据类型不符合预期时抛出
    """
    for chart in charts:
        # ==================================================================
        # 阶段1：数据结构校验
        # ==================================================================
        if not isinstance(chart, dict):
            continue  # 跳过无效图表数据

        # 提取表格配置数据
        table_data: dict = chart.get('tableData', {})
        if not table_data:
            continue  # 无表格数据时跳过

        # ==================================================================
        # 阶段2：表格基础配置
        # ==================================================================
        # 获取表格展示数据
        raw_data = table_data.get('data', {})
        # 配置排序参数
        if table_data.get('sort') in ('asc', 'desc'):
            # 执行排序操作（保留原始数据顺序）
            raw_data = {
                k: raw_data[k]
                for k in sorted(
                    raw_data,
                    key=lambda x: str(x).lower(),
                    reverse=table_data['sort'] == 'desc'
                )
            }

        # ==================================================================
        # 阶段3：表格结构初始化
        # ==================================================================
        # 定义样式模板
        COMMON_STYLE = {
            'padding': '0 10px',
            'vertical-align': 'middle',
            'border-right': 'none',
            'border-left': 'none',
            'border-top': 'none',
            'border-bottom': '1px solid rgb(230, 230, 230)',
            'background-color': 'rgb(255, 255, 255)',
        }

        # 构建样式字符串
        header_style = self._build_style({
            **COMMON_STYLE,
            'height': '50px',
            'font-size': '12px',
            'color': '#8c95a8',
            'border-top': '1px solid rgb(230, 230, 230)',
        })

        row_style = self._build_style({
            **COMMON_STYLE,
            'height': '38px',
            'font-size': '12px',
        })

        total_style = self._build_style({
            **COMMON_STYLE,
            'height': '38px',
            'font-size': '12px',
            'color': 'black',
            'font-weight': 'bold',
        })

        # ==================================================================
        # 阶段4：表头动态生成
        # ==================================================================
        # 提取列标题（首个样本数据键）
        data_headers = []
        if raw_data:
            sample_data = next(iter(raw_data.values()))
            if isinstance(sample_data, dict):
                data_headers = list(sample_data.keys())

        # 构建表头HTML
        header_html = []
        # 添加主分类标题
        header_html.append(f'<th align="left" style="{header_style}">{table_data["firstColumnHeader"]}</th>')
        # 添加小计列
        if table_data.get('isRowTotal'):
            header_html.append(f'<th align="left" style="{header_style}">小计</th>')
        # 添加数据列标题
        header_html.extend(
            f'<th align="left" style="{header_style}">{header}</th>'
            for header in data_headers
        )

        # ==================================================================
        # 阶段5：数据行处理
        # ==================================================================
        data_rows = []
        total_values = [0] * (len(data_headers) + 1)  # 索引0存储小计总计

        for category, values in raw_data.items():
            # 转换值为字典格式（防御性处理）
            value_dict = values if isinstance(values, dict) else {}

            # 计算当前分类小计
            row_total = sum(value_dict.values())
            # 构建数据单元格
            cells = []
            # 添加分类名称
            cells.append(f'<td align="left" style="{row_style}">{category}</td>')
            # 添加小计单元格
            if table_data.get('isRowTotal'):
                cells.append(f'<td align="left" style="{row_style}">{row_total}</td>')
            # 添加各数据项单元格
            cells.extend(
                f'<td align="left" style="{row_style}">{value_dict.get(key, 0)}</td>'
                for key in data_headers
            )
            # 更新总计
            total_values[0] += row_total
            for idx, key in enumerate(data_headers, start=1):
                total_values[idx] += value_dict.get(key, 0)

            data_rows.append(f'<tr>{"".join(cells)}</tr>')

        # ==================================================================
        # 阶段6：总计行构建
        # ==================================================================
        total_cells = []
        # 添加总计标签
        total_cells.append(f'<td align="left" style="{total_style}">总计</td>')
        # 添加小计总计
        if table_data.get('isRowTotal'):
            total_cells.append(f'<td align="left" style="{total_style}">{total_values[0]}</td>')
        # 添加各列总计
        total_cells.extend(
            f'<td align="left" style="{total_style}">{value}</td>'
            for value in total_values[1:]
        )

        # ==================================================================
        # 阶段7：HTML结构组合
        # ==================================================================
        table_html = f'''
        {'<div><br /></div>' * 2}
        <div>
            <table cellpadding="0" cellspacing="0" class="report-chart__table" 
                   style="width:{table_data['tableWidth']}px;border:none;margin-top:0;margin-bottom:0;margin-left:0;margin-right:0;">
                <tbody>
                    <tr>{"".join(header_html)}</tr>
                    {"".join(data_rows)}
                    <tr>{"".join(total_cells)}</tr>
                </tbody>
            </table>
        </div>'''

        self.chartHtml += table_html

        # ==================================================================
        # 阶段8：间隔处理
        # ==================================================================
        # 最后一个图表减少间隔行数
        interval = 5 if chart != charts[-1] else 2
        self.chartHtml += '<div><br /></div>' * interval