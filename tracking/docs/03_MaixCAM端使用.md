> **代码公开版：** 本仓库不附带模型权重或采集数据。下文涉及的 `.mud`／`.cvimodel` 文件须从你自己的训练任务导出，并按代码配置的路径部署。

# MaixCAM 端使用

MaixCAM Pro 的作用是识别皮卡丘，并把目标相对画面中心的偏差发给电脑。

## 需要的软件

使用 MaixVision 打开并运行：

```text
maixcam端/在maixvision中运行  pkq_识别_UDP发送.py
```

## 复制模型文件

把下面两个文件复制到 MaixCAM Pro 的 `/root/models/` 目录：

```text
model_280927.mud
model_280927.cvimodel
```

最终路径应该是：

```text
/root/models/model_280927.mud
/root/models/model_280927.cvimodel
```

代码里使用的是：

```python
MODEL_PATH = "/root/models/model_280927.mud"
```

如果路径不对，运行时会出现类似：

```text
model path ... not exists
```

## 设置电脑 IP

MaixCAM 需要知道电脑的 IPv4 地址，才能把 UDP 数据发过去。

Windows 查看 IP：

```powershell
ipconfig
```

找到正在使用的网卡，比如 `无线局域网适配器 WLAN`，看这一行：

```text
IPv4 地址 . . . . . . . . . . . . : 192.168.xxx.xxx
```

然后把 MaixCAM 端代码里的 `PC_IP` 改成这个地址：

```python
PC_IP = "192.0.2.10"
PC_PORT = 8899
```

注意：MaixCAM Pro 和电脑必须在同一个 WiFi 或同一个手机热点下。

## 关键参数解释

```python
CONF_TH = 0.5
IOU_TH = 0.45
SEND_INTERVAL_MS = 50
```

含义：

- `CONF_TH`：置信度阈值。越高越严格，误识别更少，但可能更容易丢目标。
- `IOU_TH`：目标框重叠处理阈值。一般保持默认即可。
- `SEND_INTERVAL_MS`：发送间隔。50 ms 约等于每秒发送 20 次坐标。

## 坐标反向设置

代码里有：

```python
SEND_INVERT_X = True
SEND_INVERT_Y = True
```

如果你看到：

- 皮卡丘实际在左边，但 GUI 显示在右边。
- 皮卡丘实际在下边，但 GUI 显示在上边。

就说明坐标方向反了，可以调整这两个开关。

建议优先只在一个地方改反向：

- 要么改 MaixCAM 端的 `SEND_INVERT_X/Y`。
- 要么改 PC GUI 里的 X/Y 反向。

不要两个地方同时乱改，否则容易越改越乱。

## MaixCAM 发送的数据格式

识别到目标时发送：

```text
TARGET,dx,dy,score
```

例子：

```text
TARGET,-24,16,0.887
```

没有识别到目标时发送：

```text
LOST
```

## 屏幕上画了什么

MaixCAM 屏幕显示：

- 蓝色十字：画面中心，也就是云台要对准的位置。
- 红色框：模型识别到的目标框。
- 绿色十字：目标中心。
- 黄色线：从画面中心指向目标中心。
- `dx/dy`：目标相对中心的偏差。
- `score`：识别置信度。

## 常见错误

### 模型不存在

现象：

```text
model exists: False
```

处理：

- 检查模型是否复制到了 `/root/models/`。
- 检查文件名是否完全一致。
- 确认 `.mud` 和 `.cvimodel` 都在。

### GUI 收不到数据

处理：

- 确认 MaixCAM 和电脑在同一网络。
- 确认 `PC_IP` 是电脑 WLAN 的 IPv4 地址。
- 确认 PC GUI 已经启动 UDP 监听。
- 确认端口都是 `8899`。
- Windows 防火墙弹窗时允许 Python 访问网络。

