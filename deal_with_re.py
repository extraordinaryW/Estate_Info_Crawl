import re
string = "保证金：\n￥\n2,050,000\n起拍价：\n￥\n20,520,000\n加价幅度：\n￥\n100,000\n评估价：\n￥\n29,313,800\n延时周期：\n5分钟/次\n?\n竞价周期：\n3天\n?\n售后说明：\n不支持七天无理由退货"
string = string.replace(',', '')
# print(string)
start_price_match = re.search(r'起拍价：\n￥\n(\d+)\n', string)
start_price = start_price_match.group(1) if start_price_match else ''
print(start_price)