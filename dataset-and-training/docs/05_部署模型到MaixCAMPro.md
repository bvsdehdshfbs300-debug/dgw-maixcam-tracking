> **代码公开版：** 本仓库不附带模型权重或采集数据。下文涉及的 `.mud`／`.cvimodel` 文件须从你自己的训练任务导出，并按代码配置的路径部署。

# 部署模型到 MaixCAM Pro

训练完成后，需要把模型文件复制到 MaixCAM Pro，并运行识别代码。

## 复制模型

把训练得到的两个文件复制到 MaixCAM Pro：

```text
/root/models/
```

例如：

```text
/root/models/model_280927.mud
/root/models/model_280927.cvimodel
```

两个文件都要复制。

## 修改识别代码里的模型路径

打开 `皮卡丘识别.py`：

```python
model_path = "/root/models/model_280927.mud"
```

如果你的模型文件叫 `model_123456.mud`，就改成：

```python
model_path = "/root/models/model_123456.mud"
```

路径和文件名必须完全一致。

## 运行识别代码

在 MaixVision 中打开：

```text
皮卡丘识别.py
```

点击运行。

正常情况下，终端会先打印：

```text
model exists: True
```

如果是：

```text
model exists: False
```

说明路径不对或模型没复制到位。

## 屏幕显示内容

识别成功时，MaixCAM Pro 屏幕上会显示：

- 红色矩形框：识别到的目标位置。
- 绿色十字：目标中心点。
- 类别名：模型输出的标签。
- 置信度：模型认为它是目标的把握。

置信度越接近 1，说明模型越确定。

## 代码中的检测阈值

```python
objs = detector.detect(img, conf_th=0.5, iou_th=0.45)
```

参数含义：

- `conf_th=0.5`：置信度低于 0.5 的目标不要。
- `iou_th=0.45`：用于合并重复检测框，一般默认即可。

如果检测不到，可以临时把 `conf_th` 降低：

```python
objs = detector.detect(img, conf_th=0.35, iou_th=0.45)
```

如果误识别太多，可以把 `conf_th` 提高：

```python
objs = detector.detect(img, conf_th=0.65, iou_th=0.45)
```

## YOLOv5、YOLOv8、YOLO11 不能乱混

本项目代码使用：

```python
detector = nn.YOLOv5(model=model_path)
```

如果你在 MaixHub 训练的是 YOLOv5，就保持这样。

如果你下载的是 YOLOv8 模型，可能需要：

```python
detector = nn.YOLOv8(model=model_path)
```

如果你用的是 YOLO11 模型，可能需要：

```python
detector = nn.YOLO11(model=model_path)
```

具体取决于你的模型类型和 MaixPy 版本支持的接口。

