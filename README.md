# mein-claw-skills

我的 OpenClaw 技能集合

## 📦 包含的技能

### 1. 小红书采集器 (xiaohongshu-collector)
小红书内容采集工具，支持搜索、采集帖子（标题/内容/图片/评论/视频）。

**功能：**
- 搜索关键词采集
- 筛选（时间/排序/类型）
- 导出Markdown和JSON格式
- 采集图片和视频

### 2. 微信采集器 (wechat-collector)
微信公众号文章采集器，支持登录状态持久化。

**功能：**
- 批量采集文章
- 提取图片和内容
- 保存为Markdown和JSON
- 保持登录状态

### 3. 携程机票采集器 (ctrip-flights-collector)
携程机票价格和航班信息采集工具。

**功能：**
- 查询指定航线航班
- 自动滚动加载完整列表
- 输出结构化JSON数据
- 有头浏览器绕过反爬虫

### 4. 智能搜索 (smart-search)
智能搜索引擎选择工具，自动切换百度/Bing获取最佳搜索结果。

**功能：**
- 自动选择最佳搜索引擎
- 中文内容优先使用百度
- 英文内容使用Bing
- 财经数据、新闻等专门模式

### 5. Playwright回退 (playwright-fallback)
有头浏览器自动化工具，当无头浏览器失败时自动切换。

**功能：**
- 有头浏览器模式
- VNC可视化
- 登录状态持久化
- 绕过反爬虫检测

## 🚀 使用方法

每个技能目录下都有 `SKILL.md` 文档，说明详细使用方法。

```bash
# 示例：使用小红书采集器
cd ~/.agents/skills/xiaohongshu-collector
# 详见 SKILL.md
```

## 📋 依赖

- OpenClaw
- Playwright (通过 playwright-fallback 技能)
- Python 3.11+

## ⚠️ 注意事项

- 请遵守各平台的使用条款
- 采集数据仅供个人使用
- 避免频繁请求
- 建议在非高峰期使用

## 📄 许可

MIT License

## 👤 作者

Mark111113

---

**更多 OpenClaw 技能：** [ClawHub](https://clawhub.com)
