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
