import re

def extract_financial_fast(result):
    """快速财务数据提取 - 不使用API"""
    title = result.get('title', '')
    snippet = result.get('snippet', '')
    text = f"{title} {snippet}"
    
    # 提取数字和单位
    data = {}
    
    # 营收模式：营收/收入 XXX亿元
    revenue_match = re.search(r'(?:营收|收入)[\s:：]*(\d+\.?\d*)\s*亿', text)
    if revenue_match:
        data['revenue'] = f"{revenue_match.group(1)}亿元"
    
    # 净利润模式：净利润/归母净利润 XXX亿元
    profit_match = re.search(r'(?:净利润|归母净利润)[\s:：]*(\d+\.?\d*)\s*亿', text)
    if profit_match:
        data['profit'] = f"{profit_match.group(1)}亿元"
    
    # 增长率模式：同比[增长/下降] XX%
    growth_match = re.search(r'同比(?:增长|下降)\s*(\d+\.?\d*)%', text)
    if growth_match:
        direction = '增长' if '增长' in text else '下降'
        data['growth'] = f"{direction}{growth_match.group(1)}%"
    
    return {
        "title": title,
        "url": result.get('url', ''),
        "type": "financial",
        "data": data,
        "method": "fast"
    }
