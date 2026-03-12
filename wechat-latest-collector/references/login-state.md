# 登录态复用说明（分享版）

## 关键结论

可复用凭据不是“某个浏览器窗口本身”，而是：

- exporter 服务端保存的公众号 cookie/token
- 再加上 API 页面显示的 `auth-key`

所以正确做法不是依赖“助手打开的浏览器”和“用户看到的浏览器”必须是同一个进程，而是：

1. 用真实桌面浏览器 / VNC 浏览器扫码登录
2. 在 API 页面拿到 `auth-key`
3. 立即写入 exporter 项目目录下的状态文件
4. 后续脚本统一从状态文件读取 `auth-key`

## 默认状态文件位置

```bash
$WECHAT_EXPORTER_DIR/state/auth_key.txt
```

默认 `WECHAT_EXPORTER_DIR` 为：

```bash
/root/.openclaw/workspace/projects/wechat-article-exporter
```

## 推荐流程

1. 启动 exporter
2. 用 `scripts/open_exporter_vnc.sh` 打开本地页面
3. 用户扫码登录公众号后台
4. 在 API 页面点击“查询 API 密钥”
5. 运行：

```bash
python3 scripts/save_auth_key.py "<auth-key>"
```

6. 再运行：

```bash
python3 scripts/wechat_latest_collect.py --article-url "https://mp.weixin.qq.com/s/xxxxx" --limit 5
```

## 什么时候需要重新扫码

出现以下任一情况时，视为登录态可能过期：

- `Auth key is invalid or expired`
- `AuthKey not found`
- `认证信息无效`
- 文章列表 API 返回 `ret != 0`

## 安全建议

- `auth-key` 不要提交进 git
- 不要发到群里或公开文档里
- exporter 服务不要暴露到公网
- 不要依赖浏览器进程本身来复用登录态，优先依赖状态文件里的 `auth-key`
