#!/root/.agents/skills/xiaohongshu-collector/scripts/xiaohongshu_collector.py
"""
小红书话题采集器 - 优化版
视频下载策略：检测到视频时，调用独立的 video_downloader 模块
"""
import sys
import os
import time
import json
import re
import random
import asyncio
from datetime import datetime
from pathlib import Path

os.environ["DISPLAY"] = ":0"

sys.path.insert(0, '/root/.agents/skills/playwright-fallback/scripts')
from playwright_fallback import PlaywrightFallback

# 导入视频下载器
from video_downloader import VideoDownloader, download_xhs_video


class XiaohongshuCollector:
    """小红书话题采集器 - 优化版"""

    def __init__(self, download_video: bool = True):
        self.browser = None
        self.download_video = download_video
        self.video_downloader = None
        self._init_video_downloader()

    def _init_video_downloader(self):
        """初始化视频下载器"""
        # 从 XHS-Downloader 配置获取 cookie
        cookie = ""
        settings_path = Path.home() / ".agents/skills/xiaohongshu/tools/XHS-Downloader/Volume/settings.json"
        if settings_path.exists():
            try:
                with open(settings_path) as f:
                    settings = json.load(f)
                    cookie = settings.get("cookie", "")
            except:
                pass

        if cookie:
            self.video_downloader = VideoDownloader(cookie=cookie)
            print("✅ 视频下载器已初始化")
        else:
            print("⚠️ 未找到 Cookie，视频下载功能不可用")

    def random_sleep(self, min_sec=2, max_sec=5):
        """随机延迟"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
    
    def apply_filters(self, sort="general", time_filter=None, note_type=None, search_range=None, location=None):
        """
        应用筛选条件
        - sort: 排序 (general/latest/most_likes/most_comments/most_collects)
        - time_filter: 时间 (1d/7d/30d/90d/365d)
        - note_type: 笔记类型 (all/video/image)
        - search_range: 搜索范围 (all/viewed/unviewed/followed)
        - location: 位置 (all/local/nearby)
        """
        try:
            # UI 文本映射
            sort_map = {
                'general': '综合',
                'latest': '最新',
                'most_likes': '最多点赞',
                'most_comments': '最多评论',
                'most_collects': '最多收藏'
            }
            time_map = {
                '1d': '一天内',
                '7d': '一周内',
                '30d': '一月内',
                '90d': '三月内',
                '365d': '一年内'
            }
            note_type_map = {
                'all': '不限',
                'video': '视频',
                'image': '图文'
            }
            search_range_map = {
                'all': '不限',
                'viewed': '已看过',
                'unviewed': '未看过',
                'followed': '已关注'
            }
            location_map = {
                'all': '不限',
                'local': '同城',
                'nearby': '附近'
            }
            
            # 鼠标悬停筛选按钮
            print("🖱️  鼠标悬停筛选按钮...")
            
            filter_btn = self.browser.page.get_by_text("筛选").first
            box = filter_btn.bounding_box()
            
            if not box:
                print("⚠️  未找到筛选按钮")
                return
            
            print(f"📍 筛选按钮位置：({box['x']}, {box['y']})")
            
            # 移动到按钮
            self.browser.page.mouse.move(box['x'] - 100, box['y'])
            self.random_sleep(0.5, 1)
            self.browser.page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
            print("✓ 已悬停筛选按钮")
            self.random_sleep(2, 3)
            
            # 依次应用筛选
            filters_applied = []
            
            # 1. 排序依据
            if sort and sort != "general":
                sort_text = sort_map.get(sort, sort)
                if self._click_filter_option(sort_text):
                    filters_applied.append(f"排序：{sort_text}")
                    self.random_sleep(1, 2)
            
            # 2. 笔记类型
            if note_type and note_type != "all":
                type_text = note_type_map.get(note_type, note_type)
                if self._click_filter_option(type_text):
                    filters_applied.append(f"类型：{type_text}")
                    self.random_sleep(1, 2)
            
            # 3. 发布时间
            if time_filter:
                time_text = time_map.get(time_filter, time_filter)
                if self._click_filter_option(time_text):
                    filters_applied.append(f"时间：{time_text}")
                    self.random_sleep(1, 2)
            
            # 4. 搜索范围
            if search_range and search_range != "all":
                range_text = search_range_map.get(search_range, search_range)
                if self._click_filter_option(range_text):
                    filters_applied.append(f"范围：{range_text}")
                    self.random_sleep(1, 2)
            
            # 5. 位置距离
            if location and location != "all":
                location_text = location_map.get(location, location)
                if self._click_filter_option(location_text):
                    filters_applied.append(f"位置：{location_text}")
                    self.random_sleep(1, 2)
            
            if filters_applied:
                print(f"✅ 已应用筛选：{', '.join(filters_applied)}")
                
                # 滚动触发加载
                print("📜 滚动触发加载...")
                for i in range(3):
                    self.browser.page.evaluate("window.scrollBy(0, 800)")
                    self.random_sleep(1, 2)
            else:
                print("⚠️  未应用任何筛选")
                
        except Exception as e:
            print(f"⚠️  应用筛选失败：{e}")
    
    def _click_filter_option(self, filter_text):
        """查找并点击筛选选项"""
        try:
            result = self.browser.page.evaluate(f"""
                () => {{
                    const all = Array.from(document.querySelectorAll('*'));
                    const target = all.find(el => {{
                        const text = (el.textContent || '').trim();
                        const rect = el.getBoundingClientRect();
                        return text.includes('{filter_text}') && 
                               rect.y > 100 && rect.y < 1000 && 
                               rect.width > 20 && rect.height > 15;
                    }});
                    if (target) {{
                        const rect = target.getBoundingClientRect();
                        return {{ found: true, x: rect.left + rect.width/2, y: rect.top + rect.height/2 }};
                    }}
                    return {{ found: false }};
                }}
            """)
            
            if result.get('found'):
                self.browser.page.mouse.move(result['x'], result['y'])
                self.random_sleep(0.5, 1)
                self.browser.page.mouse.click(result['x'], result['y'])
                print(f"✓ 已点击：{filter_text}")
                return True
            else:
                print(f"⚠️  未找到：{filter_text}")
                return False
        except Exception as e:
            print(f"⚠️  点击失败：{e}")
            return False

    def search_and_collect(self, keyword, max_notes=10, sort="general", time_filter=None, 
                          note_type=None, search_range=None, location=None):
        """
        搜索并采集小红书贴子
        """
        print("\n" + "="*70)
        print(f"🔍 小红书话题采集：{keyword}")
        if sort != "general":
            print(f"📊 排序：{sort}")
        if time_filter:
            print(f"📅 时间筛选：{time_filter}")
        if note_type:
            print(f"📝 笔记类型：{note_type}")
        if search_range:
            print(f"🔍 搜索范围：{search_range}")
        if location:
            print(f"📍 位置距离：{location}")
        print("="*70)

        # 创建保存目录
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        safe_keyword = re.sub(r'[^\w\u4e00-\u9fff]+', '_', keyword)
        save_dir = f"/mnt/fn/Download3/clawdbotfile/xiaohongshu/{timestamp}_{safe_keyword}"

        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 保存目录：{save_dir}")

        notes_dir = save_path / "notes"
        images_dir = save_path / "images"
        videos_dir = save_path / "videos"
        notes_dir.mkdir(exist_ok=True)
        images_dir.mkdir(exist_ok=True)
        videos_dir.mkdir(exist_ok=True)

        # 创建浏览器
        self.browser = PlaywrightFallback(profile_name="xiaohongshu")
        self.browser.start(headless=False)

        try:
            # 构建搜索 URL
            base_url = "https://www.xiaohongshu.com/search_result"
            search_url = f"{base_url}?keyword={keyword}&type=54"

            if sort != "general":
                search_url += f"&sort={sort}"

            print(f"\n🔍 搜索：{keyword}")
            self.browser.page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            self.random_sleep(3, 5)

            # 检查是否需要安全验证
            current_url = self.browser.page.url
            page_title = self.browser.page.title()

            if 'captcha' in current_url or '验证' in page_title:
                print("")
                print("=" * 50)
                print("⚠️  需要安全验证")
                print("=" * 50)
                print("")
                print("📱 请在 VNC 中完成验证（端口 5900）")
                print("🔄 自动等待验证完成（最多 120 秒）...")
                print("")

                # 自动等待验证完成（轮询检查）
                max_wait = 120
                check_interval = 3
                waited = 0

                while waited < max_wait:
                    self.random_sleep(check_interval, check_interval)
                    waited += check_interval

                    current_url = self.browser.page.url
                    page_title = self.browser.page.title()

                    if 'captcha' not in current_url and '验证' not in page_title:
                        print(f"\n✅ 验证已完成！（等待 {waited} 秒）\n")
                        break
                    else:
                        print(f"   ⏳ 等待验证完成... ({waited}/{max_wait} 秒)", end='\r')

                if waited >= max_wait:
                    print("\n❌ 验证超时，可能未完成")
                    return {"save_dir": save_dir, "total_notes": 0, "notes": []}

                # 重新访问搜索页
                self.browser.page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                self.random_sleep(3, 5)

            # 应用筛选条件
            if any([sort != "general", time_filter, note_type, search_range, location]):
                print(f"\n📅 应用筛选条件...")
                self.apply_filters(sort=sort, time_filter=time_filter, note_type=note_type, 
                                  search_range=search_range, location=location)
            
            # 滚动加载所有内容
            print("📜 滚动加载内容...")
            for i in range(5):
                self.browser.page.evaluate("window.scrollBy(0, 800)")
                self.random_sleep(2, 3)
