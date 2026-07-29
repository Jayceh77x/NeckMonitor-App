# NeckMonitor App

智能颈椎监测系统的 Python 上位机软件，基于 PySide6 实现。APP 定位是 STM32U575 智能颈椎监测设备的无线数据显示终端，负责蓝牙通信、JSON 数据解析、界面展示和本地内存缓存。

硬件端仍然是算法端。姿态计算、NanoEdge AI 推理、异常判断、健康评分和提醒策略都应由 STM32 完成，Python APP 只接收、解析、显示结果。

## 当前状态

- 默认启动使用模拟数据，方便没有硬件时继续开发 UI。
- 设置页提供数据源切换按钮，可在模拟数据和真实蓝牙之间一键切换。
- 真实蓝牙入口保留为 Windows 虚拟串口 `COM8`，波特率 `115200`。
- 模拟数据已经统一为单行 JSON，和真实 STM32 协议走同一套解析链路。
- Dashboard 已接入健康评分、当前状态、提醒模式、今日佩戴时长、蓝牙状态、Pitch、Roll、置信度、异常计数和历史记录。
- 当前状态卡已支持持续时间统计，状态变化时重新计时。
- 今日佩戴时长已支持连接即计时，断开即暂停累计。
- 实时 Pitch/Roll 曲线已改为平滑曲线，带采样点标记、动态纵轴和分钟级时间轴。

## 运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

依赖：

```text
PySide6>=6.7
```

## 数据流

```text
STM32U575 或模拟数据源
  -> JDY-24M / Windows COM 口 或 MockDataSource
  -> BluetoothManager.raw_data_received
  -> JsonLineStreamDecoder.feed()
  -> SensorDataParser.parse()
  -> NeckSensorSample
  -> SensorDataCache
  -> MainWindow.update_sample()
```

真实蓝牙和模拟数据只在数据源层不同，进入 APP 后共用同一套 JSON 分帧、解析、缓存和 UI 刷新逻辑。

## 模块结构

```text
main.py
neck_monitor/
  app.py                         # 应用装配和信号连接
  models.py                      # NeckSensorSample 数据模型
  bluetooth/
    client.py                    # PySide6 QSerialPort 串口读取
    manager.py                   # 数据源统一入口和 mock/serial 切换
    mock_source.py               # 模拟 STM32 JSON 数据源
  data/
    parser.py                    # JSON 分帧和协议解析
    cache.py                     # 最近数据内存缓存
  ui/
    main_window.py               # 主窗口、页面和数据绑定
    widgets.py                   # 自绘仪表、姿态图、实时曲线
    assets/posture/              # 姿态图片资源
docs/
  Bluetooth_Protocol_V1.md       # 蓝牙协议说明
```

## 数据源切换

当前默认数据源在 `neck_monitor/app.py` 中设置：

```python
self.bluetooth = BluetoothManager(
    port_name="COM8",
    baud_rate=115200,
    source_mode=BluetoothManager.SOURCE_MOCK,
)
```

设置页按钮可在运行时切换：

- `mock`：模拟数据源，用于 UI 开发。
- `serial`：真实蓝牙串口，默认 `COM8 / 115200`。

切换时会停止当前源、重置分帧缓冲并启动新源。真实蓝牙底层读取仍由 `BluetoothSerialClient` 完成。

## JSON 协议

APP 接收单行 JSON，每帧必须以真实换行符 `\n` 结尾。示例：

```json
{"version":1,"seq":1,"score":92,"state":"NORMAL","pitch":12.5,"roll":3.2,"mode":0,"alert":0,"confidence":0.96}
```

当前解析器要求的核心字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `version` | int | 协议版本，默认兼容 `1` |
| `score` | int | STM32 输出的健康评分，范围 0-100 |
| `state` | string | STM32 输出的姿态状态 |
| `pitch` | number | 俯仰角，单位度 |
| `roll` | number | 横滚角，单位度 |
| `mode` | int/string | 提醒模式 |
| `alert` | int/bool | STM32 提醒事件标记 |
| `confidence` | number/null | STM32/NanoEdge AI 输出的置信度 |
| `timestamp` | string | 可选 ISO 8601 时间戳 |
| `yaw` | number | 可选偏航角 |
| `pressure` | number | 可选压力值 |

`state` 枚举映射：

| 原始值 | APP 显示 |
| --- | --- |
| `NORMAL` | 正常 |
| `HEAD_DOWN` | 低头异常 |
| `HEAD_UP` | 仰头异常 |
| `TILT_LEFT` | 左倾异常 |
| `TILT_RIGHT` | 右倾异常 |
| `TILT` | 侧倾异常 |

## UI 功能

### Dashboard

- 健康评分：显示 STM32 返回的 `score`。
- 当前状态：显示 `state` 的中文状态，正常状态显示为“良好坐姿”。
- 当前状态持续时间：状态变化时重新计时，格式为 `MM:SS` 或 `HH:MM:SS`。
- 提醒模式：根据 `mode` 显示普通、静音或强提醒模式。
- 今日佩戴时长：蓝牙连接后开始计时，断开后暂停累计。
- 蓝牙状态：显示模拟数据接收中、真实蓝牙接收中、已停止或错误状态。

### 实时监测

- Pitch 和 Roll 当前值。
- 平滑实时曲线，最近窗口最多保留 180 个采样点。
- 纵轴按当前曲线窗口内最大绝对角度自适应。
- 底部时间轴固定显示最近 2 分钟、1 分钟和当前分钟。
- 采样点用小圆点标记，最新采样点稍微突出。
- 置信度显示 `confidence`，APP 不计算 AI 结果。

### 历史记录

- 当前为内存和表格记录，最多显示最近 120 条。
- 字段包括时间、评分、Pitch、Roll、姿态、模式和数据源。

### 设备设置

- 显示设备名称、蓝牙模块、串口参数和数据格式。
- 提供模拟数据与真实蓝牙的数据源切换按钮。

## 本地统计规则

APP 目前只做显示端和轻量统计：

- `abnormal_count`：根据 `state` 从正常进入异常时累计。
- `last_reminder_time`：收到 `alert` 上升事件时记录。
- `current_state_duration`：根据 APP 本机时间统计当前状态持续时间。
- `wear_time`：根据蓝牙连接状态统计本次 APP 运行期间的今日佩戴时长。

APP 不做以下计算：

- 姿态识别算法
- NanoEdge AI 推理
- 健康评分计算
- 提醒策略判断

## 验证

基础检查：

```powershell
python -m compileall neck_monitor
```

建议联调检查：

1. 模拟数据源能持续刷新 Dashboard 和实时曲线。
2. 设置页切到真实蓝牙后能打开 `COM8 / 115200`。
3. STM32 每帧输出单行 JSON，并以 `\n` 结尾。
4. Pitch/Roll 大幅变化时曲线纵轴能自适应。
5. 当前状态改变时持续时间重新计时。
6. 蓝牙连接后今日佩戴时长开始计时，断开后暂停。

## 开发日志

### 2026-07-24

今日完成内容

1. 完成 PySide6 项目基础框架搭建
   - 创建应用入口 `main.py`
   - 拆分 UI、蓝牙通信、数据解析、数据缓存等模块
   - 保留后续接入 STM32 蓝牙串口的扩展位置

2. 完成 JDY-24M 蓝牙数据模拟
   - 新增 `BluetoothManager`
   - 当前无真实蓝牙模块时，使用定时器模拟 JDY-24M 数据发送
   - 数据链路为 `BluetoothManager -> SensorDataParser -> SensorDataCache -> MainWindow`

3. 切换模拟数据格式为 JSON
   - 当前核心字段包括 `score`、`state`、`pitch`、`roll`、`mode`
   - UI 可基于 JSON 数据实时刷新健康评分、当前状态、Pitch、Roll、历史记录等内容

4. 完成竞赛展示风格 UI 设计
   - 首页采用左侧导航栏、顶部状态栏、核心数据卡片、实时姿态区域和右侧信息栏布局
   - 顶部卡片包含健康评分、当前状态、提醒模式、今日佩戴时长
   - 健康评分使用半圆仪表盘样式
   - Pitch / Roll 使用实时曲线组件预留展示趋势
   - 历史记录页使用更清晰的表格形式显示数据
   - 设备设置页预留真实蓝牙串口参数和设备信息展示位置

5. 当前设计约束
   - APP 仅作为 STM32 设备数据展示端
   - 当前不进行 AI 计算
   - `AI状态` 和 `置信度` 为预留展示字段
   - 精细统计数据暂时显示为 `--`，后续扩展 JSON 数据格式后再接入

### 2026-07-27

- 将健康评分圆环、实时折线图、姿态状态仪表、按钮和卡片拆分为可复用的 PySide6 UI 组件。
- 优化首页健康评分与当前状态卡片布局，解决评分文字重叠和姿态文字显示不全问题。
- 为当前状态卡片接入正常坐姿、低头、侧倾和后仰图片；左倾、右倾、侧倾与低头共用同一异常姿态素材。
- 完成姿态状态仪表的五段能量块、实时状态配色与头颈轮廓图显示。
- 调整仰头、左倾、正常、右倾、低头标签与对应能量块的对齐关系，避免外侧标签和轮廓图被遮挡。
- 异常姿态的激活能量块、对应标签和状态文字统一使用 `#f59e0b`，正常状态保持绿色。
- 对姿态图片进行透明背景处理并整理到 `neck_monitor/ui/assets/posture/`，保留 `reference/` 中的原始素材。
- 本次改动仅涉及 UI 与图片资源，没有修改蓝牙、协议解析、缓存和 STM32 数据处理逻辑。
- 已通过 Python 编译检查、离屏启动与正常/低头/仰头等状态的渲染验证。

### 2026-07-29

- 接入真实蓝牙串口读取入口，保留 `COM8 / 115200` 默认配置。
- 增加设置页数据源切换按钮，支持模拟数据与真实蓝牙一键切换。
- 模拟数据统一改为单行 JSON，和 STM32 协议保持一致。
- 增加 JSON 分帧和解析链路，支持半包、粘包和 `\r\n`。
- 当前状态卡增加持续时间统计，状态变化时重新计时。
- 今日佩戴时长改为连接即计时，断开即暂停累计。
- 实时姿态折线改为平滑曲线，保留采样点标记。
- 实时曲线纵轴改为按当前窗口最大绝对角度自适应。
- 实时曲线底部时间轴改为分钟级固定刻度。
