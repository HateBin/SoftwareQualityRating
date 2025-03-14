a = {'2024-01-11': 'aaaaa', '2024-01-01': 'bbbbb', '2023-04-20': 'aaacs', '2023-04-21': 'aaacs', '空': 'b'}

a.setdefault('空', 'aa')
print(a)