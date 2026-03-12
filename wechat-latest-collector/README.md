# wechat-latest-collector

适合分享的微信公众号“最近 N 篇文章发现 + 正文批量采集”工作流 skill。

## 这是什么

这个 skill 不直接抓正文，而是先通过本地 `wechat-article-exporter` 服务拿到某个公众号最近 N 篇文章列表，再可选调用同仓库内的 `wechat-collector` 抓正文。

## exporter 来源

本 skill 依赖一个外部开源项目作为“文章列表发现层”：

- 上游仓库：`https://github.com/wechat-article/wechat-article-exporter`

默认情况下，`scripts/start_exporter_dev.sh` 会在 `WECHAT_EXPORTER_DIR` 不存在时，自动从这个仓库 clone 到本地。

如果你不想让脚本自动拉取外部仓库，也可以：

1. 手动 clone `wechat-article-exporter`
2. 用环境变量把它指到目标目录

例如：

```bash
export WECHAT_EXPORTER_DIR=/your/path/wechat-article-exporter
```

## 特点

- 支持 `article-url -> biz/fakeid -> latest N`
- 支持缓存并复用 `auth-key`
- 支持按需启动 exporter 服务
- 默认优先寻找同仓库里的 `wechat-collector`
- 尽量减少硬编码，支持环境变量覆盖

## 依赖

- Node 22+
- Yarn 1.x
- 本地桌面环境 / VNC（扫码登录时需要）
- 一个可登录的微信公众号后台
- 同仓库中的 `wechat-collector`，或手动指定兼容的 collector 路径

## 默认环境变量

- `WECHAT_EXPORTER_DIR`：exporter 项目目录
- `WECHAT_EXPORTER_PORT`：服务端口（默认 3017）
- `WECHAT_EXPORTER_HOST`：监听地址（默认 0.0.0.0）
- `WECHAT_EXPORTER_BASE_URL`：完整服务地址，优先于端口推导
- `WECHAT_COLLECTOR_PATH`：正文采集脚本路径
- `WECHAT_LATEST_TEMP_DIR`：中间 JSON / URL 列表输出目录

## 快速流程

```bash
cd wechat-latest-collector

# 1) 启动 exporter
bash scripts/start_exporter_dev.sh

# 2) 在桌面/VNC打开页面并扫码
bash scripts/open_exporter_vnc.sh

# 3) 保存 auth-key
python3 scripts/save_auth_key.py "<auth-key>"

# 4) 拉最近 5 篇，并可选采正文
python3 scripts/wechat_latest_collect.py \
  --article-url "https://mp.weixin.qq.com/s/xxxxx" \
  --limit 5 \
  --collect

# 5) 停服务
bash scripts/stop_exporter_dev.sh
```

## 注意

这是环境定制型 skill，不保证别人在零配置环境中直接即用。

请勿提交：
- `state/auth_key.txt`
- `.server.pid`
- `server.log`
- exporter 的本地运行数据
