#!/usr/bin/env python3
"""
微信公众号文章采集器
支持登录状态持久化、智能验证检测、批量采集
"""

import sys
import os
import time
import json
import argparse
from pathlib import Path
from datetime import datetime

# 硬编码DISPLAY（参考小红书collector）
os.environ["DISPLAY"] = ":0"

# 添加playwright-fallback路径
sys.path.append('/root/.agents/skills/playwright-fallback/scripts')
from playwright_fallback import PlaywrightFallback


class WeChatCollector:
    """微信公众号文章采集器"""

    def __init__(self, profile_name="wechat_articles", output_dir=None, dry_run=False, screenshot=True):
        """
        初始化采集器

        Args:
            profile_name: 浏览器profile名称
            output_dir: 输出目录
            dry_run: 测试模式（不保存文件）
            screenshot: 是否保存截图
        """
        self.profile_name = profile_name
        self.output_dir = output_dir or "/mnt/fn/Download3/clawdbotfile/wechat"
        self.dry_run = dry_run
        self.screenshot = screenshot
        self.browser = None

        # 确保输出目录存在
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        print(f"📱 微信采集器初始化")
        print(f"📁 输出目录: {self.output_dir}")
        print(f"🧪 测试模式: {'是' if dry_run else '否'}")

    def extract_article(self, url, timeout=120):
        """
        提取单篇文章

        Args:
            url: 文章URL
            timeout: 等待验证超时时间（秒）

        Returns:
            采集结果字典
        """
        print(f"\n📄 采集文章: {url}")

        try:
            # 启动浏览器
            if not self.browser:
                print("🚀 启动浏览器...")
                self.browser = PlaywrightFallback(profile_name=self.profile_name)
                self.browser.start(headless=True)  # 使用已有Cookie，可以无头模式

            # 访问文章
            print("📍 访问页面...")
            self.browser.goto(url, wait_until="networkidle")

            # 等待页面加载
            time.sleep(2)

            # 智能检测验证状态
            print("⏳ 检测页面状态...")
            start_time = time.time()
            verified = False
            page = self.browser.page

            while time.time() - start_time < timeout:
                current_url = page.url
                elapsed = int(time.time() - start_time)

                # 检测1：URL变化（包含poc_token）
                if "poc_token" in current_url:
                    print(f"✅ 检测到验证通过！URL已变化（{elapsed}秒）")
                    verified = True
                    break

                # 检测2：页面内容
                try:
                    content = page.content()
                    if "环境异常" not in content and "完成验证" not in content:
                        if len(content) > 5000:
                            print(f"✅ 检测到验证通过！页面已加载（{elapsed}秒）")
                            verified = True
                            break
                except:
                    pass

                # 显示进度
                if elapsed % 10 == 0 and elapsed > 0:
                    print(f"   ⏱️  等待中... {elapsed}/{timeout} 秒", flush=True)

                time.sleep(2)

            if not verified:
                print(f"⚠️ 超时（{timeout}秒），尝试提取当前页面...")

            # 等待页面稳定
            time.sleep(2)

            # 提取内容
            print("📥 提取文章内容...")

            try:
                content_data = self.browser.extract_content()
            except Exception as e:
                print(f"⚠️ extract_content失败，使用备用方法: {e}")
                # 备用提取方法
                page_content = page.content()
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(page_content, 'html.parser')

                for script in soup(['script', 'style', 'noscript']):
                    script.decompose()

                text = soup.get_text(separator='\n', strip=True)

                content_data = {
                    'url': page.url,
                    'title': page.title(),
                    'content': text,
                    'html': page_content
                }

            # 检查内容
            if not content_data or not content_data.get('content'):
                return {
                    'success': False,
                    'url': url,
                    'error': '内容提取失败'
                }

            content_length = len(content_data.get('content', ''))

            if content_length < 500:
                return {
                    'success': False,
                    'url': url,
                    'error': f'内容太短: {content_length} 字符',
                    'current_url': page.url
                }

            print(f"✅ 提取成功！内容长度: {content_length} 字符")

            # 清理内容
            text = content_data['content']
            lines = [line.strip() for line in text.split('\n')]
            cleaned_lines = []
            prev_empty = False

            for line in lines:
                if line:
                    cleaned_lines.append(line)
                    prev_empty = False
                elif not prev_empty:
                    cleaned_lines.append('')
                    prev_empty = True

            cleaned_text = '\n'.join(cleaned_lines)
            content_data['content'] = cleaned_text

            # 截图
            if self.screenshot and not self.dry_run:
                self.browser.screenshot(f"article_{int(time.time())}")

            return {
                'success': True,
                'url': url,
                'data': content_data,
                'length': content_length,
                'verified': verified,
                'elapsed': int(time.time() - start_time)
            }

        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()

            if self.browser and self.screenshot:
                self.browser.screenshot("error")

            return {
                'success': False,
                'url': url,
                'error': str(e)
            }

    def save_article(self, article_data):
        """
        保存文章到文件

        Args:
            article_data: 文章数据字典

        Returns:
            保存的文件路径字典
        """
        if not article_data['success']:
            return None

        data = article_data['data']
        timestamp = time.strftime('%Y%m%d_%H%M%S')

        # 从标题生成安全文件名
        title = data.get('title', '微信文章')
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_', '。', '，')).strip()
        safe_title = safe_title[:50] if len(safe_title) > 50 else safe_title

        if not safe_title:
            safe_title = f"微信文章_{timestamp}"

        base_name = f"{timestamp}_{safe_title}"

        # 文件路径
        md_file = f"{self.output_dir}/{base_name}.md"
        json_file = f"{self.output_dir}/{base_name}.json"
        # NAS 路径与输出路径一致（因为 output_dir 已经在 NAS 上）
        nas_md_file = md_file

        # 保存Markdown
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# {data.get('title', '微信文章')}\n\n")
            f.write(f"**URL:** {data.get('url', article_data['url'])}\n\n")
            f.write(f"**采集时间:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            if article_data.get('elapsed'):
                f.write(f"**检测耗时:** {article_data['elapsed']} 秒\n\n")
            f.write("---\n\n")
            f.write(data.get('content', ''))

        # 保存JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 复制到NAS
        if not self.dry_run:
            os.system(f"cp {md_file} {nas_md_file}")

        print(f"\n✅ 文章已保存:")
        print(f"   📄 {md_file}")
        print(f"   📋 {json_file}")
        if not self.dry_run:
            print(f"   💾 {nas_md_file}")

        return {
            'md': md_file,
            'json': json_file,
            'nas': nas_md_file if not self.dry_run else None
        }

    def collect(self, url, timeout=120):
        """
        采集文章（主入口）

        Args:
            url: 文章URL
            timeout: 等待验证超时时间（秒）

        Returns:
            采集结果字典
        """
        # 提取
        result = self.extract_article(url, timeout)

        if result['success']:
            # 保存
            if not self.dry_run:
                files = self.save_article(result)
                result['files'] = files

            # 显示预览
            preview_length = min(2000, result['length'])
            print(f"\n📄 内容预览（前{preview_length}字）:")
            print("=" * 70)
            print(result['data']['content'][:preview_length])
            print("=" * 70)
        else:
            print(f"\n❌ 采集失败: {result.get('error')}")

        return result

    def close(self):
        """关闭浏览器"""
        if self.browser:
            print("\n🔚 关闭浏览器...")
            self.browser.close()
            print("✓ Cookie已保存，下次自动恢复登录状态")
            self.browser = None


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='微信公众号文章采集器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s "https://mp.weixin.qq.com/s/xxxxx"
  %(prog)s "url1" "url2" "url3"
  %(prog)s @urls.txt --output /path/to/output
  %(prog)s "url" --dry-run --timeout 60
        """
    )

    parser.add_argument('urls', nargs='+', help='微信文章URL（支持多个或@filename）')
    parser.add_argument('--output', '-o', help='输出目录（默认: /root/.openclaw/workspace/temp）')
    parser.add_argument('--dry-run', '-n', action='store_true', help='测试模式（不保存文件）')
    parser.add_argument('--no-screenshot', action='store_true', help='不保存截图')
    parser.add_argument('--timeout', '-t', type=int, default=120, help='等待验证超时时间（秒）')

    args = parser.parse_args()

    # 处理URL列表
    urls = []
    for url_arg in args.urls:
        if url_arg.startswith('@'):
            # 从文件读取
            file_path = url_arg[1:]
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    urls.extend([line.strip() for line in f if line.strip()])
            except Exception as e:
                print(f"❌ 读取URL文件失败: {e}")
                sys.exit(1)
        else:
            urls.append(url_arg)

    if not urls:
        print("❌ 请提供至少一个URL")
        sys.exit(1)

    # 创建采集器
    collector = WeChatCollector(
        output_dir=args.output,
        dry_run=args.dry_run,
        screenshot=not args.no_screenshot
    )

    try:
        # 采集文章
        print(f"\n{'='*70}")
        print(f"开始采集 {len(urls)} 篇文章")
        print(f"{'='*70}\n")

        results = []
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] 采集: {url}")

            result = collector.collect(url, timeout=args.timeout)
            results.append(result)

            # 统计
            success_count = sum(1 for r in results if r['success'])
            print(f"\n📊 进度: {success_count}/{len(results)} 成功")

            # 间隔
            if i < len(urls):
                print("⏳ 等待5秒...")
                time.sleep(5)

        # 总结
        print(f"\n{'='*70}")
        print("采集完成")
        print(f"{'='*70}")
        print(f"总数: {len(results)}")
        print(f"成功: {sum(1 for r in results if r['success'])}")
        print(f"失败: {sum(1 for r in results if not r['success'])}")

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        collector.close()


if __name__ == "__main__":
    main()
