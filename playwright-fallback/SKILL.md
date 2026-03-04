---
name: playwright-fallback
description: Playwright 有头浏览器 Fallback 技能。当 OpenClaw 无头浏览器失败时，自动切换到 Playwright 有头浏览器。支持登录状态保持、内容提取、截图等功能。
---

# Playwright Fallback 技能

**使用场景：**
- OpenClaw 无头浏览器被阻止或失败
- 需要登录的网站（小红书、知乎等）
- 需要保持会话状态
- 反爬虫严格的网站

---

## 🎯 核心功能

### 1. 自动 Fallback 机制

```
OpenClaw 浏览器失败 → Playwright 有头浏览器接管
```

### 2. 持久化登录状态

- 使用 `launchPersistentContext`
- 用户数据目录：`/mnt/fn/Download3/clawdbotfile/playwright-profiles/{project}`
- 首次登录后，后续访问无需重新登录

### 3. VNC 可视化

- 在群晖 VNC 中可以看到浏览器窗口
- 便于调试和手动操作

---

## 🚀 使用方式

### 方法 1: 直接调用工具（推荐）

```python
import sys
sys.path.append('/root/.agents/skills/playwright-fallback/scripts')

from playwright_fallback import PlaywrightFallback

# 创建浏览器实例
browser = PlaywrightFallback(profile_name="xiaohongshu")

try:
    # 启动有头浏览器
    browser.start(headless=False)

    # 访问目标 URL
    browser.goto("http://xhslink.com/o/4Q7mhdNSpjE")

    # 如果需要登录，等待用户手动操作
    if "需要登录" in browser.page.content():
        browser.wait_for_login(timeout=120)

    # 提取内容
    content = browser.extract_content()
    print(f"标题: {content['title']}")
    print(f"URL: {content['url']}")

finally:
    browser.close()
```

### 方法 2: 作为 Fallback 使用

```python
def fetch_with_fallback(url):
    """带 Fallback 的内容获取"""

    # 优先尝试 OpenClaw 浏览器
    try:
        # 使用 browser 工具
        # 如果成功，返回内容
        return content_from_openclaw

    except Exception as e:
        print(f"⚠️ OpenClaw 浏览器失败: {e}")
        print("🔄 切换到 Playwright 有头浏览器...")

        # Fallback 到 Playwright
        browser = PlaywrightFallback(profile_name="fallback")
        browser.start(headless=False)
        browser.goto(url)

        # 检查是否需要登录
        if browser.wait_for_login(timeout=60):
            content = browser.extract_content()
            browser.save_state()
            return content

        finally:
            browser.close()
```

---

## 📁 项目隔离

不同项目使用不同的配置文件，避免状态冲突：

```python
# 小红书项目
browser = PlaywrightFallback(profile_name="xiaohongshu")

# 知乎项目
browser = PlaywrightFallback(profile_name="zhihu")

# 测试项目
browser = PlaywrightFallback(profile_name="test")
```

**用户数据目录：**
```
/mnt/fn/Download3/clawdbotfile/playwright-profiles/xiaohongshu/
/mnt/fn/Download3/clawdbotfile/playwright-profiles/zhihu/
/mnt/fn/Download3/clawdbotfile/playwright-profiles/test/
```

---

## 🔐 登录状态保持

### 首次使用

1. 启动浏览器
2. 访问目标网站
3. 等待用户在 VNC 中扫码登录
4. 状态自动保存

### 后续使用

1. 启动浏览器（使用相同的 profile_name）
2. 访问目标网站
3. **无需重新登录**，Cookie 自动加载

---

## 📸 截图功能

自动截图，保存到 `/tmp/`：

```python
browser.screenshot("after_load")      # 加载后
browser.screenshot("after_login")    # 登录后
browser.screenshot("error")          # 错误时
```

---

## 🛠️ 工具文件

**Python 工具：** `~/.agents/skills/playwright-fallback/scripts/playwright_fallback.py`

**主要类：** `PlaywrightFallback`

**主要方法：**
- `start()` - 启动浏览器
- `goto(url)` - 访问 URL
- `wait_for_login()` - 等待登录
- `extract_content()` - 提取内容
- `screenshot(name)` - 截图
- `save_state()` - 保存状态
- `close()` - 关闭浏览器

---

## 💡 最佳实践

### 1. 何时使用 Playwright Fallback

**优先使用 OpenClaw 浏览器：**
- ✅ 简单的页面访问
- ✅ 不需要登录的网站
- ✅ 批量任务

**使用 Playwright Fallback：**
- ⚠️ OpenClaw 浏览器失败
- ⚠️ 需要登录的网站
- ⚠️ 反爬虫严格
- ⚠️ 需要保持会话

### 2. 状态管理

- 每个项目使用独立的 `profile_name`
- 定期清理过期的配置文件
- 重要状态及时备份

### 3. 错误处理

```python
try:
    browser.start()
    browser.goto(url)
    content = browser.extract_content()
except Exception as e:
    browser.screenshot("error")
    raise
finally:
    browser.close()
```

---

## 🎯 集成到工作流

### 示例：智能搜索

```python
def smart_search(query):
    """智能搜索：优先 OpenClaw，失败则 Fallback"""

    # 尝试 OpenClaw 浏览器 + 百度
    try:
        return search_with_openclaw(query)
    except Exception:
        pass

    # Fallback 到 Playwright + 百度
    browser = PlaywrightFallback(profile_name="search")
    browser.start()

    browser.goto(f"https://www.baidu.com/s?wd={query}")
    content = browser.extract_content()

    browser.close()
    return content
```

---

## 📝 配置要求

**环境要求：**
```bash
# 已安装
export DISPLAY=:0  # VNC 显示

# Playwright 和 Chromium
pip3 install playwright
playwright install chromium
```

**用户权限：**
```bash
# root 用户已授权访问 X Server
su - li -c "xhost +SI:localuser:root"
```

---

**使用前请确保：**
1. ✅ VNC 已启动（群晖管理页面）
2. ✅ DISPLAY 环境变量已设置
3. ✅ Playwright 和 Chromium 已安装
