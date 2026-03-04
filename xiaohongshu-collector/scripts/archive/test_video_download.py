import asyncio
import sys
from video_downloader import VideoDownloader
from pathlib import Path

async def test_download():
    # 使用一个已知有视频的帖子
    test_url = "https://www.xiaohongshu.com/explore/679f6bbe000000002503deb2?xsec_token=ABWErcFDKJ7eE1psYaQvDN9zrgRHYBzkAI81suEBBleag=&xsec_source=pc_search&source=web_explore_feed"
    
    downloader = VideoDownloader()
    save_path = Path("/tmp/test_video.mp4")
    
    print("📥 测试视频下载...")
    print(f"URL: {test_url}")
    
    # 先获取页面
    status, html = await downloader.fetch_page(test_url)
    print(f"页面状态: {status}")
    
    # 解析数据
    data = downloader.parse_html(html)
    video_info = downloader.get_video_info(data)
    
    if video_info:
        print(f"\n🎬 视频信息:")
        print(f"  分辨率: {video_info.get('width')}x{video_info.get('height')}")
        print(f"  编码: {video_info.get('codec')}")
        print(f"  大小: {video_info.get('size', 0) / 1024 / 1024:.2f} MB")
        print(f"  下载URL: {video_info.get('download_url', 'None')[:80]}...")
        
        # 下载测试
        if video_info.get('download_url'):
            print(f"\n📥 开始下载...")
            success = await downloader.download_video(video_info['download_url'], save_path)
            
            if success:
                import os
                size = os.path.getsize(save_path) / 1024 / 1024
                print(f"✅ 下载成功！")
                print(f"   文件: {save_path}")
                print(f"   大小: {size:.2f} MB")
            else:
                print(f"❌ 下载失败")
        else:
            print(f"⚠️  无下载链接")
    else:
        print(f"❌ 未找到视频信息")

asyncio.run(test_download())
