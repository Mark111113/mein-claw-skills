---
name: smart-search
description: 智能搜索技能 - 自动选择最佳搜索引擎（百度/Bing），提取结构化数据。支持中文搜索、英文搜索、财务数据提取、新闻抓取。
---

# Smart Search - 智能搜索技能

## 核心功能

自动检测搜索语言和内容类型，选择最佳搜索引擎，提取结构化数据。

### 特点

- ✅ **自动语言检测** - 中文用百度，英文用 Bing Stealth
- ✅ **智能提取** - 使用 ZAI API 提取结构化数据
- ✅ **多种搜索模式** - 新闻、财经、技术、通用
- ✅ **反爬虫绕过** - Stealth 技术 + Jina AI 回退
- ✅ **结构化输出** - JSON + Markdown

---

## 使用场景

### 1. 财经数据搜索

```bash
python3 smart_search.py "赛力斯 2024年财报" --mode financial
```

输出：
```json
{
  "query": "赛力斯 2024年财报",
  "engine": "baidu",
  "results": [
    {
      "title": "赛力斯2024年财报",
      "revenue": "1451.76亿元",
      "profit": "59.46亿元"
    }
  ]
}
```

### 2. 新闻搜索

```bash
python3 smart_search.py "特斯拉最新新闻" --mode news
```

### 3. 技术搜索

```bash
python3 smart_search.py "nvidia 5090d specs" --mode tech
```

### 4. 通用搜索

```bash
python3 smart_search.py "如何使用 Python 爬虫"
```

---

## 搜索策略

### 语言检测

```python
def detect_language(query: str) -> str:
    """检测查询语言"""
    # 简单启发式：包含中文字符
    if any('\u4e00' <= c <= '\u9fff' for c in query):
        return 'zh'
    return 'en'
```

### 搜索引擎选择

| 语言 | 内容类型 | 引擎 | 方法 |
|------|---------|------|------|
| 中文 | **财经** | **东方财富** | Playwright + 直接访问财报页面 |
| 中文 | 新闻 | 百度 | browser + 百度新闻 |
| 中文 | 通用 | 百度 | browser |
| 英文 | 技术 | Bing Stealth | Playwright |
| 英文 | 通用 | Bing Stealth | Playwright |

### 财经模式（financial）

**特点：**
- 自动识别股票代码（支持公司名称映射）
- 优先访问东方财富获取结构化财务数据
- 失败时自动回退到百度搜索

**支持的公司：**
- 宁德时代 (300750.SZ)
- 中际旭创 (300308.SZ)
- 比亚迪 (002594.SZ)
- 赛力斯 (601127.SH)
- 其他股票可通过6位数字代码自动识别

**提取的指标：**
- 营业总收入
- 归属净利润
- 同比增长率
- 毛利率
- 净利率

**CSS 选择器（东方财富）：**
```python
# 主表格
table_selector = "table"

# 数据行
rows = page.query_selector_all("table tr")

# 单元格提取
for row in rows:
    cells = row.query_selector_all("td")
    key = cells[0].inner_text()   # 指标名称
    value = cells[1].inner_text() # 最新季度数据
```

### 数据提取策略

| 内容类型 | 提取方法 | 工具 |
|---------|---------|------|
| 财务数据 | ZAI API + prompt | zai_coding_extractor.py |
| 新闻内容 | Jina AI Reader | curl |
| 技术文档 | browser snapshot | CDP |
| 通用内容 | 正则表达式 | Python |

---

## 工作流程

### 1. 分析查询

```python
query = "赛力斯 2024年财报"

# 1. 检测语言
language = detect_language(query)  # 'zh'

# 2. 检测内容类型
mode = detect_mode(query)  # 'financial'

# 3. 选择搜索引擎
engine = select_engine(language, mode)  # ('baidu', 'browser')
```

### 2. 执行搜索

```python
# 百度搜索
if engine == 'baidu':
    url = f"https://www.baidu.com/s?wd={quote(query)}"
    html = browser_open(url)

# Bing Stealth 搜索
elif engine == 'bing':
    result = node search-bing-stealth.js query
    html = result['html']
```

### 3. 提取数据

```python
# 财务数据
if mode == 'financial':
    data = zai_extract(html, "提取营业收入、净利润")

# 新闻内容
elif mode == 'news':
    data = jina_extract(url)

# 技术文档
elif mode == 'tech':
    data = browser_snapshot(html)
```

### 4. 格式化输出

```python
# JSON
output = {
    "query": query,
    "engine": engine,
    "mode": mode,
    "results": data
}

save_json(output, f"{query}.json")

# Markdown
save_markdown(data, f"{query}.md")
```

---

## 目录结构

```
smart-search/
├── SKILL.md                      # 技能文档（本文件）
├── references/
│   ├── search-strategies.md      # 搜索策略详细说明
│   ├── extraction-methods.md     # 数据提取方法
│   └── troubleshooting.md        # 故障排除
└── scripts/
    ├── smart_search.py            # 主入口脚本
    ├── detector.py                # 语言/模式检测
    ├── search_baidu.py            # 百度搜索
    ├── search_bing.py             # Bing 搜索
    ├── extractor.py               # 数据提取
    ├── utils.py                   # 工具函数
    └── config.py                  # 配置文件
```

---

## 安装

### 依赖

```bash
# 已安装
- browser 工具（OpenClaw 内置）
- search-bing-stealth.js
- zai_coding_extractor.py

# 可选安装
pip3 install curl-cffi --break-system-packages
```

### 配置

```bash
# 复制示例配置
cp scripts/config.example.py scripts/config.py

# 编辑配置
vim scripts/config.py
```

---

## 快速开始

### 基本使用

```bash
# 自动检测
python3 scripts/smart_search.py "搜索内容"

# 指定模式
python3 scripts/smart_search.py "搜索内容" --mode financial

# 指定引擎
python3 scripts/smart_search.py "search query" --engine bing

# 仅搜索
python3 scripts/smart_search.py "搜索内容" --no-extract

# 保存结果
python3 scripts/smart_search.py "搜索内容" --output ./results
```

### 高级用法

```python
# Python 代码
from smart_search import SmartSearch

searcher = SmartSearch()

# 搜索
results = searcher.search(
    query="赛力斯 2024年财报",
    mode='financial'
)

# 提取
data = searcher.extract(results, 'financial')
```

---

## 搜索模式

### financial（财经）

**检测关键词**：
- 财报、营收、利润、净利润、营业收入
- 股票代码、股票名称
- 财务报告、年度报告

**提取字段**：
- 营业收入
- 净利润
- 毛利率
- 同比增长

**示例**：
```bash
python3 smart_search.py "赛力斯 601127 2024年营收" --mode financial
```

### news（新闻）

**检测关键词**：
- 新闻、最新、今天、昨天
- 事件、发布、报道

**提取字段**：
- 标题
- 来源
- 时间
- 正文摘要

**示例**：
```bash
python3 smart_search.py "特斯拉 最新新闻" --mode news
```

### tech（技术）

**检测关键词**：
- API、文档、教程
- Python、JavaScript、框架
- 问题、how to、如何

**提取字段**：
- 代码示例
- 技术细节
- 参考链接

**示例**：
```bash
python3 smart_search.py "Playwright stealth tutorial" --mode tech
```

---

## 反爬虫策略

### 1. Stealth 技术

```python
# 中文：browser 工具
browser_open(url)

# 英文：Playwright Stealth
node search-bing-stealth.js query
```

### 2. Jina AI Reader 回退

```python
def fallback_extraction(url):
    """当浏览器解析失败时"""
    import requests
    response = requests.get(f"https://r.jina.ai/{url}")
    return response.text
```

### 3. curl-cffi（可选）

```python
from curl_cffi import requests

def cloudflare_bypass(url):
    """绕过 Cloudflare"""
    response = requests.get(url)
    return response.text
```

---

## 输出格式

### JSON

```json
{
  "query": "赛力斯 2024年财报",
  "language": "zh",
  "engine": "baidu",
  "mode": "financial",
  "timestamp": "2026-02-20T01:30:00Z",
  "results": [
    {
      "title": "赛力斯集团2024年年度报告",
      "url": "https://...",
      "data": {
        "revenue": "1451.76亿元",
        "profit": "59.46亿元",
        "growth": "305.04%"
      }
    }
  ]
}
```

### Markdown

```markdown
# 赛力斯 2024年财报

## 搜索信息
- **查询**: 赛力斯 2024年财报
- **引擎**: 百度
- **时间**: 2026-02-20 01:30:00

## 财务数据
- **营业收入**: 1451.76亿元
- **净利润**: 59.46亿元
- **同比增长**: 305.04%

## 来源
- [赛力斯集团2024年年度报告](https://...)
```

---

## 故障排除

### 搜索无结果

**原因**：
1. 关键词不明确
2. 搜索引擎限制

**解决**：
```bash
# 更换关键词
python3 smart_search.py "更具体的关键词"

# 更换引擎
python3 smart_search.py "query" --engine bing
```

### 提取失败

**原因**：
1. 网页结构复杂
2. 反爬虫限制

**解决**：
```bash
# 使用 Jina AI 回退
python3 smart_search.py "query" --fallback jina

# 禁用提取
python3 smart_search.py "query" --no-extract
```

### 百度 CAPTCHA

**原因**：
- 频繁访问

**解决**：
```bash
# 使用 Jina AI
python3 smart_search.py "query" --method jina

# 延迟
python3 smart_search.py "query" --delay 5
```

---

## 最佳实践

1. **明确查询**
   - ✅ "赛力斯 2024年营业收入"
   - ❌ "赛力斯"

2. **指定模式**
   - ```bash
     python3 smart_search.py "赛力斯财报" --mode financial
     ```

3. **保存结果**
   - ```bash
     python3 smart_search.py "query" --output ./results
     ```

4. **批量搜索**
   - ```bash
     cat queries.txt | while read q; do
         python3 smart_search.py "$q" --output ./results
     done
     ```

---

## 性能优化

### 并发搜索

```python
from concurrent.futures import ThreadPoolExecutor

queries = ["query1", "query2", "query3"]

with ThreadPoolExecutor(max_workers=3) as executor:
    results = executor.map(smart_search, queries)
```

### 缓存

```python
import hashlib

def cache_key(query):
    return hashlib.md5(query.encode()).hexdigest()

# 避免重复搜索
if cache_exists(cache_key(query)):
    return load_cache(cache_key(query))
```

---

**最后更新**: 2026-02-20 01:25
