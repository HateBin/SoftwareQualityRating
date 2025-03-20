def _add_multi_dimensional_table_html(self, table_data: dict) -> None:
    """
    生成多维数据表格的HTML结构，支持动态列头和行统计功能

    该方法通过解析多维字典数据，自动构建包含列头、数据行和总计行的复杂HTML表格。
    特别适用于展示多维度交叉统计结果，支持自动计算行总计和列总计。

    参数:
        table_data (dict): 包含表格配置和数据的字典，结构示例：
            {
                'tableWidth': 1000,       # 表格总宽度(像素)
                'data': {                 # 核心数据字典
                    '平台A': {'类型1': 5, '类型2': 3},
                    '平台B': {'类型1': 2, '类型2': 7}
                },
                'firstColumnHeader': '软件平台',  # 首列标题文本
                'isRowTotal': True        # 是否显示行总计列
            }

    返回:
        None: 直接更新实例的chartHtml属性

    实现流程:
        1. 提取数据列头信息
        2. 定义表格样式体系
        3. 构建表格数据行HTML
        4. 计算并生成总计行数据
        5. 组合完整表格HTML结构
    """
    # ==================================================================
    # 阶段1：数据列头提取
    # ==================================================================
    # 从首行数据值中提取列头信息（动态适应数据结构）
    data_headers = []
    for value_data in table_data['data'].values():
        data_headers = list(value_data.keys())  # 提取内部字典的键作为列头
        break  # 仅需获取第一个元素的键集合

    # ==================================================================
    # 阶段2：表格样式体系定义
    # ==================================================================
    # 通用单元格样式配置（基础边框和间距设置）
    common_style = {
        'padding': '0 10px',
        'vertical-align': 'middle',
        'border-right': 'none',
        'border-left': 'none',
        'border-top': 'none',
        'border-bottom': '1px solid rgb(230, 230, 230)',
        'background-color': 'rgb(255, 255, 255)',
    }

    # 表头行特定样式（增加顶部边框和文字颜色）
    header_row_style = style_convert({
        **common_style,
        'height': '50px',
        'font-size': '12px',
        'color': '#8c95a8',
        'border-top': '1px solid rgb(230, 230, 230)',
    })

    # 数据行通用样式（标准行高和字体）
    row_style = style_convert({
        **common_style,
        'height': '38px',
        'font-size': '12px',
    })

    # 总计行强调样式（加粗字体和深色文字）
    total_row_style = style_convert({
        **common_style,
        'height': '38px',
        'font-size': '12px',
        'color': 'black',
        'font-weight': 'bold',
    })

    # ==================================================================
    # 阶段3：数据行HTML生成
    # ==================================================================
    data_row_html = ''  # 初始化数据行HTML容器
    total_row_values = [0] * (len(data_headers) + 1)  # 初始化总计行数值容器[行小计, 列1, 列2...]

    # 遍历每个主分类的数据条目（如不同平台的数据）
    for table_key, table_data_dict in table_data['data'].items():
        # 构建单行数据单元格
        row_cells = []
        current_row_total = 0  # 当前行小计

        # 遍历每个子分类的数据值（如不同缺陷类型）
        for header in data_headers:
            cell_value = table_data_dict.get(header, 0)
            row_cells.append(f'<td align="left" style="{row_style}">{cell_value}</td>')
            current_row_total += cell_value

        # 添加行小计单元格（根据配置决定是否显示）
        if table_data.get('isRowTotal'):
            row_cells.insert(1, f'<td align="left" style="{row_style}">{current_row_total}</td>')

        # 累积到总计行数值
        total_row_values[0] += current_row_total  # 行小计累计
        for idx, val in enumerate(table_data_dict.values()):
            total_row_values[idx + 1] += val  # 各列数值累计

        # 组装完整数据行HTML
        data_row_html += f'''
        <tr>
            <td align="left" style="{row_style}">{table_key}</td>
            {''.join(row_cells)}
        </tr>'''

    # ==================================================================
    # 阶段4：表头与总计行构建
    # ==================================================================
    # 生成动态列头HTML
    header_cells = []
    if table_data.get('isRowTotal'):
        header_cells.append(f'<th align="left" style="{header_row_style}">小计</th>')
    header_cells.extend(
        f'<th align="left" style="{header_row_style}">{header}</th>'
        for header in data_headers
    )

    # 生成总计行HTML
    total_cells = []
    if table_data.get('isRowTotal'):
        total_cells.append(f'<td align="left" style="{total_row_style}">{total_row_values[0]}</td>')
    total_cells.extend(
        f'<td align="left" style="{total_row_style}">{val}</td>'
        for val in total_row_values[1:]
    )

    # ==================================================================
    # 阶段5：完整表格组装
    # ==================================================================
    self.chartHtml += f'''
    {'<div><br /></div>' * 2}
    <div>
        <table cellpadding="0" cellspacing="0" class="report-chart__table" 
               style="width:{table_data['tableWidth']}px;border:none;margin:0;">
            <tbody>
                <tr>
                    <th align="left" style="{header_row_style}">
                        {table_data['firstColumnHeader']}
                    </th>
                    {''.join(header_cells)}
                </tr>
                {data_row_html}
                <tr>
                    <td align="left" style="{total_row_style}">总计</td>
                    {''.join(total_cells)}
                </tr>
            </tbody>
        </table>
    </div>'''