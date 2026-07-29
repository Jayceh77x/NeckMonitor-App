# NeckMonitor App

基于 Python + PySide6 的智能颈椎监测数据展示端。

蓝牙与 STM32 联调请直接参考：[蓝牙串口通信协议 V1](docs/Bluetooth_Protocol_V1.md)。

当前阶段：

- 仅作为 STM32 设备的数据展示端
- 暂不进行 AI 计算
- 默认通过 Windows 蓝牙虚拟串口 `COM8` 读取真实 JDY-24M 数据
- 保留 `BluetoothManager(simulation=True)` 模拟数据入口，便于无硬件时调试 UI

## 运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## 模块结构

```text
main.py
neck_monitor/
  app.py
  models.py
  ui/
    main_window.py
  bluetooth/
    manager.py
    client.py
    mock_source.py
  data/
    parser.py
    cache.py
```

## 今日完成内容

1. 完成 PySide6 项目基础框架搭建
   - 创建应用入口 `main.py`
   - 拆分 UI、蓝牙通信、数据解析、数据缓存等模块
   - 保留后续接入 STM32 蓝牙串口的扩展位置

2. 完成 JDY-24M 蓝牙串口接入
   - `BluetoothManager` 默认打开 `COM8`，串口参数为 115200 8N1
   - 使用 PySide6 `QSerialPort` 读取真实蓝牙虚拟串口字节流
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
   - UI 已删除“AI 状态”，避免让人误解为 APP 在执行 AI
   - `confidence` 仅展示 STM32U575 返回的板端识别置信度
   - 精细统计数据暂时显示为 `--`，后续扩展 JSON 数据格式后再接入

## 开发日志

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

## 当前模拟数据格式

JDY-24M 模拟数据采用 JSON 字符串：

```json
{
  "version": 1,
  "seq": 1,
  "score": 95,
  "state": "正常",
  "pitch": 3.2,
  "roll": -1.5,
  "mode": "JDY-24M_SIM",
  "confidence": 0.96,
  "alert": 0
}
```

实际串口数据必须在 JSON 后追加换行符 `\n`，即一行代表一帧：

```text
{"version":1,"seq":1,"score":95,"state":"NORMAL","pitch":3.2,"roll":-1.5,"mode":0,"confidence":0.96,"alert":0}\n
```

真实蓝牙串口已接入 `neck_monitor.bluetooth.manager.BluetoothManager`，默认读取 `COM8`。如需无硬件调试，可手动构造 `BluetoothManager(simulation=True)` 使用模拟数据源。

## 后续开发说明

### 当前数据流

```text
BluetoothManager
  -> raw_data_received(串口字节块或模拟字符串)
  -> JsonLineStreamDecoder.feed()
  -> SensorDataParser.parse()
  -> NeckSensorSample
  -> SensorDataCache
  -> MainWindow.update_sample()
```

当前 `BluetoothManager` 默认使用真实 `COM8` 串口读取 JDY-24M 数据。串口层只发出原始字节块，仍由 `JsonLineStreamDecoder` 按 `\n` 分帧，因此支持半包、粘包和 `\r\n`。模拟数据源仍保留在 `simulation=True` 模式中。

### 当前核心数据结构

`neck_monitor.models.NeckSensorSample` 当前字段：

```python
score: int          # 健康评分，0-100
state: str          # 当前姿态状态，例如：正常、低头异常、仰头异常、侧倾异常
pitch: float        # 俯仰角，单位 deg
roll: float         # 横滚角，单位 deg
mode: str           # 设备模式，例如：JDY-24M_SIM、普通模式
timestamp: datetime # 接收或采样时间
yaw: float          # 预留字段，当前默认为 0.0
pressure: float     # 预留字段，当前默认为 0.0
confidence: float | None # STM32 板端识别置信度，范围 0.0-1.0
alert: bool         # STM32 提醒事件，0/1 或 false/true
```

### 字段归属

APP 不执行姿态识别、AI 推理、健康评分或提醒决策。以下字段必须由 STM32U575 计算后经蓝牙发送：

- `score`：健康评分，0-100。
- `state`：姿态识别结果。
- `pitch`、`roll`：姿态角，单位为度。
- `yaw`：偏航角；UI 需要时发送。
- `pressure`：压力传感器数据；UI 需要时发送。
- `mode`：STM32 当前提醒模式。
- `alert`：STM32 已触发提醒的事件标记。
- `confidence`：STM32/NanoEdge AI 输出的置信度，范围 0.0-1.0。
- `wear_minutes`：今日佩戴时长，单位为分钟。
- `target_minutes`：今日佩戴目标，单位为分钟。
- `battery`：设备电量百分比。

以下字段不属于 STM32 核心算法结果：

- `abnormal_count`：APP 根据 `state` 从正常切换到异常的次数统计。
- `longest_bad_posture_seconds`：APP 根据异常状态开始、结束时间统计。
- `reminder_count`：APP 根据 `alert` 从 0 变为 1 的次数统计。
- `last_reminder_time`：APP 在收到提醒事件时记录的本机时间。
- `device_name`：设备元数据，可在连接后发送一次或在 APP 中配置。
- `firmware`：固件元数据，建议连接后由 STM32 发送一次。
- `rssi`：蓝牙接收信号强度，应由电脑蓝牙栈或 JDY-24M 查询接口提供；普通串口数据本身通常无法得到 RSSI。

注意：如果要求 APP 断开或关闭后仍能得到完整的“今日统计”，应将前四个统计值保存在 APP 的 SQLite 中；如果设备端需要作为唯一可信来源，也可以由 STM32 保存并定期发送统计快照。

### 蓝牙传输数据名单

推荐将高频数据控制在一帧 JSON 中。STM32 每 500-1000 ms 发送一次：

| 字段 | 必需 | 类型 | 来源/用途 |
| --- | --- | --- | --- |
| `version` | 是 | int | 协议版本，当前固定为 `1` |
| `seq` | 是 | uint32 | 帧序号，用于发现丢帧和重复帧 |
| `score` | 是 | int | STM32 计算的健康评分，0-100 |
| `state` | 是 | string | STM32 姿态结果枚举 |
| `pitch` | 是 | float | 俯仰角，单位 deg |
| `roll` | 是 | float | 横滚角，单位 deg |
| `mode` | 是 | int | 提醒模式：0 普通、1 静音、2 强提醒 |
| `alert` | 是 | int | 提醒事件：0 未触发、1 触发 |
| `confidence` | 建议 | float/null | 板端识别置信度，0.0-1.0 |
| `wear_minutes` | 建议 | int | 今日佩戴分钟数 |
| `target_minutes` | 可选 | int | 今日目标分钟数 |
| `battery` | 建议 | int | 电量百分比，0-100 |
| `yaw` | 可选 | float | 偏航角，单位 deg |
| `pressure` | 可选 | float | 压力值，单位需与固件统一 |
| `uptime_ms` | 建议 | uint32 | STM32 启动后的毫秒数，用于时序判断 |

连接建立后可发送一次设备元数据，也可以暂时放在同一帧中：`device_name`、`firmware`。`rssi` 不建议由 STM32 遥测帧提供。

### 推荐 JSON 协议 V1

STM32 发送示例：

```json
{
  "version": 1,
  "seq": 1024,
  "score": 92,
  "state": "NORMAL",
  "pitch": 12.5,
  "roll": 3.2,
  "mode": 0,
  "alert": 0,
  "confidence": 0.96,
  "wear_minutes": 388,
  "target_minutes": 480,
  "battery": 85,
  "uptime_ms": 325680
}
```

实际发送内容必须是单行紧凑 JSON，并以 `\n` 结尾：

```text
{"version":1,"seq":1024,"score":92,"state":"NORMAL","pitch":12.5,"roll":3.2,"mode":0,"alert":0,"confidence":0.96,"wear_minutes":388,"target_minutes":480,"battery":85,"uptime_ms":325680}\n
```

`state` 固定枚举：`NORMAL`、`HEAD_DOWN`、`HEAD_UP`、`TILT_LEFT`、`TILT_RIGHT`。APP 解析后自动转换成中文显示。

### APP 解码方案

串口和蓝牙可能出现半包或粘包，不能假设一次读取就是一帧。当前 APP 已加入 `JsonLineStreamDecoder`，处理步骤为：

1. JDY-24M 将 STM32 UART 字节透明传输到电脑串口。
2. APP 把每次读到的字节追加到接收缓冲区。
3. APP 按换行符 `\n` 切分完整帧；没有换行的半帧继续等待。
4. 一次收到多行时逐帧处理，解决粘包。
5. 每帧按 UTF-8 解码，再交给 `json.loads()`。
6. `SensorDataParser` 校验必需字段并转换类型，最后更新缓存和 UI。

因此 STM32 端只需要保证：UTF-8/ASCII JSON、每帧单行、末尾固定发送 `\n`、字段名和单位遵守协议。JSON 中不要加入注释、尾逗号或 `NaN`。

### UI 字段接入计划

已接入字段：

- 首页健康评分：`score`
- 首页当前状态：`state`
- 首页提醒模式：`mode`
- 实时数据 Pitch：`pitch`
- 实时数据 Roll：`roll`
- 识别置信度：`confidence`
- 异常事件计数：根据 `state` 状态切换统计
- 最后提醒时间：根据 `alert` 提醒事件记录
- 历史记录：`timestamp`、`score`、`pitch`、`roll`、`state`、`mode`

待接入字段：

- 今日佩戴时长：`wear_minutes`
- 目标佩戴时长：`target_minutes`
- 最长异常姿态持续时间：`longest_bad_posture_seconds`
- 久坐或姿态提醒次数：`reminder_count`
- 设备名称：`device_name`
- 固件版本：`firmware`
- 蓝牙信号：`rssi`
- 电量：`battery`

### 未完成事项

1. 真实蓝牙串口接入
   - 已默认接入 Windows 蓝牙虚拟串口 `COM8`。
   - 如设备管理器中的实际端口不是 `COM8`，需要同步修改 `neck_monitor/app.py` 中的端口配置。
   - 接入后仍按行读取 JSON，每行一帧数据。

2. 数据协议最终确认
   - 需要和 STM32 固件端统一 JSON 字段名、单位、枚举值。
   - 建议每帧以换行符 `\n` 结束，便于串口端分帧。
   - 建议 STM32 端发送 UTF-8 编码 JSON。

3. UI 精细数据接入
   - 当前多个统计字段显示为 `--`。
   - 等 JSON 扩展后，在 `SensorDataParser` 和 `NeckSensorSample` 中增加字段。
   - 然后在 `MainWindow.update_sample()` 中刷新对应控件。

4. 历史记录持久化
   - 当前历史记录只存在内存和界面表格中。
   - 后续可保存为 CSV、JSONL 或 SQLite。
   - 竞赛演示阶段建议先使用 CSV，方便查看和导出。

5. 数据校验和异常处理
   - 当前解析器只做基础字段校验。
   - 后续应处理 JSON 格式错误、字段缺失、数值越界、串口断开等情况。
   - UI 上应增加错误提示或连接状态提示。

6. 视觉细节继续优化
   - 顶部卡片可继续微调字号、留白和仪表盘细节。
   - 实时曲线可增加坐标、时间轴、阈值线。
   - 右侧“姿态状态指示”已接入自绘仪表和头颈轮廓素材，后续可继续优化动画与高 DPI 细节。

7. 打包发布
   - 后续可使用 PyInstaller 打包 Windows 可执行文件。
   - 需要测试 PySide6 插件、字体、图标和串口权限是否随包正常工作。

### 建议开发顺序

1. 确认 STM32 输出 JSON 协议。
2. 在 `NeckSensorSample` 中补齐扩展字段。
3. 修改 `SensorDataParser`，兼容新旧两种 JSON 数据。
4. 将 `BluetoothManager` 的模拟数据扩展为完整 JSON。
5. 把首页和右侧信息栏的 `--` 字段逐步接入真实数据。
6. 新增真实串口读取实现，先在 Windows COM 口上测试。
7. 增加错误提示、连接重试、串口选择等设备设置功能。
8. 增加历史数据保存和导出。
9. 做竞赛演示版本打包。

### 真实蓝牙串口接入建议

如果使用 `pyserial`，建议新增或改造：

```text
neck_monitor/bluetooth/
  manager.py              # 统一对外接口
  serial_reader.py        # 真实串口读取
  simulator.py            # 模拟数据源
```

`BluetoothManager` 可以负责选择数据源：

- `simulation=True`：使用模拟 JDY-24M 数据。
- `simulation=False`：使用真实串口读取。

真实串口读取建议行为：

- 打开指定 COM 口。
- 按行读取字节流。
- 解码为 UTF-8 字符串。
- 发出 `raw_data_received` 信号。
- 串口断开时发出 `connection_changed(False)` 和错误信号。

### 测试建议

当前可用基础检查：

```powershell
python -m compileall main.py neck_monitor
```

后续建议增加单元测试：

- JSON 正常解析测试
- JSON 缺字段测试
- 数值类型错误测试
- 缓存最大长度测试
- 模拟蓝牙数据格式测试

### Git 说明

后续由项目所有者自行完成 Git 检查、提交和上传。Codex 不自动执行 Git 操作。

## 开发日志

### 2026-07-29

- 增加设置页数据源切换按钮，支持模拟数据与真实蓝牙一键切换。
- 模拟数据统一改为单行 JSON，和 STM32 协议保持一致。
- 当前状态卡增加持续时间统计，连接蓝牙后自动开始计时。
- 今日佩戴时长改为连接即计时，断开即暂停累计。
- 实时姿态曲线改为平滑曲线，并保留采样点标记。