---
name: xiaohongshu-collector
description: |
  小红书内容采集器。搜索、采集贴子（标题/内容/图片/评论/视频），支持筛选（时间/排序/类型）。
  使用场景：批量采集小红书内容、舆情分析、内容备份、竞品监控。

  什么时候使用：
  - "采集小红书上关于XX的贴子"
  - "搜索小红书XX关键词并下载"
  - "监控小红书XX话题的讨论"
  - "获取小红书热门内容的数据"
  - "导出小红书贴子（含图片视频）"
---

# 小红书采集器

批量采集小红书贴子，自动下载图片和视频，结构化存储评论。

## 快速开始

```bash
cd /root/.agents/skills/xiaohongshu-collector/scripts

# 基础采集
python3 xiaohongshu_collector.py "关键词" --max 10

# 带筛选的采集
python3 xiaohongshu_collector.py "关键词" --max 5 --note-type video --time-filter 1d
```

## 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `keyword` | 搜索关键词（必需） | - |
| `--max` | 采集数量 | 10 |
| `--sort` | 排序：general/newest/most_likes/most_comments/most_favorites | general |
| `--time-filter` | 时间：1d/7d/180d | 无 |
| `--note-type` | 类型：all/video/image | all |

## 两步流程（推荐）

视频下载采用分离设计，避免浏览器页面限制：

### 第1步：采集数据

```bash
# 采集视频笔记（只标记，不下载视频）
python3 xiaohongshu_collector.py "留园" --max 5 --note-type video

# 组合筛选示例
python3 xiaohongshu_collector.py "苏州" --max 10 --note-type video --time-filter 1d --sort most_likes
```

采集完成后，输出目录结构：
```
/mnt/fn/Download3/clawdbotfile/xiaohongshu/{timestamp}_{关键词}/
├── summary.json          # 汇总信息
├── notes/                # 贴子JSON（包含视频标记）
└── images/               # 图片（已下载）
```

### 第2步：批量下载视频

```bash
# 从notes目录读取视频信息，串行下载
python3 video_batch_downloader.py /mnt/fn/Download3/clawdbotfile/xiaohongshu/{timestamp}_{关键词}/notes
```

下载完成后，更新目录结构：
```
...
├── videos/               # 视频（下载后生成）
│   ├── 001_标题.mp4
│   └── ...
└── notes/                # JSON已更新（添加local_path）
```

### 为什么分两步？

- **可靠性**：浏览器页面加载后 `__INITIAL_STATE__` 可能被移除，独立请求可获取完整数据
- **断点续传**：视频下载失败可重新运行下载脚本
- **避免风控**：串行下载+延迟，降低被封风险

## 登录

**首次使用：**
1. 运行任意采集命令
2. 脚本检测未登录，自动打开VNC登录页
3. 在VNC中扫码登录
4. 终端按回车继续

**登录保持：**
- Cookie保存：`/root/.openclaw/browser-profiles/xiaohongshu/`
- 有效期：7-30天

## 故障排除

| 问题 | 解决 |
|------|------|
| 采集结果为0 | 检查VNC中的登录状态 |
| 视频无法下载 | 确认URL包含`xsec_token`，重新运行下载脚本 |
| 部分评论缺失 | 正常，有些贴子确实无评论 |

## 技术要点

- **搜索**：首页输入关键词 → 回车（避免直接访问搜索URL）
- **筛选**：鼠标悬停"筛选"按钮 → 精确匹配点击选项
- **导航**：JS关闭详情页 → 等待DOM稳定 → 返回列表
- **图片**：requests库HTTP下载（不离开当前页面）
- **视频**：httpx独立请求获取下载链接（避免浏览器HTML限制）
