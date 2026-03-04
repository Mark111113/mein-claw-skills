# Archive 目录说明

此目录存放已废弃或过期的脚本和备份文件。

## 归档的脚本

### download_videos_separate.py
**状态：** 已废弃  
**原因：** 被 `video_batch_downloader.py` 替代  
**功能：** 独立视频下载脚本（旧版本）

### test_video_download.py
**状态：** 测试脚本  
**功能：** 用于测试视频下载功能

### xiaohongshu_collector_cmd.py
**状态：** 已废弃  
**原因：** 被 `xiaohongshu_collector.py` 替代  
**功能：** 旧版命令行采集脚本

## backups/ 目录

存放所有 `.backup_*` 文件：
- `video_downloader.py.backup_*`
- `xiaohongshu_collector.py.backup_*`

这些是修改前的备份文件，用于紧急回滚。

---

**注意：** 请勿使用归档目录中的脚本，使用 `../scripts/` 目录中的当前版本。
