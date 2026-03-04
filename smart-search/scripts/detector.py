#!/usr/bin/env python3
"""
检测器 - 语言和模式检测
"""
import re
from typing import Optional


# 语言检测关键词
LANGUAGE_PATTERNS = {
    'zh': r'[\u4e00-\u9fff]',  # 中文字符
}

# 模式检测关键词
MODE_KEYWORDS = {
    'financial': [
        '财报', '营收', '利润', '净利润', '营业收入',
        '毛利率', '净利润率', '同比', '增长率',
        'financial', 'revenue', 'profit', 'earnings',
        '股票', 'stock', '股价', 'share'
    ],
    'news': [
        '新闻', '最新', '今天', '昨天', '报道',
        '突发', '发布', '发布会',
        'news', 'latest', 'today', 'breaking'
    ],
    'tech': [
        'API', 'SDK', '文档', '教程', '开发',
        'Python', 'JavaScript', 'Java', 'React',
        'how to', 'how do i', 'tutorial', 'guide'
    ]
}


def detect_language(text: str) -> str:
    """
    检测文本语言

    Args:
        text: 输入文本

    Returns:
        语言代码 ('zh', 'en', 'unknown')
    """
    # 检查中文
    if re.search(LANGUAGE_PATTERNS['zh'], text):
        return 'zh'

    # 默认为英文
    return 'en'


def detect_mode(text: str) -> str:
    """
    检测搜索模式

    Args:
        text: 输入文本

    Returns:
        模式名称 ('financial', 'news', 'tech', 'general')
    """
    text_lower = text.lower()

    # 检查每种模式
    for mode, keywords in MODE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return mode

    # 默认为通用模式
    return 'general'


def detect_mode_confidence(text: str) -> tuple:
    """
    检测搜索模式（带置信度）

    Args:
        text: 输入文本

    Returns:
        (模式名称, 置信度 0-1)
    """
    text_lower = text.lower()

    scores = {}
    for mode, keywords in MODE_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword.lower() in text_lower:
                score += 1
        scores[mode] = score

    # 找最高分
    max_score = max(scores.values())
    if max_score == 0:
        return 'general', 0.0

    best_mode = max(scores, key=scores.get)

    # 计算置信度（简单归一化）
    confidence = min(max_score / 3.0, 1.0)

    return best_mode, confidence


def extract_stock_code(text: str) -> Optional[str]:
    """
    提取股票代码

    Args:
        text: 输入文本

    Returns:
        股票代码或 None
    """
    # 匹配 6 位数字股票代码
    match = re.search(r'\b(\d{6})\b', text)
    if match:
        return match.group(1)

    # 匹配字母数字代码（如 HK00700）
    match = re.search(r'\b([A-Z]{2}\d{5})\b', text)
    if match:
        return match.group(1)

    return None


def extract_year(text: str) -> Optional[int]:
    """
    提取年份

    Args:
        text: 输入文本

    Returns:
        年份或 None
    """
    # 匹配 4 位数字年份
    match = re.search(r'\b(20\d{2})\b', text)
    if match:
        return int(match.group(1))

    return None


if __name__ == '__main__':
    # 测试
    tests = [
        "赛力斯 2024年财报",
        "Tesla latest news",
        "Playwright stealth tutorial",
        "Python 爬虫教程"
    ]

    for test in tests:
        lang = detect_language(test)
        mode = detect_mode(test)
        mode_conf = detect_mode_confidence(test)

        print(f"查询: {test}")
        print(f"  语言: {lang}")
        print(f"  模式: {mode} (置信度: {mode_conf[1]:.2f})")
        print()
