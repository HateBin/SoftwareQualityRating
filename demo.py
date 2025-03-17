from collections import defaultdict

BUG_LEVELS = ["致命", "严重", "一般", "提示", "建议"]
b = defaultdict(int, {level: 0 for level in BUG_LEVELS})
b['空'] += 1
print(b)