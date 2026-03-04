#!/usr/bin/env python3
"""
Playwright 有头浏览器包装器（修复版）
作为 OpenClaw 浏览器的 Fallback

注意：由于 NAS 文件系统不支持文件锁，Profile 保存到本地
"""
import os
import sys
import json
import time
import shutil
from pathlib import Path
from datetime import datetime

# 设置 DISPLAY
os.environ["DISPLAY"] = ":0"

try:
    from playwright.sync_api import sync_playwright, BrowserContext
    print("✓ Playwright 已安装")
except ImportError:
    print("✗ Playwright 未安装")
    print("请运行: pip3 install playwright && playwright install chromium")
    sys.exit(1)


class PlaywrightFallback:
    """Playwright 有头浏览器 Fallback 类"""

    def __init__(self, profile_name="default"):
        """
        初始化浏览器

        Args:
            profile_name: 配置文件名称（用于隔离不同项目的状态）
        """
        self.profile_name = profile_name

        # 由于 NAS 文件系统不支持 Chromium 文件锁，使用本地存储
        # 但提供备份/恢复功能到 NAS
        local_dir = Path("/root/.openclaw/browser-profiles")
        local_dir.mkdir(parents=True, exist_ok=True)

        self.user_data_dir = str(local_dir / profile_name)

        # NAS 备份路径
        self.nas_backup_dir = f"/mnt/fn/Download3/clawdbotfile/playwright-profiles/{profile_name}"

        self.browser = None
        self.context = None
        self.page = None

        print(f"📱 使用配置: {profile_name}")
        print(f"📁 本地数据: {self.user_data_dir}")
        print(f"💾 NAS 备份: {self.nas_backup_dir}")

        # 启动时尝试从 NAS 恢复
        self._restore_from_nas()

    def _restore_from_nas(self):
        """从 NAS 恢复 profile（智能策略）"""
        nas_path = Path(self.nas_backup_dir)
        local_path = Path(self.user_data_dir)

        # 确保 NAS 目录存在
        if not nas_path.exists():
            nas_path.mkdir(parents=True, exist_ok=True)
            return False

        # 智能恢复策略：
        # 1. 本地不存在时，从 NAS 恢复
        # 2. 本地存在但为空时，从 NAS 恢复
        # 3. 本地存在且有数据时，检查 Cookies 时间戳，优先用新的
        
        if not local_path.exists():
            # 本地不存在，从 NAS 恢复
            if nas_path.exists() and list(nas_path.iterdir()):
                print("🔄 从 NAS 恢复配置（本地不存在）...")
                shutil.copytree(nas_path, local_path, dirs_exist_ok=True)
                print("✓ 配置已恢复")
                return True
            return False
        
        # 本地存在，检查是否为空
        local_files = list(local_path.iterdir()) if local_path.exists() else []
        if not local_files:
            # 本地为空，从 NAS 恢复
            if nas_path.exists() and list(nas_path.iterdir()):
                print("🔄 从 NAS 恢复配置（本地为空）...")
                shutil.copytree(nas_path, local_path, dirs_exist_ok=True)
                print("✓ 配置已恢复")
                return True
            return False
        
        # 本地有数据，检查 Cookies 文件时间戳
        local_cookies = local_path / "Default" / "Cookies"
        nas_cookies = nas_path / "Default" / "Cookies"
        
        use_nas = False
        if local_cookies.exists() and nas_cookies.exists():
            # 比较时间戳，优先用新的
            local_time = local_cookies.stat().st_mtime
            nas_time = nas_cookies.stat().st_mtime
            
            if nas_time > local_time:
                use_nas = True
                print(f"🔄 NAS Cookies 更新 ({nas_time:.0f} > {local_time:.0f})，从 NAS 恢复...")
            else:
                print(f"✓ 本地 Cookies 更新 ({local_time:.0f} > {nas_time:.0f})，使用本地数据")
        elif not local_cookies.exists() and nas_cookies.exists():
            # 本地没有 Cookies，从 NAS 恢复
            use_nas = True
            print("🔄 本地无 Cookies，从 NAS 恢复...")
        
        if use_nas:
            try:
                shutil.copytree(nas_path, local_path, dirs_exist_ok=True)
                print("✓ 配置已恢复")
                return True
            except Exception as e:
                print(f"⚠️ 恢复失败: {e}")
                return False
        
        print("✓ 使用本地配置（保留登录状态）")
        return False

    def _backup_to_nas(self):
        """备份 profile 到 NAS"""
        local_path = Path(self.user_data_dir)
        nas_path = Path(self.nas_backup_dir)

        if not local_path.exists():
            return False

        try:
            # 确保 NAS 目录存在
            nas_path.mkdir(parents=True, exist_ok=True)

            # 复制到 NAS（排除锁定文件）
            import subprocess
            result = subprocess.run([
                "rsync", "-av",
                "--exclude=SingletonLock",
                "--exclude=SingletonSocket",
                "--exclude=SingletonCookie",
                f"{local_path}/",
                f"{nas_path}/"
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✓ 配置已备份到 NAS")
                return True
            else:
                print(f"⚠️ 备份警告: {result.stderr}")
                return False

        except Exception as e:
            print(f"⚠️ 备份失败: {e}")
            return False

    def start(self, headless=False, viewport={"width": 1280, "height": 800}):
        """
        启动浏览器

        Args:
            headless: 是否无头模式（默认 False，有头）
            viewport: 视口大小
        """
        print(f"\n=== 启动 Playwright 浏览器 ===")
        print(f"模式: {'有头' if not headless else '无头'}")
        print(f"视口: {viewport}")

        self.playwright = sync_playwright().start()

        # 使用持久化上下文（保持登录状态）
        self.context = self.playwright.chromium.launch_persistent_context(
            self.user_data_dir,
            headless=headless,
            viewport=viewport,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
            ]
        )

        # pages 是属性，不是方法
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()
        print("✓ 浏览器已启动")
        print("✓ 你可以在 VNC 中看到浏览器窗口")

        return self.page

    def goto(self, url, wait_until="networkidle", timeout=30000):
        """
        访问 URL

        Args:
            url: 目标 URL
            wait_until: 等待条件
            timeout: 超时时间（毫秒）

        Returns:
            页面对象
        """
        print(f"\n🌐 访问: {url}")

        try:
            self.page.goto(url, wait_until=wait_until, timeout=timeout)
            print(f"✓ 页面标题: {self.page.title()}")

            # 截图保存
            self.screenshot("after_load")

            return self.page

        except Exception as e:
            print(f"✗ 访问失败: {e}")
            self.screenshot("error")
            raise

    def wait_for_login(self, timeout=120):
        """
        等待用户手动登录

        Args:
            timeout: 等待时间（秒）
        """
        print(f"\n⏳ 等待登录（{timeout} 秒）...")
        print("   请在 VNC 中扫码或输入账号密码")
        print("   登录成功后，页面会自动跳转\n")

        # 检测登录状态（根据URL变化判断）
        start_url = self.page.url
        start_time = time.time()

        while time.time() - start_time < timeout:
            time.sleep(2)
            if self.page.url != start_url:
                print("✓ 检测到页面跳转，可能已登录")
                self.screenshot("after_login")
                return True

        print("⚠️ 超时，未检测到登录")
        return False

    def extract_content(self):
        """
        提取页面内容

        Returns:
            页面标题和内容
        """
        title = self.page.title()
        content = self.page.content()

        # 尝试提取正文
        try:
            # 移除 script 和 style 标签
            self.page.evaluate("""() => {
                document.querySelectorAll('script, style').forEach(el => el.remove());
            }""")

            # 获取正文文本
            body_text = self.page.evaluate("() => document.body.innerText")

            return {
                "title": title,
                "url": self.page.url,
                "content": body_text,
                "html": content
            }

        except Exception as e:
            print(f"⚠️ 提取内容时出错: {e}")
            return {
                "title": title,
                "url": self.page.url,
                "content": content
            }

    def screenshot(self, name):
        """
        截图保存

        Args:
            name: 截图名称
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{name}_{timestamp}.png"
            # 保存到 NAS 存储
            screenshot_dir = "/mnt/fn/Download3/clawdbotfile/playwright-screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            path = f"{screenshot_dir}/{filename}"

            self.page.screenshot(path=path)
            print(f"📸 截图已保存: {path}")

        except Exception as e:
            print(f"⚠️ 截图失败: {e}")

    def save_state(self):
        """
        保存浏览器状态（Cookie、LocalStorage 等）到 NAS
        """
        print("💾 正在备份配置到 NAS...")
        self._backup_to_nas()

    def close(self):
        """关闭浏览器"""
        try:
            if self.context:
                self.context.close()
        except Exception as e:
            print(f"⚠️ 关闭 context 时出错: {e}")

        try:
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            print(f"⚠️ 停止 playwright 时出错: {e}")

        print("✓ 浏览器已关闭")

        # 关闭前自动备份到 NAS
        try:
            self._backup_to_nas()
        except Exception as e:
            print(f"⚠️ 备份到 NAS 时出错: {e}")


def main():
    """示例用法"""
    # 创建浏览器实例
    browser = PlaywrightFallback(profile_name="xiaohongshu")

    try:
        # 启动浏览器
        browser.start(headless=False)

        # 访问小红书
        browser.goto("http://xhslink.com/o/4Q7mhdNSpjE")

        # 首次使用需要等待登录
        if browser.wait_for_login(timeout=120):
            print("✓ 登录成功")

        # 提取内容
        content = browser.extract_content()
        print(f"\n📝 标题: {content['title']}")
        print(f"🔗 URL: {content['url']}")
        print(f"📄 内容长度: {len(content['content'])} 字符")

        # 保存状态（下次可以直接使用，无需重新登录）
        browser.save_state()

        # 保持浏览器打开一段时间
        print("\n⏳ 浏览器将保持打开 30 秒...")
        time.sleep(30)

    except Exception as e:
        print(f"✗ 出错: {e}")
        browser.screenshot("error")

    finally:
        browser.close()


if __name__ == "__main__":
    main()
