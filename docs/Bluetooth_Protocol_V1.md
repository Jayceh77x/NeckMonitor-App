# NeckMonitor 蓝牙串口通信协议 V1

本文档用于 STM32U575、JDY-24M 蓝牙模块和 NeckMonitor Python APP 之间的通信联调。

## 1. 系统边界

数据链路：

```text
STM32U575 -> UART -> JDY-24M -> Bluetooth SPP -> Windows 虚拟 COM 口 -> PySide6 APP
```

STM32U575 负责：

- 传感器采集
- 姿态角计算
- NanoEdge AI 推理
- 姿态状态判断
- 健康评分计算
- 提醒模式和提醒决策

APP 只负责接收、分帧、解析、缓存、历史统计和界面显示，不重新计算姿态、AI 结果或健康评分。

APP 界面没有 `ai_status` 字段。`confidence` 是 STM32 输出的识别置信度，不是 APP 计算结果。

## 2. 串口和蓝牙参数

推荐参数：

| 参数 | 推荐值 |
| --- | --- |
| UART 波特率 | 115200 bps |
| 数据位 | 8 |
| 停止位 | 1 |
| 校验位 | None |
| 流控 | None |
| 字符编码 | UTF-8，无 BOM |
| 数据格式 | 单行 JSON |
| 帧结束符 | LF，即字节 `0x0A` |
| 发送周期 | 500-1000 ms |

如果 JDY-24M 当前配置为其他波特率，可以调整，但 STM32 UART、JDY-24M 和 APP 串口设置必须一致。推荐优先使用 115200、8N1。

JDY-24M 只负责透明传输，不应修改 JSON 内容。

## 3. 分帧规则

每个 JSON 对象是一帧，每帧必须满足：

1. 一帧只能占一行。
2. JSON 后必须追加 `\n`。
3. 可以使用 `\r\n`，APP 会自动去掉 `\r`。
4. 不允许在 JSON 字符串中插入真实换行。
5. 不允许添加 JSON 注释、尾逗号、`NaN`、`Infinity`。
6. 浮点数使用小数点 `.`，不能使用逗号作为小数点。
7. 推荐单帧不超过 512 字节。
8. V1 不在 JSON 后追加 CRC 或校验和；链路完整性依赖蓝牙协议，APP 继续通过 JSON、类型和范围校验过滤异常帧。

最小可用帧：

```text
{"version":1,"seq":1,"score":95,"state":"NORMAL","pitch":1.2,"roll":-0.5,"mode":0,"alert":0}\n
```

字节流结尾必须是真实的换行字节 `0x0A`，不是字符 `\` 和字符 `n`。

## 4. 遥测帧字段

STM32 建议每 500-1000 ms 发送一帧遥测数据。

| 字段 | 必需 | JSON 类型 | 范围/格式 | 数据来源 |
| --- | --- | --- | --- | --- |
| `version` | 是 | integer | 固定为 `1` | 协议版本 |
| `seq` | 是 | integer | uint32，逐帧递增 | STM32 帧序号 |
| `score` | 是 | integer | 0-100 | STM32 健康评分 |
| `state` | 是 | string | 见姿态枚举 | STM32 姿态识别结果 |
| `pitch` | 是 | number | 有限浮点数，单位 deg | STM32 姿态计算 |
| `roll` | 是 | number | 有限浮点数，单位 deg | STM32 姿态计算 |
| `mode` | 是 | integer | 0、1、2 | STM32 提醒模式 |
| `alert` | 是 | integer/bool | `0/1` 或 `false/true` | STM32 提醒事件 |
| `confidence` | 建议 | number/null | 0.0-1.0 | STM32/NanoEdge AI |
| `wear_minutes` | 建议 | integer | 0 或正整数，单位 min | STM32 佩戴计时 |
| `target_minutes` | 可选 | integer | 0 或正整数，单位 min | STM32/设备配置 |
| `battery` | 建议 | integer | 0-100，单位 % | STM32 电量检测 |
| `yaw` | 可选 | number | 有限浮点数，单位 deg | STM32 姿态计算 |
| `pressure` | 可选 | number | 单位需在固件端固定 | STM32 压力传感器 |
| `uptime_ms` | 建议 | integer | uint32，单位 ms | STM32 系统时基 |
| `timestamp` | 可选 | string | ISO 8601 | STM32 RTC 时间 |
| `device_name` | 首帧建议 | string | 建议不超过 32 字节 | 设备元数据 |
| `firmware` | 首帧建议 | string | 建议不超过 16 字节 | 固件元数据 |

`timestamp` 示例：`2026-07-25T15:30:45`。如果 STM32 没有可靠 RTC，可以只发送 `uptime_ms`，APP 使用电脑接收时间记录历史数据。

## 5. 姿态枚举

`state` 必须使用以下大写 ASCII 枚举：

| 值 | APP 显示 | 含义 |
| --- | --- | --- |
| `NORMAL` | 正常 | 当前姿态正常 |
| `HEAD_DOWN` | 低头异常 | 低头异常 |
| `HEAD_UP` | 仰头异常 | 仰头异常 |
| `TILT_LEFT` | 左倾异常 | 颈部向左侧倾 |
| `TILT_RIGHT` | 右倾异常 | 颈部向右侧倾 |

角度正负方向统一为：

- `pitch > 0`：仰头
- `pitch < 0`：低头
- `roll > 0`：右倾
- `roll < 0`：左倾

姿态阈值由 STM32 决定。APP 不根据角度重新判断 `state`。

APP 将英文枚举自动转换为中文显示。不要发送不固定的自然语言，例如“有点低头”或“基本正常”。

## 6. 提醒模式枚举

| `mode` | APP 显示 | 含义 |
| --- | --- | --- |
| `0` | 普通模式 | 标准提醒策略 |
| `1` | 静音模式 | 静音或弱提醒策略 |
| `2` | 强提醒模式 | 强提醒策略 |

如果固件需要增加模式，应先升级协议版本或与 APP 同步增加枚举，不能直接复用现有数字表示其他含义。

## 7. `alert` 提醒事件规则

`alert` 表示 STM32 已经执行了一次提醒决策，不表示 APP 自己判断需要提醒。

APP 按 `alert` 的上升沿统计提醒：

```text
0 -> 1：记为一次提醒，并记录最后提醒时间
1 -> 1：仍然是同一次提醒，不重复计数
1 -> 0：提醒事件复位
```

建议 STM32 在触发提醒时连续发送两帧 `alert=1`，随后恢复为 `alert=0`。这样可以降低单帧丢失导致提醒事件遗漏的概率，同时 APP 仍只统计一次。

示例：

```text
seq=100, alert=0
seq=101, alert=1
seq=102, alert=1
seq=103, alert=0
```

上述序列在 APP 中只计为一次提醒。

## 8. APP 本地统计字段

以下字段当前不要求 STM32 在高频遥测帧中发送：

| 字段 | APP 统计方式 |
| --- | --- |
| `abnormal_count` | `state` 从 `NORMAL` 进入任意异常状态时加 1 |
| `longest_bad_posture_seconds` | 根据异常状态开始和结束时间计算 |
| `reminder_count` | 根据 `alert` 的 0 到 1 上升沿统计 |
| `last_reminder_time` | 收到 `alert` 上升沿时记录电脑时间 |

从一种异常状态直接切换到另一种异常状态，当前仍属于同一次连续异常，不增加 `abnormal_count`。只有恢复 `NORMAL` 后再次进入异常状态才算新的一次异常。

当前 APP 已实现 `abnormal_count` 和 `last_reminder_time` 的内存统计；`longest_bad_posture_seconds`、`reminder_count` 以及跨重启持久化仍待开发。

如果 APP 断开连接，APP 无法统计断开期间发生的数据。若比赛需求要求设备离线后仍保留完整今日统计，应采用以下方案之一：

- APP 使用 SQLite 按日期持久化已接收统计；断开期间的数据仍无法补齐。
- STM32 保存完整统计，并在重连后发送统计快照。该方案需要后续增加新的消息类型。

## 9. 设备元数据和 RSSI

`device_name` 和 `firmware` 不是算法结果，但 APP 显示真实设备信息时需要获得它们。

当前建议在连接后的第一帧遥测中附加：

```json
{
  "device_name": "NeckMonitor-01",
  "firmware": "v1.0.0"
}
```

也可以每 30 秒重复携带一次，便于 APP 重连或丢失首帧后恢复信息。

当前解析器可以接收并忽略这些额外字段，设备信息控件的动态绑定仍待开发，因此蓝牙端可以先按协议发送，不会影响现有遥测解析。

`rssi` 不放入 STM32 遥测帧。RSSI 表示接收端观察到的蓝牙信号强度，通常应从 Windows 蓝牙栈或 JDY-24M 的查询接口获得。若 JDY-24M 固件无法查询 RSSI，APP 显示 `--`。

## 10. 完整发送示例

正常姿态：

```text
{"version":1,"seq":1024,"score":92,"state":"NORMAL","pitch":3.2,"roll":-1.5,"mode":0,"alert":0,"confidence":0.96,"wear_minutes":388,"target_minutes":480,"battery":85,"uptime_ms":325680,"device_name":"NeckMonitor-01","firmware":"v1.0.0"}\n
```

低头异常并触发提醒：

```text
{"version":1,"seq":1025,"score":68,"state":"HEAD_DOWN","pitch":-24.7,"roll":2.1,"mode":0,"alert":1,"confidence":0.94,"wear_minutes":389,"target_minutes":480,"battery":85,"uptime_ms":326480}\n
```

未启用或暂时没有置信度时：

```text
{"version":1,"seq":1026,"score":88,"state":"NORMAL","pitch":2.0,"roll":0.6,"mode":1,"alert":0,"confidence":null}\n
```

## 11. STM32 组包参考

可以使用 `snprintf` 或 JSON 库生成单行字符串。不要手工分多次发送同一帧，建议先在缓冲区中生成完整 JSON，再一次调用 UART 发送。

```c
char tx_buffer[512];

int tx_length = snprintf(
    tx_buffer,
    sizeof(tx_buffer),
    "{\"version\":1,\"seq\":%lu,\"score\":%u,"
    "\"state\":\"%s\",\"pitch\":%.2f,\"roll\":%.2f,"
    "\"mode\":%u,\"alert\":%u,\"confidence\":%.3f,"
    "\"wear_minutes\":%u,\"battery\":%u,\"uptime_ms\":%lu}\n",
    (unsigned long)telemetry_seq,
    health_score,
    posture_state_text,
    pitch_deg,
    roll_deg,
    reminder_mode,
    alert_active,
    confidence,
    wear_minutes,
    battery_percent,
    (unsigned long)HAL_GetTick()
);

if (tx_length > 0 && tx_length < (int)sizeof(tx_buffer)) {
    HAL_UART_Transmit(
        &huart_x,
        (uint8_t *)tx_buffer,
        (uint16_t)tx_length,
        100
    );
}
```

注意事项：

- 某些 STM32 工程默认没有启用 `printf` 浮点格式，需要开启浮点格式支持或使用 JSON 库。
- 必须检查 `snprintf` 返回长度，防止缓冲区截断。
- `seq` 每成功生成一帧后递增，uint32 溢出后从 0 继续即可。
- 如果 UART 使用 DMA，必须保证发送完成前 `tx_buffer` 不被下一帧覆盖。
- 不要使用本地化格式输出浮点数，必须保持小数点为 `.`。

## 12. APP 解码流程

APP 的接收流程如下：

```text
串口读取任意长度字节块
        |
        v
追加到接收缓冲区
        |
        v
搜索换行字节 0x0A
        |
        +-- 没有完整行：保留半包，等待下一次数据
        |
        +-- 找到一行：取出完整 JSON 帧
                         |
                         v
                    UTF-8 解码
                         |
                         v
                    json.loads()
                         |
                         v
                  字段、类型、范围校验
                         |
                         v
                    缓存并刷新 UI
```

APP 支持：

- 一帧被拆成多次串口读取，即半包。
- 多帧一次到达，即粘包。
- `\n` 和 `\r\n` 两种行结束方式。
- 英文姿态枚举自动转换成中文。
- 忽略暂未绑定到 UI 的额外 JSON 字段。

APP 会拒绝：

- 不完整或非法 JSON。
- 缺少 `score`、`state`、`pitch`、`roll`、`mode`。
- `version` 不是 1。
- `score` 不在 0-100。
- `confidence` 不为 `null` 且不在 0.0-1.0。
- `alert` 不是 0、1、false 或 true。
- `pitch`、`roll` 是无穷大或 NaN。
- UTF-8 编码错误。

当前 APP 为兼容早期模拟数据，暂时允许缺少 `version`、`seq`、`confidence` 和 `alert`；正式 STM32 固件仍应按本文档完整发送。

当前 APP 能接收 `seq`，丢帧率统计和重复帧提示尚未接入 UI，但蓝牙端必须从现在开始正确递增该字段，避免后续再次修改固件协议。

## 13. 联调验收清单

蓝牙/STM32 端完成后，依次验证：

1. 串口助手能看到每行一个完整 JSON。
2. 每行末尾存在真实字节 `0x0A`。
3. 连续发送 1000 帧无乱码、无截断、无缓冲区溢出。
4. `seq` 连续递增，允许检测丢帧。
5. `NORMAL`、`HEAD_DOWN`、`HEAD_UP`、`TILT_LEFT`、`TILT_RIGHT` 均能正确显示。
6. Pitch、Roll 正负方向与文档一致。
7. `score`、`confidence`、`battery` 不越界。
8. `mode=0/1/2` 在 APP 中显示正确。
9. `alert` 连续两帧为 1 时 APP 只统计一次提醒。
10. 人工把一帧拆成两次发送，APP 仍能正确解析。
11. 一次发送两帧，APP 能分别解析两条数据。
12. 发送非法 JSON 时 APP 提示数据格式错误，下一条正确帧可以继续刷新。

## 14. V1 固定结论

蓝牙端最重要的实现要求只有四条：

1. 使用 UTF-8 单行 JSON。
2. 每帧末尾发送真实换行字节 `0x0A`。
3. 字段名、枚举、单位和范围严格遵守本文档。
4. STM32 只发送已经计算完成的结果，APP 只解析和展示。
