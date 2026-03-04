#!/usr/bin/env python3
"""
小红书视频批量下载器（两步流程第2步）
从已采集的JSON中读取视频信息，串行下载视频

用法:
    python3 video_batch_downloader.py <notes目录路径>
    
示例:
    python3 video_batch_downloader.py /mnt/fn/Download3/clawdbotfile/xiaohongshu/20260225_1430_关键词/notes
"""
import json
import asyncio
import sys
from pathlib import Path
from video_downloader import VideoDownloader


async def download_videos_from_notes(notes_dir: Path):
    """
    从notes目录中的JSON文件读取视频信息并串行下载
    
    Args:
        notes_dir: notes目录路径
    """
    # 查找所有JSON文件
    json_files = list(notes_dir.glob("*.json"))
    
    if not json_files:
        print("❌ 未找到JSON文件")
        return
    
    print(f"📁 找到 {len(json_files)} 个贴子文件")
    
    # 过滤出有视频但未下载的
    videos_to_download = []
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                note_data = json.load(f)
            
            video = note_data.get('video', {})
            # 有视频且未下载（没有local_path）
            if video and video.get('has_video') and not video.get('local_path'):
                note_url = note_data.get('url')
                if note_url:
                    videos_to_download.append({
                        'json_file': json_file,
                        'note_data': note_data,
                        'url': note_url,
                        'title': note_data.get('title', 'untitled')[:30]
                    })
        except Exception as e:
            print(f"⚠️  读取 {json_file.name} 失败: {e}")
    
    if not videos_to_download:
        print("✅ 没有需要下载的视频（已全部下载或无视频）")
        return
    
    print(f"🎬 发现 {len(videos_to_download)} 个待下载视频")
    
    # 创建视频目录
    videos_dir = notes_dir.parent / "videos"
    videos_dir.mkdir(exist_ok=True)
    
    # 创建下载器
    downloader = VideoDownloader()
    
    # 串行下载（避免风控）
    success_count = 0
    failed_count = 0
    
    for i, item in enumerate(videos_to_download, 1):
        print(f"\n{'='*70}")
        print(f"📥 [{i}/{len(videos_to_download)}] {item['title']}")
        print(f"   URL: {item['url'][:80]}...")
        
        try:
            # 提取note_id作为文件名
            note_id = item['url'].split('/explore/')[-1].split('?')[0]
            safe_title = ''.join(c if c.isalnum() or c in '_-' else '_' for c in item['title'])
            filename = f"{note_id}_{safe_title}" if safe_title else note_id
            
            # 下载视频
            result = await downloader.download_from_note_url(
                item['url'],
                videos_dir,
                filename=filename
            )
            
            if result and result.get('local_path'):
                # 更新JSON
                item['note_data']['video']['local_path'] = result['local_path']
                item['note_data']['video']['codec'] = result.get('codec', 'unknown')
                item['note_data']['video']['width'] = result.get('width', 0)
                item['note_data']['video']['height'] = result.get('height', 0)
                item['note_data']['video']['size'] = result.get('size', 0)
                
                with open(item['json_file'], 'w', encoding='utf-8') as f:
                    json.dump(item['note_data'], f, ensure_ascii=False, indent=2)
                
                print(f"   ✅ 下载成功并更新JSON")
                success_count += 1
            else:
                print(f"   ❌ 下载失败")
                failed_count += 1
                
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            failed_count += 1
        
        # 每个视频下载后等待，避免风控
        if i < len(videos_to_download):
            print(f"   ⏳ 等待3秒...")
            await asyncio.sleep(3)
    
    print(f"\n{'='*70}")
    print(f"📊 下载完成:")
    print(f"   ✅ 成功: {success_count}")
    print(f"   ❌ 失败: {failed_count}")
    print(f"📁 视频目录: {videos_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 video_batch_downloader.py <notes目录路径>")
        print("示例: python3 video_batch_downloader.py /mnt/fn/Download3/clawdbotfile/xiaohongshu/20260225_1430_关键词/notes")
        sys.exit(1)
    
    notes_dir = Path(sys.argv[1])
    
    if not notes_dir.exists():
        print(f"❌ 目录不存在: {notes_dir}")
        sys.exit(1)
    
    if not notes_dir.is_dir():
        print(f"❌ 不是目录: {notes_dir}")
        sys.exit(1)
    
    asyncio.run(download_videos_from_notes(notes_dir))
