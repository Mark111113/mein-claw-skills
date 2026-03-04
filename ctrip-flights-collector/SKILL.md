# 携程机票采集器

携程机票价格和航班信息采集工具。支持直飞航班查询、价格筛选、结构化JSON输出。

## 功能

- 查询指定日期、航线的直飞航班信息
- 自动滚动加载完整航班列表（突破懒加载）
- 输出结构化JSON数据（航班号、航司、时间、机场、价格）
- 有头浏览器模式，绕过反爬虫

## 使用场景

- "查询3月6日上海到北京的机票"
- "采集携程航班信息"
- "查询机票价格"
- "分析航班时刻表"

## 航线代码说明

常用机场代码：
- 上海：SHA (所有机场)、PVG (浦东)、SHA (虹桥)
- 北京：PEK (首都)、PKX (大兴)
- 广州：CAN
- 深圳：SZX
- 成都：CTU、TFU
- 三亚：SYX

## 使用方法

### 基本查询

```bash
# 查询上海到北京，3月6日的航班
python3 /root/.agents/skills/ctrip-flights-collector/scripts/ctrip_flights.py
```

### 自定义参数

修改脚本中的参数：
- `departure`: 出发地机场代码（默认：SHA）
- `destination`: 目的地机场代码（默认：PEK）
- `date`: 查询日期（默认：2026-03-06）

## 输出格式

JSON文件包含：
- `route`: 航线信息
- `date`: 查询日期
- `total_flights`: 航班总数
- `flights`: 航班列表
  - `flight_number`: 航班号
  - `aircraft`: 机型
  - `airline`: 航空公司
  - `departure_time`: 起飞时间
  - `arrival_time`: 到达时间
  - `departure_airport`: 出发机场
  - `arrival_airport`: 到达机场
  - `price`: 价格（整数）
  - `price_text`: 价格文本

## 输出位置

- JSON文件：`/root/.openclaw/workspace/temp/ctrip_[route]_[date].json`
- 自动备份到NAS：`/mnt/fn/Download3/clawdbotfile/`

## 技术特点

1. **有头浏览器**：使用Playwright有头模式，绕过反爬虫
2. **慢速滚动**：每次300px，等待0.5秒，充分触发懒加载
3. **智能解析**：识别携程使用的non-breaking space（\xa0）
4. **VNC可视化**：可以在VNC中看到采集过程

## 依赖

- Playwright（通过playwright-fallback技能）
- Python 3.11+

## 注意事项

- 采集过程需要30-60秒（滚动加载）
- 需要VNC连接查看浏览器窗口
- 数据来源于携程，仅供参考
- 建议在非高峰期使用，避免过多请求

## 示例输出

```json
{
  "route": "上海(SHA) → 北京(PEK)",
  "date": "2026-03-06",
  "total_flights": 96,
  "flights": [
    {
      "flight_number": "HU7614",
      "aircraft": "波音738(中)",
      "airline": "新海航｜海南航空",
      "departure_time": "06:40",
      "arrival_time": "09:05",
      "departure_airport": "浦东国际机场T2",
      "arrival_airport": "首都国际机场T2",
      "price": 340,
      "price_text": "¥340起"
    }
  ]
}
```
