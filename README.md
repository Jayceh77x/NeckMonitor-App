# NeckMonitor App

基于 Python + PySide6 的智能颈椎监测数据展示端。

当前阶段：

- 仅作为 STM32 设备的数据展示端
- 暂不进行 AI 计算
- 蓝牙串口模块预留接口，后续接入真实设备
- 目前使用 `BluetoothManager` 模拟 JDY-24M 蓝牙模块发送 JSON 数据驱动 UI

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

## 当前模拟数据格式

JDY-24M 模拟数据采用 JSON 字符串：

```json
{
  "score": 95,
  "state": "正常",
  "pitch": 3.2,
  "roll": -1.5,
  "mode": "JDY-24M_SIM"
}
```

后续接入真实蓝牙串口时，优先替换或扩展 `neck_monitor.bluetooth.manager.BluetoothManager` 的数据来源，保持其向外发出同样结构的 JSON 字符串即可。

## 后续开发说明

### 当前数据流

```text
BluetoothManager
  -> raw_data_received(JSON 字符串)
  -> SensorDataParser.parse()
  -> NeckSensorSample
  -> SensorDataCache
  -> MainWindow.update_sample()
```

当前 `BluetoothManager` 使用 `QTimer` 定时生成模拟数据。后续接入真实 JDY-24M 蓝牙串口后，建议保持对外信号不变，即继续通过 `raw_data_received.emit(payload)` 发送 JSON 字符串，这样 UI、解析和缓存模块不需要大改。

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
```

### 建议扩展 JSON 数据格式

下一阶段建议将 STM32/JDY-24M 发送的数据扩展为：

```json
{
  "score": 92,
  "state": "正常",
  "pitch": 12.5,
  "roll": 3.2,
  "yaw": 0.0,
  "pressure": 0.0,
  "mode": "普通模式",
  "confidence": null,
  "ai_status": "未启用",
  "wear_minutes": 388,
  "target_minutes": 480,
  "abnormal_count": 8,
  "longest_bad_posture_seconds": 195,
  "reminder_count": 1,
  "last_reminder_time": "10:23:15",
  "battery": 85,
  "rssi": -42,
  "firmware": "v2.1.3",
  "device_name": "NeckMonitor-01",
  "timestamp": "2026-07-24T14:44:29"
}
```

字段说明：

- `score`：健康评分，建议 STM32 端或上位机端统一输出 0-100。
- `state`：姿态状态文本，建议固定枚举值，避免 UI 侧做复杂判断。
- `pitch`、`roll`、`yaw`：姿态角度，单位建议统一为度。
- `pressure`：压力传感器值，当前 UI 未重点展示，后续可加入实时数据页。
- `mode`：提醒模式，例如普通模式、静音模式、强提醒模式。
- `confidence`：AI 置信度预留字段；当前不进行 AI 计算，可传 `null`。
- `ai_status`：AI 状态预留字段；当前建议固定为 `未启用`。
- `wear_minutes`：今日佩戴时长，单位分钟。
- `target_minutes`：今日目标佩戴时长，单位分钟。
- `abnormal_count`：今日异常次数。
- `longest_bad_posture_seconds`：最长异常姿态持续时间。
- `reminder_count`：今日提醒次数。
- `last_reminder_time`：最近一次提醒时间。
- `battery`：设备电量百分比。
- `rssi`：蓝牙信号强度，单位 dBm。
- `firmware`：固件版本。
- `device_name`：设备名称。
- `timestamp`：采样时间，推荐 ISO 8601 格式。

### UI 字段接入计划

已接入字段：

- 首页健康评分：`score`
- 首页当前状态：`state`
- 首页提醒模式：`mode`
- 实时数据 Pitch：`pitch`
- 实时数据 Roll：`roll`
- 历史记录：`timestamp`、`score`、`pitch`、`roll`、`state`、`mode`

待接入字段：

- 今日佩戴时长：`wear_minutes`
- 目标佩戴时长：`target_minutes`
- AI 状态：`ai_status`
- 置信度：`confidence`
- 今日异常次数：`abnormal_count`
- 最长异常姿态持续时间：`longest_bad_posture_seconds`
- 久坐或姿态提醒次数：`reminder_count`
- 最后提醒时间：`last_reminder_time`
- 设备名称：`device_name`
- 固件版本：`firmware`
- 蓝牙信号：`rssi`
- 电量：`battery`

### 未完成事项

1. 真实蓝牙串口接入
   - 当前只模拟 JDY-24M 数据。
   - 后续需要确认 Windows 下蓝牙串口映射的 COM 口。
   - 推荐使用 PySide6 的 `QSerialPort` 或 `pyserial` 接入。
   - 接入后仍建议按行读取 JSON，每行一帧数据。

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
   - 右侧“姿态状态指示”当前为占位，可后续改成自绘人体/角度示意。

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

当前开发习惯：

- 设计和开发前先检查 `git status`
- 每个阶段完成后做本地提交
- 不再每次自动上传 GitHub
- 如需上传，手动执行：

```powershell
git push -u origin main
```
