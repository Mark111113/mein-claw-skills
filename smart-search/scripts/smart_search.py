#!/usr/bin/env python3
"""
Smart Search - 智能搜索主脚本
自动选择最佳搜索引擎，提取结构化数据
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from detector import detect_language, detect_mode
from extractor import extract_data

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SmartSearch:
    """智能搜索类"""

    def __init__(self, config: Optional[Dict] = None):
        """初始化"""
        self.config = config or {}
        self.results = []

    def search(
        self,
        query: str,
        mode: Optional[str] = None,
        engine: Optional[str] = None,
        extract: bool = True
    ) -> Dict[str, Any]:
        """
        执行智能搜索

        Args:
            query: 搜索关键词
            mode: 搜索模式 (financial, news, tech, general)
            engine: 搜索引擎 (baidu, bing, auto)
            extract: 是否提取数据

        Returns:
            搜索结果字典
        """
        logger.info(f"开始搜索: {query}")

        # 1. 检测语言
        language = detect_language(query)
        logger.info(f"检测语言: {language}")

        # 2. 检测模式
        if not mode:
            mode = detect_mode(query)
        logger.info(f"搜索模式: {mode}")

        # 3. 选择引擎
        if not engine or engine == 'auto':
            engine = self._select_engine(language, mode)
        logger.info(f"搜索引擎: {engine}")

        # 4. 执行搜索
        search_results = self._execute_search(query, engine, mode)
        logger.info(f"搜索结果: {len(search_results)} 条")

        # 5. 提取数据
        extracted_data = []
        if extract:
            for result in search_results:
                data = extract_data(result, mode)
                extracted_data.append(data)

        # 6. 组装结果
        output = {
            "query": query,
            "language": language,
            "engine": engine,
            "mode": mode,
            "timestamp": datetime.now().isoformat(),
            "results": extracted_data if extract else search_results
        }

        return output

    def _select_engine(self, language: str, mode: str) -> str:
        """选择搜索引擎"""
        # 中文用百度
        if language == 'zh':
            return 'baidu'
        # 英文用 Bing Stealth
        elif language == 'en':
            return 'bing'
        else:
            return 'baidu'  # 默认

    def _execute_search(self, query: str, engine: str, mode: str = '') -> List[Dict]:
        """执行搜索"""
        # 财经模式优先使用专业财经网站
        if mode == 'financial':
            return self._search_financial(query)
        
        if engine == 'baidu':
            return self._search_baidu(query)
        elif engine == 'bing':
            return self._search_bing(query)
        else:
            raise ValueError(f"不支持的搜索引擎: {engine}")

    
    def _search_financial(self, query: str) -> List[Dict]:
        """财经数据搜索 - 直接访问东方财富等"""
        import re
        from urllib.parse import quote
        
        logger.info(f"财经模式搜索: {query}")
        
        # 尝试提取股票代码（6位数字）
        stock_code_match = re.search(r'\b(\d{6})\b', query)
        # 尝试匹配已知公司名称
        company_keywords = {
            '宁德时代': {'code': '300750', 'market': 'SZ'},
            '中际旭创': {'code': '300308', 'market': 'SZ'},
            '比亚迪': {'code': '002594', 'market': 'SZ'},
            '赛力斯': {'code': '601127', 'market': 'SH'},
        }
        
        stock_info = None
        if stock_code_match:
            code = stock_code_match.group(1)
            market = 'SH' if code.startswith('6') else 'SZ'
            stock_info = {'code': code, 'market': market}
        else:
            for name, info in company_keywords.items():
                if name in query:
                    stock_info = info
                    break
        
        results = []
        
        # 1. 尝试东方财富
        if stock_info:
            try:
                eastmoney_results = self._search_eastmoney(stock_info, query)
                if eastmoney_results:
                    results.extend(eastmoney_results)
                    logger.info(f"东方财富获取: {len(eastmoney_results)} 条")
            except Exception as e:
                logger.warning(f"东方财富失败: {e}")
        
        # 2. Fallback: 百度搜索
        if not results:
            logger.info("使用百度搜索作为回退")
            return self._search_baidu(query)
        
        return results
    
    def _search_eastmoney(self, stock_info: Dict, query: str) -> List[Dict]:
        """访问东方财富获取财报数据"""
        from playwright.sync_api import sync_playwright
        
        code = stock_info['code']
        market = stock_info['market']
        
        # 东方财富财报页面
        url = f"https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/Index?type=web&code={market}{code}"
        
        logger.info(f"访问东方财富: {url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()
            
            try:
                # 访问页面并等待加载
                page.goto(url, wait_until="networkidle", timeout=30000)
                
                # 等待表格加载（增加等待时间）
                page.wait_for_selector("table", timeout=15000)
                
                # 额外等待 JavaScript 渲染完成
                page.wait_for_timeout(3000)
                
                # 提取主要财务指标
                results = []
                
                # 获取页面标题
                title = page.title()
                
                # 提取表格数据 - 使用正确的选择器
                financial_data = {}
                
                # 获取所有表格行
                rows = page.query_selector_all("table tr")
                
                for row in rows:
                    try:
                        cells = row.query_selector_all("td")
                        if len(cells) >= 2:
                            key = cells[0].inner_text().strip()
                            # 获取最新季度数据（第2列，第1列是表头）
                            value = cells[1].inner_text().strip() if len(cells) > 1 else ""
                            if key and value:
                                financial_data[key] = value
                    except Exception as e:
                        logger.debug(f"提取行数据失败: {e}")
                        continue
                
                # 提取关键财务指标
                key_indicators = {}
                indicator_mapping = {
                    '营业总收入': ['营业总收入', '营业收入'],
                    '归属净利润': ['归属净利润', '净利润'],
                    '同比增长': ['同比增长', '归属净利润同比增长'],
                    '毛利率': ['毛利率'],
                    '净利率': ['净利率']
                }
                
                for std_name, keywords in indicator_mapping.items():
                    for key, value in financial_data.items():
                        if any(kw in key for kw in keywords):
                            key_indicators[std_name] = value
                            break
                
                if key_indicators:
                    results.append({
                        "title": f"{title} - 主要财务指标",
                        "url": url,
                        "snippet": json.dumps(key_indicators, ensure_ascii=False),
                        "source": "eastmoney",
                        "data": key_indicators
                    })
                    logger.info(f"东方财富提取成功: {len(key_indicators)} 个指标")
                else:
                    logger.warning("东方财富未找到关键财务指标")
                
                browser.close()
                return results
                
            except Exception as e:
                browser.close()
                logger.warning(f"东方财富页面解析失败: {e}")
                return []

    def _search_baidu(self, query: str) -> List[Dict]:
        """百度搜索 - 使用 Playwright"""
        from urllib.parse import quote
        import time

        url = f"https://www.baidu.com/s?wd={quote(query)}"
        logger.info(f"访问百度: {url}")

        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                # 使用有头模式，复用已有的浏览器配置
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                # 访问百度
                page.goto(url, wait_until="networkidle", timeout=30000)
                time.sleep(2)
                
                # 提取搜索结果
                results = []
                items = page.query_selector_all(".result, .c-container")
                
                for i, item in enumerate(items[:10]):  # 最多10条
                    try:
                        # 提取标题
                        title_el = item.query_selector("h3 a, .t a, .title a")
                        title = title_el.inner_text() if title_el else ""
                        
                        # 提取链接
                        link_el = item.query_selector("a[href]")
                        link = link_el.get_attribute("href") if link_el else ""
                        
                        # 提取摘要
                        snippet_el = item.query_selector(".c-abstract, .c-span9, .content-right_8Zs40")
                        snippet = snippet_el.inner_text() if snippet_el else ""
                        
                        if title and link:
                            results.append({
                                "title": title.strip(),
                                "url": link,
                                "snippet": snippet.strip()[:500] if snippet else ""
                            })
                    except Exception as e:
                        logger.debug(f"提取结果 {i} 失败: {e}")
                        continue
                
                browser.close()
                
                if results:
                    logger.info(f"百度搜索成功: {len(results)} 条")
                    return results
                    
        except ImportError:
            logger.warning("Playwright 未安装，使用 Jina AI Reader 回退")
        except Exception as e:
            logger.warning(f"Playwright 搜索失败: {e}，使用 Jina AI Reader 回退")

        # 回退方案：使用 Jina AI Reader
        return self._search_jina(url, query)

    def _search_bing(self, query: str) -> List[Dict]:
        import subprocess
        import json

        script_path = SCRIPT_DIR.parent.parent.parent / "tools" / "search-bing-stealth.js"

        if not script_path.exists():
            logger.warning(f"Bing Stealth 脚本不存在: {script_path}")
            return self._search_baidu_fallback(query)

        logger.info(f"使用 Bing Stealth: {query}")

        try:
            result = subprocess.run(
                ["node", str(script_path), query],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get('results', [])
            else:
                logger.error(f"Bing 搜索失败: {result.stderr}")
                return []

        except Exception as e:
            logger.error(f"Bing 搜索异常: {e}")
            return []

    def _search_jina(self, url: str, query: str) -> List[Dict]:
        """使用 Jina AI Reader 作为回退"""
        import subprocess
        
        logger.info(f"Jina AI Reader 回退: {url}")
        
        try:
            result = subprocess.run(
                ["curl", "-s", "-L", f"https://r.jina.ai/{url}"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                # 解析 Jina AI 返回的 Markdown 内容
                content = result.stdout
                lines = content.split('\n')
                
                results = []
                current_title = ""
                current_url = ""
                current_snippet = ""
                
                for line in lines:
                    line = line.strip()
                    # 检测标题行
                    if line.startswith('## ') or line.startswith('### '):
                        if current_title and current_url:
                            results.append({
                                "title": current_title,
                                "url": current_url,
                                "snippet": current_snippet[:500]
                            })
                        current_title = line.lstrip('#').strip()
                        current_snippet = ""
                    # 检测链接
                    elif line.startswith('[') and '](' in line:
                        try:
                            start = line.find('](') + 2
                            end = line.find(')', start)
                            if start > 1 and end > start:
                                current_url = line[start:end]
                        except:
                            pass
                    # 检测 URL 行
                    elif line.startswith('http'):
                        current_url = line
                    else:
                        current_snippet += line + " "
                
                # 添加最后一个结果
                if current_title and current_url:
                    results.append({
                        "title": current_title,
                        "url": current_url,
                        "snippet": current_snippet[:500]
                    })
                
                if results:
                    logger.info(f"Jina AI 解析成功: {len(results)} 条")
                    return results[:10]
                    
        except Exception as e:
            logger.error(f"Jina AI Reader 失败: {e}")
        
        return [{
            "title": f"搜索: {query}",
            "url": url,
            "snippet": "无法提取搜索结果"
        }]

    def _search_baidu_fallback(self, query: str) -> List[Dict]:
        """百度回退搜索"""
        import subprocess

        url = f"https://www.baidu.com/s?wd={query}"
        logger.info(f"百度回退搜索: {url}")

        # 使用 Jina AI Reader
        try:
            result = subprocess.run(
                ["curl", "-s", f"https://r.jina.ai/{url}"],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode == 0:
                return [
                    {
                        "title": f"搜索: {query}",
                        "url": url,
                        "content": result.stdout[:500]
                    }
                ]
        except Exception as e:
            logger.error(f"回退搜索失败: {e}")

        return []


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Smart Search - 智能搜索工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'query',
        help='搜索关键词'
    )

    parser.add_argument(
        '--mode',
        choices=['financial', 'news', 'tech', 'general'],
        default='general',
        help='搜索模式'
    )

    parser.add_argument(
        '--engine',
        choices=['baidu', 'bing', 'auto'],
        default='auto',
        help='搜索引擎'
    )

    parser.add_argument(
        '--no-extract',
        action='store_true',
        help='不提取数据，仅搜索'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='./output',
        help='输出目录'
    )

    parser.add_argument(
        '--format',
        choices=['json', 'markdown', 'both'],
        default='both',
        help='输出格式'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='详细输出'
    )

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 执行搜索
    searcher = SmartSearch()

    try:
        result = searcher.search(
            query=args.query,
            mode=args.mode,
            engine=args.engine,
            extract=not args.no_extract
        )

        # 输出结果
        if args.format in ['json', 'both']:
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            safe_query = "".join(c if c.isalnum() else '_' for c in args.query)
            json_file = output_dir / f"{safe_query}.json"

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            logger.info(f"JSON 已保存: {json_file}")

        if args.format in ['markdown', 'both']:
            # Markdown 输出
            md_content = _format_markdown(result)
            md_file = output_dir / f"{safe_query}.md"

            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(md_content)

            logger.info(f"Markdown 已保存: {md_file}")

        # 控制台输出
        if args.verbose:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"✅ 搜索完成: {args.query}")
            print(f"   引擎: {result['engine']}")
            print(f"   结果: {len(result['results'])} 条")

    except Exception as e:
        logger.error(f"搜索失败: {e}")
        sys.exit(1)


def _format_markdown(data: Dict) -> str:
    """格式化为 Markdown"""
    lines = []

    lines.append(f"# {data['query']}")
    lines.append("")
    lines.append("## 搜索信息")
    lines.append(f"- **查询**: {data['query']}")
    lines.append(f"- **语言**: {data['language']}")
    lines.append(f"- **引擎**: {data['engine']}")
    lines.append(f"- **模式**: {data['mode']}")
    lines.append(f"- **时间**: {data['timestamp']}")
    lines.append("")

    if data['results']:
        lines.append("## 搜索结果")
        lines.append("")

        for i, result in enumerate(data['results'], 1):
            lines.append(f"### {i}. {result.get('title', 'N/A')}")
            lines.append("")

            if 'url' in result:
                lines.append(f"**链接**: [{result['url']}]({result['url']})")
                lines.append("")

            if 'data' in result:
                lines.append("**数据**:")
                lines.append("```json")
                lines.append(json.dumps(result['data'], ensure_ascii=False, indent=2))
                lines.append("```")
                lines.append("")

            elif 'content' in result:
                lines.append("**内容**:")
                lines.append(result['content'][:500])
                lines.append("...")

    return "\n".join(lines)


if __name__ == '__main__':
    main()
