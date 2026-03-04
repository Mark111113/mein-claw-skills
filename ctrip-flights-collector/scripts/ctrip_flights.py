#!/usr/bin/env python3
"""
携程机票数据提取脚本 - 输出结构化JSON
"""
import sys
import time
import re
import json

# 添加 Playwright fallback 路径
sys.path.insert(0, '/root/.agents/skills/playwright-fallback/scripts')
from playwright_fallback import PlaywrightFallback

def extract_flights_from_text(page_text):
    """从页面文本中提取航班信息"""
    lines = page_text.split('\n')
    flights = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 检测航班号行（如 "HU7614 波音738(中)"）
        # 注意：携程使用 non-breaking space (\xa0)
        flight_match = re.match(r'^([A-Z]{2}\d{3,4})[\s\xa0\u3000]+(\S+)', line)
        if flight_match:
            # 调试输出
            if len(flights) == 0:
                print(f"🐛 找到第一个航班: {repr(line[:60])}")
                print(f"   Match groups: {flight_match.groups()}")
            flight_num = flight_match.group(1)
            aircraft = flight_match.group(2)

            # 向后查找相关信息
            departure_time = None
            arrival_time = None
            departure_airport = None
            arrival_airport = None
            airline = None
            price = None
            price_text = None

            # 向前查找航空公司
            for j in range(max(0, i-5), i):
                if any(air in lines[j] for air in ['中国国航', '东方航空', '南方航空', '海南航空', '厦门航空', '山东航空', '深圳航空', '四川航空', '吉祥航空', '金鹏航空']):
                    airline = lines[j].strip()
                    break

            # 向后查找时间、机场、价格
            j = i + 1
            while j < len(lines) and j < i + 15:
                next_line = lines[j].strip()

                # 时间
                if re.match(r'^\d{1,2}:\d{2}$', next_line):
                    if departure_time is None:
                        departure_time = next_line
                    elif arrival_time is None:
                        arrival_time = next_line

                # 机场
                elif '机场' in next_line:
                    if departure_airport is None:
                        departure_airport = next_line
                    elif arrival_airport is None:
                        arrival_airport = next_line

                # 价格
                elif next_line.startswith('¥'):
                    price_match = re.search(r'¥(\d+)', next_line)
                    if price_match and price is None:
                        price = int(price_match.group(1))
                        price_text = next_line

                # 遇到"中转组合"或新的航班号，停止
                elif '中转组合' in next_line or re.match(r'^[A-Z]{2}\d{3,4}', next_line):
                    break

                j += 1

            # 只有有完整信息的才添加
            if departure_time and arrival_time:
                flights.append({
                    'flight_number': flight_num,
                    'aircraft': aircraft,
                    'airline': airline,
                    'departure_time': departure_time,
                    'arrival_time': arrival_time,
                    'departure_airport': departure_airport,
                    'arrival_airport': arrival_airport,
                    'price': price,
                    'price_text': price_text
                })

        # 遇到"中转组合"停止
        if '中转组合' in line:
            break

        i += 1

    return flights

def main():
    print("🚀 启动浏览器...")
    browser = PlaywrightFallback(profile_name="ctrip_flights")
    browser.start(headless=False)

    print("📍 访问航班列表...")
    browser.goto("https://flights.ctrip.com/online/list/oneway-sha-pek?date=2026-03-06")
    time.sleep(5)

    print("\n🔄 滚动加载所有航班...")
    for i in range(30):
        browser.page.evaluate("window.scrollBy(0, 300)")
        time.sleep(0.5)

        if (i+1) % 5 == 0:
            scroll_pos = browser.page.evaluate("window.scrollY")
            total_height = browser.page.evaluate("document.body.scrollHeight")
            print(f"   📜 {scroll_pos}/{total_height}px ({i+1}/30)", flush=True)

    time.sleep(2)
    print("✅ 滚动完成\n")

    print("📥 提取并解析航班信息...")
    page_text = browser.page.inner_text("body")

    # 保存原始文本用于调试
    debug_file = '/root/.openclaw/workspace/temp/ctrip_debug_raw.txt'
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(page_text)
    print(f"🐛 调试：原始文本已保存到 {debug_file}")

    flights = extract_flights_from_text(page_text)
    print(f"✅ 解析完成，找到 {len(flights)} 个直飞航班\n")

    # 输出JSON
    output = {
        'route': '上海(SHA) → 北京(PEK)',
        'date': '2026-03-06',
        'total_flights': len(flights),
        'flights': flights
    }

    # 保存JSON
    json_file = '/root/.openclaw/workspace/temp/ctrip_march6_flights.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"💾 JSON已保存: {json_file}\n")

    # 打印预览
    print("="*70)
    print("📋 航班预览（前10个）:")
    print("="*70)
    for idx, flight in enumerate(flights[:10], 1):
        print(f"\n{idx}. {flight.get('flight_number', '')}")
        if flight.get('airline'):
            print(f"   航空: {flight.get('airline', '')}")
        print(f"   ⏰ {flight.get('departure_time', '')} → {flight.get('arrival_time', '')}")
        print(f"   ✈️ {flight.get('departure_airport', '')} → {flight.get('arrival_airport', '')}")
        if flight.get('price_text'):
            print(f"   💰 {flight.get('price_text', '')}")

    # 统计
    if flights:
        prices = [f['price'] for f in flights if f.get('price')]
        if prices:
            print(f"\n💰 价格统计:")
            print(f"   最低: ¥{min(prices)}")
            print(f"   最高: ¥{max(prices)}")
            print(f"   平均: ¥{sum(prices)//len(prices)}")

    print(f"\n✅ 完成！共 {len(flights)} 个航班")
    print(f"📁 完整JSON: {json_file}")

    browser.close()

if __name__ == '__main__':
    main()
