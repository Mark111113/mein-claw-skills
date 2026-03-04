#!/usr/bin/env python3
"""
提取器 - 数据提取
"""
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

# 添加工具路径
TOOLS_DIR = Path(__file__).parent.parent.parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

# 添加 zai-coding-extractor 技能路径
ZAI_EXTRACTOR_DIR = Path(__file__).parent.parent.parent / "zai-coding-extractor" / "scripts"
if ZAI_EXTRACTOR_DIR.exists():
    sys.path.insert(0, str(ZAI_EXTRACTOR_DIR))

logger = logging.getLogger(__name__)


def extract_data(result: Dict, mode: str) -> Dict[str, Any]:
    """
    根据模式提取数据

    Args:
        result: 搜索结果
        mode: 提取模式

    Returns:
        提取的数据
    """
    if mode == 'financial':
        return extract_financial(result)
    elif mode == 'news':
        return extract_news(result)
    elif mode == 'tech':
        return extract_tech(result)
    else:
        return extract_general(result)


def extract_financial(result: Dict) -> Dict[str, Any]:
    """提取财务数据 - 快速模式，不使用API"""
    import re
    
    title = result.get('title', '')
    snippet = result.get('snippet', '')
    source = result.get('source', '')
    
    # 如果是东方财富来源，直接使用已提取的数据
    if source == 'eastmoney' and 'data' in result and result['data']:
        return {
            "title": title,
            "url": result.get('url', ''),
            "type": "financial",
            "data": result['data'],
            "method": "eastmoney_direct"
        }
    
    # 否则从文本中提取
    text = f"{title} {snippet}"
    
    # 提取数字和单位
    data = {}
    
    # 营收模式
    revenue_match = re.search(r'(?:营收|收入)[\s:：]*(\d+\.?\d*)\s*亿', text)
    if revenue_match:
        data['revenue'] = f"{revenue_match.group(1)}亿元"
    
    # 净利润模式
    profit_match = re.search(r'(?:净利润|归母净利润)[\s:：]*(\d+\.?\d*)\s*亿', text)
    if profit_match:
        data['profit'] = f"{profit_match.group(1)}亿元"
    
    # 增长率模式
    growth_match = re.search(r'同比(?:增长|下降)\s*(\d+\.?\d*)%', text)
    if growth_match:
        direction = '增长' if '增长' in text else '下降'
        data['growth'] = f"{direction}{growth_match.group(1)}%"
    
    # 季度信息
    quarter_match = re.search(r'(202\d)年?[第\s]?(Q?[1234])[季\s]', text)
    if quarter_match:
        data['year'] = quarter_match.group(1)
        data['quarter'] = quarter_match.group(2)
    
    return {
        "title": title,
        "url": result.get('url', ''),
        "type": "financial",
        "data": data,
        "method": "fast"
    }


def extract_news(result: Dict) -> Dict[str, Any]:
    """提取新闻内容"""
    url = result.get('url', '')
    title = result.get('title', '')

    # 使用 Jina AI Reader
    try:
        response = subprocess.run(
            ["curl", "-s", f"https://r.jina.ai/{url}"],
            capture_output=True,
            text=True,
            timeout=15
        )

        if response.returncode == 0:
            content = response.stdout

            # 提取摘要（前 500 字）
            summary = content[:500] + "..." if len(content) > 500 else content

            return {
                "title": title,
                "url": url,
                "type": "news",
                "content": summary,
                "method": "jina"
            }

    except Exception as e:
        logger.error(f"新闻提取失败: {e}")

    # 回退：返回原始摘要
    return {
        "title": title,
        "url": url,
        "type": "news",
        "content": result.get('snippet', ''),
        "method": "fallback"
    }


def extract_tech(result: Dict) -> Dict[str, Any]:
    """提取技术文档 - 快速模式，避免外部请求"""
    url = result.get('url', '')
    title = result.get('title', '')
    snippet = result.get('snippet', '')

    # 直接使用已有数据，避免耗时的 Jina AI 请求
    return {
        "title": title,
        "url": url,
        "type": "tech",
        "content": snippet[:500] if snippet else "",
        "method": "fast"
    }


def extract_general(result: Dict) -> Dict[str, Any]:
    """提取通用内容"""
    return {
        "title": result.get('title', ''),
        "url": result.get('url', ''),
        "type": "general",
        "content": result.get('snippet', ''),
        "method": "snippet"
    }


if __name__ == '__main__':
    # 测试
    test_result = {
        "title": "赛力斯2024年营收1451.76亿元",
        "url": "https://example.com",
        "snippet": "赛力斯集团发布2024年财报..."
    }

    data = extract_financial(test_result)
    print(json.dumps(data, ensure_ascii=False, indent=2))
