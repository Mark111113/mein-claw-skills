#!/usr/bin/env python3
"""
小红书视频下载器
从 __INITIAL_STATE__ 提取视频流信息并下载
"""
import asyncio
import httpx
import json
import re
from pathlib import Path
from typing import Optional, Dict, List
from lxml.etree import HTML


class VideoDownloader:
    """小红书视频下载器"""

    INITIAL_STATE = "//script/text()"
    PC_KEYS_LINK = ("note", "noteDetailMap", "[-1]", "note")
    PHONE_KEYS_LINK = ("noteData", "data", "noteData")

    def __init__(self, cookie: str = "", user_agent: str = ""):
        self.cookie = cookie
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self.headers = {
            "User-Agent": self.user_agent,
            "Cookie": self.cookie,
        }

    def _extract_object(self, html: str) -> str:
        """从 HTML 提取 __INITIAL_STATE__"""
        if not html:
            return ""
        html_tree = HTML(html)
        scripts = html_tree.xpath(self.INITIAL_STATE)
        return self._get_script(scripts)

    @staticmethod
    def _get_script(scripts: list) -> str:
        """获取 __INITIAL_STATE__ 脚本内容"""
        # 不要反转列表，直接按顺序查找
        for script in scripts:
            script_str = str(script).strip()
            if script_str.startswith("window.__INITIAL_STATE__"):
                return script_str
        return ""

    @staticmethod
    def _convert_object(text: str) -> dict:
        """将 JSON 格式转为 dict"""
        # 找到第一个 { 或 [ 的位置
        for i, char in enumerate(text):
            if char in '{[':
                json_text = text[i:].rstrip(';').strip()

                # 修复 JavaScript 的 undefined（不是合法JSON）
                # 在字符串外将 undefined 替换为 null
                import re
                # 使用正则替换非字符串内的 undefined
                cleaned = re.sub(r'\bundefined\b', 'null', json_text)

                # 使用括号匹配算法找到完整的JSON对象
                stack = []
                end_idx = 0
                in_string = False
                escape_next = False

                for idx, c in enumerate(cleaned):
                    if escape_next:
                        escape_next = False
                        continue

                    if c == '\\' and in_string:
                        escape_next = True
                        continue

                    if c == '"' and not escape_next:
                        in_string = not in_string
                        continue

                    if not in_string:
                        if c in '{[':
                            stack.append(c)
                        elif c in '}]':
                            if stack:
                                opening = stack[-1]
                                if (c == '}' and opening == '{') or (c == ']' and opening == '['):
                                    stack.pop()
                                    if not stack:
                                        end_idx = idx + 1
                                        break

                if end_idx > 0:
                    final_json = cleaned[:end_idx]
                    return json.loads(final_json)

        raise ValueError("无法找到完整的 JSON 对象")

    @classmethod
    def _filter_object(cls, data: dict) -> dict:
        """提取帖子数据"""
        return (
            cls._deep_get(data, cls.PHONE_KEYS_LINK)
            or cls._deep_get(data, cls.PC_KEYS_LINK)
            or {}
        )

    @classmethod
    def _deep_get(cls, data: dict, keys: list | tuple, default=None):
        """深层获取字典值"""
        if not data:
            return default
        try:
            for key in keys:
                if key.startswith("[") and key.endswith("]"):
                    data = cls._safe_get(data, int(key[1:-1]))
                else:
                    data = data[key]
            return data
        except (KeyError, IndexError, ValueError, TypeError):
            return default

    @staticmethod
    def _safe_get(data, index: int):
        """安全获取列表/字典元素"""
        if isinstance(data, dict):
            return list(data.values())[index]
        elif isinstance(data, list | tuple):
            return data[index]
        raise TypeError

    def parse_html(self, html: str) -> dict:
        """解析 HTML 提取帖子数据"""
        text = self._extract_object(html)
        if not text:
            return {}
        data = self._convert_object(text)
        return self._filter_object(data)

    def get_video_streams(self, data: dict) -> Dict[str, List[dict]]:
        """获取视频流信息"""
        video = data.get("video", {})
        if not video:
            return {}

        media = video.get("media", {})
        stream = media.get("stream", {})

        return {
            "h264": stream.get("h264", []),
            "h265": stream.get("h265", []),
        }

    def get_best_video_url(self, data: dict, prefer_h265: bool = True) -> Optional[str]:
        """获取最佳视频下载链接"""
        streams = self.get_video_streams(data)

        # 优先 h265 (更高分辨率)
        if prefer_h265 and streams.get("h265"):
            # 按分辨率排序，选择最高的
            h265 = sorted(streams["h265"], key=lambda x: x.get("height", 0), reverse=True)
            if h265 and h265[0].get("masterUrl"):
                return h265[0]["masterUrl"]

        # 回退到 h264
        if streams.get("h264"):
            h264 = sorted(streams["h264"], key=lambda x: x.get("height", 0), reverse=True)
            if h264 and h264[0].get("masterUrl"):
                return h264[0]["masterUrl"]

        return None

    def get_video_info(self, data: dict) -> Optional[dict]:
        """获取视频详细信息"""
        streams = self.get_video_streams(data)

        if not streams.get("h264") and not streams.get("h265"):
            return None

        # 获取最高分辨率
        best_stream = None
        best_url = None
        codec = "h264"

        if streams.get("h265"):
            best_stream = max(streams["h265"], key=lambda x: x.get("height", 0))
            best_url = best_stream.get("masterUrl")
            codec = "h265"
        elif streams.get("h264"):
            best_stream = max(streams["h264"], key=lambda x: x.get("height", 0))
            best_url = best_stream.get("masterUrl")

        if not best_stream:
            return None

        return {
            "has_video": True,
            "width": best_stream.get("width", 0),
            "height": best_stream.get("height", 0),
            "duration": data.get("video", {}).get("media", {}).get("duration", 0),
            "video_bitrate": best_stream.get("videoBitrate", 0),
            "size": best_stream.get("size", 0),
            "download_url": best_url,
            "codec": codec,
        }

    async def fetch_page(self, url: str) -> tuple:
        """获取页面内容"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers, follow_redirects=True, timeout=30)
            return resp.status_code, resp.text

    async def download_video(self, url: str, save_path: Path) -> bool:
        """下载视频文件"""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, follow_redirects=True, timeout=120)
                if resp.status_code == 200:
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(save_path, "wb") as f:
                        f.write(resp.content)
                    return True
            except Exception as e:
                print(f"下载失败: {e}")
        return False

    async def download_from_note_url(
        self,
        note_url: str,
        save_dir: Path,
        filename: Optional[str] = None,
    ) -> Optional[dict]:
        """从小红书帖子 URL 下载视频

        Args:
            note_url: 帖子链接（需要包含 xsec_token）
            save_dir: 保存目录
            filename: 文件名（不含扩展名）

        Returns:
            视频信息字典，失败返回 None
        """
        # 获取页面
        status, html = await self.fetch_page(note_url)

        if status != 200 or "404" in html[:500]:
            print(f"页面获取失败: {status}")
            return None

        # 解析数据
        data = self.parse_html(html)
        if not data:
            print("数据解析失败")
            return None

        # 获取视频信息
        video_info = self.get_video_info(data)
        if not video_info:
            print("未找到视频")
            return None

        # 下载视频
        if video_info.get("download_url"):
            note_id = data.get("noteId", "unknown")
            filename = filename or note_id
            save_path = save_dir / f"{filename}.mp4"

            print(f"下载视频: {video_info['width']}x{video_info['height']}")
            print(f"文件大小: {video_info['size'] / 1024 / 1024:.2f} MB")

            success = await self.download_video(video_info["download_url"], save_path)

            if success:
                video_info["local_path"] = str(save_path)
                print(f"✅ 下载成功: {save_path}")
            else:
                print("❌ 下载失败")

        return video_info


# 便捷函数
async def download_xhs_video(
    note_url: str,
    save_dir: str,
    cookie: str = "",
    filename: Optional[str] = None,
) -> Optional[dict]:
    """下载小红书视频

    Args:
        note_url: 帖子链接（需要 xsec_token）
        save_dir: 保存目录
        cookie: Cookie 字符串
        filename: 文件名（不含扩展名）

    Returns:
        视频信息字典
    """
    downloader = VideoDownloader(cookie=cookie)
    return await downloader.download_from_note_url(
        note_url,
        Path(save_dir),
        filename,
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python video_downloader.py <帖子URL> [保存目录]")
        sys.exit(1)

    url = sys.argv[1]
    save_dir = sys.argv[2] if len(sys.argv) > 2 else "/tmp"

    # 从环境变量或 XHS-Downloader 配置获取 cookie
    cookie = ""
    settings_path = Path.home() / ".agents/skills/xiaohongshu/tools/XHS-Downloader/Volume/settings.json"
    if settings_path.exists():
        with open(settings_path) as f:
            settings = json.load(f)
            cookie = settings.get("cookie", "")

    result = asyncio.run(download_xhs_video(url, save_dir, cookie))

    if result:
        print(f"\n视频信息:")
        print(f"  分辨率: {result['width']}x{result['height']}")
        print(f"  编码: {result['codec']}")
        print(f"  大小: {result['size'] / 1024 / 1024:.2f} MB")
        if result.get("local_path"):
            print(f"  本地路径: {result['local_path']}")