processed_data = {'2020-01-01': 1, '2019-01-01': 2, '2021-01-01': 3}
sort_config = 'desc'

processed_data = dict(sorted(
    processed_data.items(),
    key=lambda x: x[0].lower() if isinstance(x[0], str) else x[0],
    reverse=sort_config == 'desc'
))


print(processed_data)