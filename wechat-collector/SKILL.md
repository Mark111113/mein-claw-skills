---
name: wechat-collector
description: |
  微信公众号文章采集器。支持登录状态持久化，可批量采集文章、提取图片和内容，保存为Markdown和JSON格式。

  使用场景：
  - 采集微信公众号文章
  - 保存文章内容供后续分析
  - 批量采集文章列表
  - 提取文章中的文本和图片

  什么时候使用：
  - "采集这篇微信文章"
  - "下载微信公众号文章"
  - "批量采集微信文章"
  - "保存微信文章内容"
---

# 微信公众号文章采集器

采集微信公众号文章，自动处理人机验证，支持登录状态持久化和批量采集。

## 快速开始

```bash
cd /root/.agents/skills/wechat-collector/scripts

# 采集单篇文章
python3 wechat_collector.py "https://mp.weixin.qq.com/s/xxxxx"

# 批量采集（多个URL）
python3 wechat_collector.py "url1" "url2" "url3"

# 指定输出目录
python3 wechat_collector.py "https://mp.weixin.qq.com/s/xxxxx" --output /path/to/output

# 只提取不保存（测试模式）
python3 wechat_collector.py "https://mp.weixin.qq.com/s/xxxxx" --dry-run
```

## 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | 微信文章URL（必需） | - |
| `--output` | 输出目录 | `/mnt/fn/Download3/clawdbotfile/wechat` |
| `--dry-run` | 测试模式（不保存文件） | false |
| `--no-screenshot` | 不保存截图 | false |
| `--timeout` | 等待验证超时时间（秒） | 120 |

## 核心特性

### 1. 登录状态持久化

使用 Playwright persistent context 保持登录状态：

- **Profile名称：** `wechat_articles`
- **本地存储：** `/root/.openclaw/browser-profiles/wechat_articles/`
- **NAS备份：** `/mnt/fn/Download3/clawdbotfile/playwright-profiles/wechat_articles/`

**首次使用：**
1. 运行采集命令
2. 脚本自动打开有头浏览器
3. 手动完成人机验证
4. 验证通过后自动采集
5. Cookie自动保存到profile

**后续使用：**
- 无需手动验证
- 直接使用保存的Cookie
- 自动批量采集

### 2. 智能验证检测

脚本会自动检测验证状态，无需手动干预：

```python
# 检测URL变化（包含poc_token说明验证通过）
if "poc_token" in current_url:
    verified = True

# 检测页面内容变化
if "环境异常" not in content and len(content) > 5000:
    verified = True
```

### 3. 批量采集

支持一次采集多篇文章：

```bash
# 方法1：命令行参数
python3 wechat_collector.py "url1" "url2" "url3"

# 方法2：从文件读取
python3 wechat_collector.py @urls.txt
```

### 4. 内容提取

自动提取和清理文章内容：

- 移除HTML标签（script, style, noscript）
- 清理多余空白行
- 提取文章标题和正文
- 保存为Markdown格式
- 保存原始JSON数据

## 输出格式

### 文件结构

```
{timestamp}_{标题}.md
{timestamp}_{标题}.json
```

### Markdown格式

```markdown
# 文章标题

**URL:** https://mp.weixin.qq.com/s/xxxxx
**采集时间:** 2026-03-04 16:51:35
**检测耗时:** 6 秒

---

文章正文内容...
```

### JSON格式

```json
{
  "title": "文章标题",
  "url": "https://mp.weixin.qq.com/s/xxxxx",
  "content": "文章内容...",
  "html": "原始HTML..."
}
```

## 登录管理

### 检查登录状态

```bash
# 查看profile目录
ls -la /root/.openclaw/browser-profiles/wechat_articles/

# 检查Cookie文件
ls -lh /root/.openclaw/browser-profiles/wechat_articles/Default/Cookies
```

### 清除登录状态

```bash
# 删除profile（下次需要重新验证）
rm -rf /root/.openclaw/browser-profiles/wechat_articles
rm -rf /mnt/fn/Download3/clawdbotfile/playwright-profiles/wechat_articles
```

### 备份/恢复登录状态

```bash
# 备份
cp -r /root/.openclaw/browser-profiles/wechat_articles /root/.openclaw/browser-profiles/wechat_articles.backup

# 恢复
cp -r /root/.openclaw/browser-profiles/wechat_articles.backup /root/.openclaw/browser-profiles/wechat_articles
```

## 故障排除

| 问题 | 解决 |
|------|------|
| 采集结果为空 | 检查URL是否正确，是否在浏览器中能看到内容 |
| 需要验证 | 首次使用需要手动验证，后续自动使用保存的Cookie |
| Cookie过期 | 删除profile重新验证 |
| 浏览器无法启动 | 检查DISPLAY环境变量是否设置为:0 |
| 内容不完整 | 等待时间不够，增加--timeout参数 |

## 技术实现

**依赖：**
- `playwright` - 浏览器自动化
- `playwright-fallback` - 登录状态持久化
- `beautifulsoup4` - HTML解析
- `requests` - HTTP请求

**关键代码：**

```python
# 启动浏览器（使用persistent context）
browser = PlaywrightFallback(profile_name="wechat_articles")
browser.start(headless=True)  # 后续使用可无头模式

# 访问文章
browser.goto(url)

# 智能检测验证状态
for _ in range(timeout // 2):
    if "poc_token" in page.url or len(page.content()) > 5000:
        break
    time.sleep(2)

# 提取内容
content = browser.extract_content()
```

## 使用示例

### 示例1：采集单篇文章

```bash
python3 wechat_collector.py "https://mp.weixin.qq.com/s/0R6bZenvL9NTNE8eLciZRg"
```

输出：
```
✅ 提取成功！内容长度: 15234 字符
✅ 文章已保存:
   📄 /root/.openclaw/workspace/temp/微信多Agent配置指南_20260304_164131.md
   📋 /root/.openclaw/workspace/temp/微信多Agent配置指南_20260304_164131.json
   💾 /mnt/fn/Download3/clawdbotfile/微信多Agent配置指南_20260304_164131.md
```

### 示例2：批量采集

```bash
# 创建URL列表文件
cat > urls.txt << EOF
https://mp.weixin.qq.com/s/xxxxx1
https://mp.weixin.qq.com/s/xxxxx2
https://mp.weixin.qq.com/s/xxxxx3
EOF

# 批量采集
python3 wechat_collector.py @urls.txt
```

### 示例3：集成到工作流

```python
import sys
sys.path.append('/root/.agents/skills/wechat-collector/scripts')

from wechat_collector import WeChatCollector

# 创建采集器
collector = WeChatCollector()

# 采集文章
result = collector.collect("https://mp.weixin.qq.com/s/xxxxx")

if result['success']:
    print(f"文章已保存: {result['files']['md']}")
```

## 最佳实践

1. **首次使用：** 在有显示器的环境（VNC或物理显示器）完成首次验证
2. **批量采集：** 使用同一profile采集，避免重复验证
3. **定期备份：** 定期备份wechat_articles profile到安全位置
4. **错误处理：** 检查返回的success字段，处理失败情况
5. **速率限制：** 避免短时间内大量请求，建议间隔5-10秒

## 注意事项

⚠️ **反爬虫机制：**
- 微信公众号有严格的反爬虫措施
- 建议使用有头模式完成首次验证
- 避免频繁请求同一账号的文章

⚠️ **Cookie有效期：**
- Cookie通常7-30天有效
- 过期后需要重新验证
- 建议定期使用保持Cookie活跃

⚠️ **内容版权：**
- 采集的内容仅供个人学习使用
- 请遵守微信公众号的服务条款
- 未经授权不得用于商业用途

## 相关技能

- `xiaohongshu-collector` - 小红书内容采集器（类似实现）
- `search` - 智能搜索技能（搜索微信文章）
- `powerpoint-automation` - 将文章转换为PPT
