## 视觉追踪文件对照

| 位置 | 对应部分 | 看什么 |
| --- | --- | --- |
| [相机识别与UDP发送.py](maixcam%E7%AB%AF/%E5%9C%A8maixvision%E4%B8%AD%E8%BF%90%E8%A1%8C%20%20pkq_%E8%AF%86%E5%88%AB_UDP%E5%8F%91%E9%80%81.py) | 相机端 | 计算目标 dx/dy，通过 UDP 发送 TARGET／LOST |
| [pc端GUI/GUI.py](pc%E7%AB%AFGUI/GUI.py) | 电脑控制端 | 接收坐标、显示偏差、PID 与串口命令 |
| [docs/02_硬件准备与接线.md](docs/02_%E7%A1%AC%E4%BB%B6%E5%87%86%E5%A4%87%E4%B8%8E%E6%8E%A5%E7%BA%BF.md) | 硬件接线 | 相机、ESP32-S3 与电机的连接 |
| [docs/05_ESP32固件与串口协议.md](docs/05_ESP32%E5%9B%BA%E4%BB%B6%E4%B8%8E%E4%B8%B2%E5%8F%A3%E5%8D%8F%E8%AE%AE.md) | 执行端协议 | 电脑到 ESP32 的 M／P 命令 |
| [docs/06_参数调试与PID入门.md](docs/06_%E5%8F%82%E6%95%B0%E8%B0%83%E8%AF%95%E4%B8%8EPID%E5%85%A5%E9%97%A8.md) | PID 联调 | 方向、死区、增益与动作幅度 |

PC 先用 dry-run 对照坐标和命令，再按原说明连接执行机构。

---

> **代码公开版：** 本仓库不附带模型权重或采集数据。下文涉及的 `.mud`／`.cvimodel` 文件须从你自己的训练任务导出，并按代码配置的路径部署。

# 视觉追踪二维云台

这是一个“让二维云台自动追踪目标”的小项目。当前示例目标是皮卡丘玩偶：

1. MaixCAM Pro 负责看画面，用训练好的 YOLO 模型识别皮卡丘。
2. MaixCAM Pro 把目标偏离画面中心的坐标通过 UDP 发给电脑。
3. 电脑端 GUI 接收坐标，显示目标位置，并用 PID 算法计算电机该转多少。
4. 电脑通过串口把运动命令发给 ESP32-S3。
5. ESP32-S3 输出 STEP/DIR 脉冲，驱动 X/Y 两个闭环步进电机，让云台对准目标。

## 项目目录

```text
视觉追踪二维云台
├─ maixcam端
│  ├─ 在maixvision中运行  pkq_识别_UDP发送.py
│  └─ 训练好的模型，直接复制进models
│     ├─ model_280927.mud
│     └─ model_280927.cvimodel
├─ pc端GUI
│  └─ GUI.py
└─ docs
   ├─ 01_项目原理.md
   ├─ 02_硬件准备与接线.md
   ├─ 03_MaixCAM端使用.md
   ├─ 04_PC端GUI使用.md
   ├─ 05_ESP32固件与串口协议.md
   ├─ 06_参数调试与PID入门.md
   └─ 07_常见问题.md
```

## 你需要准备什么

- MaixCAM Pro 一块，用来做视觉识别。
- ESP32-S3 一块，用来输出电机控制脉冲。
- 两个支持 STEP/DIR 脉冲控制的闭环步进电机和对应供电。
- 一台 Windows 电脑。
- MaixVision，用来运行 MaixCAM 端代码。
- Python 3，用来运行电脑端 GUI。
- 已经烧录好匹配串口协议的 ESP32-S3 固件。

注意：当前开源包里主要包含 MaixCAM 端和 PC 端 GUI。ESP32-S3 需要运行能识别 `M x y` 和 `P us` 命令的电机控制固件，协议说明见 [05_ESP32固件与串口协议.md](docs/05_ESP32固件与串口协议.md)。

## 最快跑通流程

1. 把 `maixcam端/训练好的模型，直接复制进models/` 里的两个模型文件复制到 MaixCAM Pro 的 `/root/models/` 目录。
2. 在 MaixVision 中打开 `maixcam端/在maixvision中运行  pkq_识别_UDP发送.py`。
3. 修改代码里的 `PC_IP`，改成电脑在同一个 WiFi/热点下的 IPv4 地址。
4. 在电脑上安装依赖：

```powershell
pip install pyserial
```

5. 运行电脑端 GUI：

```powershell
python ".\pc端GUI\GUI.py"
```

6. GUI 里先启动 UDP 监听，保持 `dry-run` 打开。
7. 在 MaixVision 运行 MaixCAM 端代码，确认 GUI 能看到目标坐标变化。
8. 确认电机接线和供电无误后，连接 ESP32-S3 串口。
9. 关闭 `dry-run`，连接 ESP32，启用自动锁定。

第一次测试一定先用 `dry-run`，只看坐标和命令，不要直接让电机动。

## 推荐阅读顺序

1. [01_项目原理.md](docs/01_项目原理.md)：先看懂整套系统怎么闭环。
2. [02_硬件准备与接线.md](docs/02_硬件准备与接线.md)：再接线，尤其注意共地和供电。
3. [03_MaixCAM端使用.md](docs/03_MaixCAM端使用.md)：让摄像头能识别并发送坐标。
4. [04_PC端GUI使用.md](docs/04_PC端GUI使用.md)：让电脑能接收坐标、显示轨迹、控制 ESP32。
5. [05_ESP32固件与串口协议.md](docs/05_ESP32固件与串口协议.md)：理解电脑和 ESP32 之间说什么。
6. [06_参数调试与PID入门.md](docs/06_参数调试与PID入门.md)：让云台从“能动”变成“追得稳”。
7. [07_常见问题.md](docs/07_常见问题.md)：遇到没反应、反向、太慢、抖动时查这里。

## 安全提醒

- 电机不要用 ESP32 或 MaixCAM 的 5V/3.3V 供电。
- 电机电源和 ESP32 信号地要共地，否则 STEP/DIR 信号可能不可靠。
- 第一次通电时手放在电源开关附近，随时断电。
- 先空载测试，再装外壳和云台结构。
- 先小速度、小步数测试，确认方向后再提高参数。

