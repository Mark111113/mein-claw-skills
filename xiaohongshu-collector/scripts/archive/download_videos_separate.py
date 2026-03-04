#!/usr/bin/env python3
"""
独立视频下载脚本
在采集完成后，从已保存的JSON中读取视频贴子URL，然后单独下载视频
"""
import json
import asyncio
import sys
from pathlib import Path
from video_downloader import VideoDownloader

async def download_videos_from_notes(notes_dir: Path, output_dir: Path):
    """
    从notes目录中的JSON文件读取视频信息并下载

    Args:
        notes_dir: notes目录路径
        output_dir: 视频输出目录
    """
    # 创建视频下载器
    downloader = VideoDownloader()

    # 查找所有JSON文件
    json_files = list(notes_dir.glob("*.json"))

    if not json_files:
        print("❌ 未找到JSON文件")
        return

    print(f"📁 找到 {len(json_files)} 个贴子文件")

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    failed_count = 0

    for json_file in json_files:
        try:
            # 读取JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                note_data = json.load(f)

            # 检查是否有视频
            video = note_data.get('video', {})
            if not video or not video.get('has_video'):
                continue

            # 获取贴子URL
            note_url = note_data.get('url')
            if not note_url:
                print(f"⚠️  {json_file.name}: 无URL")
                failed_count += 1
                continue

            # 提取note_id作为文件名
            note_id = note_url.split('/explore/')[-1].split('?')[0]
            safe_title = note_data.get('title', 'untitled')[:30]
            safe_title = ''.join(c if c.isalnum() or c in '_-' else '_' for c in safe_title)

            print(f"\n🎬 处理: {safe_title[:50]}")
            print(f"   URL: {note_url[:80]}...")

            # 下载视频
            result = await downloader.download_from_note_url(
                note_url,
                output_dir,
                filename=f"{note_id}_{safe_title}"
            )

            if result and result.get('local_path'):
                # 更新JSON中的local_path
                note_data['video']['local_path'] = result['local_path']
                note_data['video']['codec'] = result.get('codec', 'unknown')

                # 保存更新后的JSON
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(note_data, f, ensure_ascii=False, indent=2)

                print(f"   ✅ 已下载并更新JSON")
                success_count += 1
            else:
                print(f"   ❌ 下载失败")
                failed_count += 1

        except Exception as e:
            print(f"   ❌ 处理失败: {e}")
            failed_count += 1

    print(f"\n{'='*70}")
    print(f"📊 下载完成:")
    print(f"   ✅ 成功: {success_count}")
    print(f"   ❌ 失败: {failed_count}")
    print(f"📁 输出目录: {output_dir}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='独立下载小红书视频')
    parser.add_argument('notes_dir', help='notes目录路径')
    parser.add_argument('--output', '-o', default='./videos', help='视频输出目录（默认：./videos）')

    args = parser.parse_args()

    notes_dir = Path(args.notes_dir)
    output_dir = Path(args.output)

    if not notes_dir.exists():
        print(f"❌ 目录不存在: {notes_dir}")
        sys.exit(1)

    asyncio.run(download_videos_from_notes(notes_dir, output_dir))
