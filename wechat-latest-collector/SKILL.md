---
name: wechat-latest-collector
description: 微信公众号“最近 N 篇文章”采集技能。用于用户想要“找某个公众号最新 5 篇 / 最近 N 篇 / 根据某篇已知文章继续找同号最近内容”时使用。这个技能依赖本地 `wechat-article-exporter` 服务做文章列表发现，并优先复用同仓库中的 `wechat-collector` 做正文批量采集。适合环境定制型、按需启动的工作流；如果用户已经给了具体文章 URL 列表，优先用 `wechat-collector` 而不是本技能。
---

# 微信公众号最近文章采集器（分享版）

这个技能解决的是：

> 如何从“某个公众号”拿到最近 N 篇文章，再交给正文采集器批量落盘。

它不是纯离线脚本，依赖一个本地服务：`wechat-article-exporter`。

## 什么时候用

优先在这些场景使用：

- “采集某个公众号最近 5 篇”
- “给你一篇这个号的文章，继续找这个号最近几篇”
- “先发现某公众号最近文章，再批量抓正文”

不要优先用于：

- 用户已经给了单篇或多篇文章 URL → 直接用 `wechat-collector`
- 用户想高频、长期、无人值守抓取很多公众号 → 先提醒风控和账号风险

## 前置依赖（重要）

这个 skill 依赖三层：

1. **本地 `wechat-article-exporter` 服务**
2. **该服务里保存的公众号登录态**
3. **该服务项目目录下缓存的 `auth-key`**

没有 exporter 服务在线，就无法完成“按公众号发现最近 N 篇”。

## 目录与默认约定

### exporter 项目目录

默认：

```bash
/root/.openclaw/workspace/projects/wechat-article-exporter
```

可通过环境变量覆盖：

```bash
WECHAT_EXPORTER_DIR=/your/path/wechat-article-exporter
```

### exporter 服务地址

默认：

```bash
http://127.0.0.1:3017
```

可通过参数或环境变量覆盖。

### auth-key 文件

默认：

```bash
$WECHAT_EXPORTER_DIR/state/auth_key.txt
```

### 正文采集器

默认优先查找同仓库里的 sibling skill：

```bash
../wechat-collector/scripts/wechat_collector.py
```

也支持环境变量覆盖：

```bash
WECHAT_COLLECTOR_PATH=/path/to/wechat_collector.py
```

### 中间文件

文章列表发现结果默认写入：

```bash
/root/.openclaw/workspace/temp/
```

可通过环境变量覆盖：

```bash
WECHAT_LATEST_TEMP_DIR=/your/temp/dir
```

## 推荐工作流

### 1. 启动 exporter

```bash
bash scripts/start_exporter_dev.sh
```

### 2. 如果登录态过期，提示用户扫码

当出现以下错误之一时，视为登录态失效：

- `AuthKey not found`
- `认证信息无效`
- `Auth key is invalid or expired`

此时应提示用户：

> 微信公众号登录态已过期。请在桌面/VNC 中打开本地 exporter 页面，点击“登录公众号”重新扫码；扫码后进入左侧 API 页面，点击“查询 API 密钥”，把新的 key 发给我，或让我把它写入本地缓存文件后继续抓取。

可用辅助命令：

```bash
bash scripts/open_exporter_vnc.sh
```

### 3. 保存 auth-key

```bash
python3 scripts/save_auth_key.py "<auth-key>"
```

### 4. 拉最近 N 篇

已知 `__biz`：

```bash
python3 scripts/wechat_latest_collect.py \
  --biz "MzIyNjM2MzQyNg==" \
  --limit 5
```

只有一篇确认属于该公众号的文章：

```bash
python3 scripts/wechat_latest_collect.py \
  --article-url "https://mp.weixin.qq.com/s/xxxxx" \
  --limit 5
```

发现后顺手批量抓正文：

```bash
python3 scripts/wechat_latest_collect.py \
  --article-url "https://mp.weixin.qq.com/s/xxxxx" \
  --limit 5 \
  --collect
```

### 5. 停服务

```bash
bash scripts/stop_exporter_dev.sh
```

## 分享版边界

这是一个**环境定制型 skill**，适合分享 workflow、脚本和经验，不保证别人“零配置即用”。

别人要复用，至少需要：

- 本地能启动 `wechat-article-exporter`
- 有桌面环境或 VNC 可扫码
- 有一个能登录的公众号后台
- 同仓库里有 `wechat-collector`，或自己提供兼容的正文采集脚本

## 成功标准

一次成功的“最新 N 篇采集”至少应满足：

1. exporter 服务正常启动
2. `auth-key` 有效
3. 成功解析到 `biz/fakeid`
4. 成功拿到最近 N 篇文章列表
5. 如果启用 `--collect`，至少大部分文章正文成功落盘
