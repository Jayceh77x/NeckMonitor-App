# NeckMonitor App

基于 Python + PySide6 的智能颈椎监测数据展示端。

当前阶段：

- 仅作为 STM32 设备的数据展示端
- 暂不进行 AI 计算
- 蓝牙串口模块预留接口，后续接入真实设备
- 目前使用模拟数据驱动 UI

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
    client.py
    mock_source.py
  data/
    parser.py
    cache.py
```

后续接入真实蓝牙串口时，优先替换或扩展 `neck_monitor.bluetooth.client.BluetoothSerialClient`，保持其向外发出原始数据字符串即可。

