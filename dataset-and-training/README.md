## 采集与模型流程文件对照

| 位置 | 对应部分 | 看什么 |
| --- | --- | --- |
| [拍照.py](%E6%8B%8D%E7%85%A7.py) | 采集数据集 | 点击触屏拍摄并保存目标图片 |
| [皮卡丘识别.py](%E7%9A%AE%E5%8D%A1%E4%B8%98%E8%AF%86%E5%88%AB.py) | 单独运行识别 | 加载自己的模型并显示目标框 |
| [docs/02_用MaixCAM采集数据集.md](docs/02_%E7%94%A8MaixCAM%E9%87%87%E9%9B%86%E6%95%B0%E6%8D%AE%E9%9B%86.md) | 采集操作 | 准备目标、拍图和导出 |
| [docs/03_MaixHub创建数据集与标注.md](docs/03_MaixHub%E5%88%9B%E5%BB%BA%E6%95%B0%E6%8D%AE%E9%9B%86%E4%B8%8E%E6%A0%87%E6%B3%A8.md) | 标注 | 数据集与目标框 |
| [docs/04_MaixHub训练模型.md](docs/04_MaixHub%E8%AE%AD%E7%BB%83%E6%A8%A1%E5%9E%8B.md) | 训练 | 从标注进入训练任务 |
| [docs/05_部署模型到MaixCAMPro.md](docs/05_%E9%83%A8%E7%BD%B2%E6%A8%A1%E5%9E%8B%E5%88%B0MaixCAMPro.md) | 部署 | 把自己的模型放回相机 |

这部分对应采图、训练和独立识别；自动控制云台的接入见 ../tracking/README.md。

---

> **代码公开版：** 本仓库不附带模型权重或采集数据。下文涉及的 `.mud`／`.cvimodel` 文件须从你自己的训练任务导出，并按代码配置的路径部署。

# MaixCAM Pro 视觉识别模型训练与运行示例

这个开源文件夹演示了一个完整的新手流程：

1. 用 MaixCAM Pro 采集自己的图片数据集。
2. 在 MaixHub 创建数据集。
3. 给图片标注目标框。
4. 在线训练视觉识别模型。
5. 把训练好的模型放回 MaixCAM Pro。
6. 用 MaixPy 代码实时识别目标。

当前示例目标是“皮卡丘玩偶”，但你可以换成自己的目标，比如积木、小车、杯子、零件、手势等。

## 文件夹内容

```text
视觉识别模型代码开源
├─ 拍照.py
├─ 皮卡丘识别.py
├─ 模型示例
│  ├─ model_280927.mud
│  └─ model_280927.cvimodel
└─ docs
   ├─ 01_先看懂整体流程.md
   ├─ 02_用MaixCAM采集数据集.md
   ├─ 03_MaixHub创建数据集与标注.md
   ├─ 04_MaixHub训练模型.md
   ├─ 05_部署模型到MaixCAMPro.md
   ├─ 06_代码中必须按实际情况修改的地方.md
   └─ 07_常见问题.md
```

## 两个 Python 文件分别做什么

### `拍照.py`

运行在 MaixCAM Pro 上，用来采集训练图片。

功能：

- 打开摄像头。
- 屏幕显示实时画面。
- 点击触摸屏拍一张照片。
- 自动保存到 MaixCAM Pro 的 `/root/datasets/target/`。
- 文件名自动递增，例如 `target_00000.jpg`、`target_00001.jpg`。

### `皮卡丘识别.py`

运行在 MaixCAM Pro 上，用来加载训练好的模型并实时识别。

功能：

- 加载 `/root/models/model_280927.mud`。
- 使用 `nn.YOLOv5` 进行目标检测。
- 在屏幕上画出目标框。
- 在目标中心画十字。
- 显示类别名和置信度。

## 最快上手流程

1. 用 MaixVision 打开并运行 `拍照.py`。
2. 拍摄你的目标图片，建议先拍 100 到 300 张。
3. 把图片从 MaixCAM Pro 导出到电脑。
4. 打开 MaixHub：<https://maixhub.com/>
5. 创建图像检测数据集。
6. 上传图片。
7. 给每张含目标的图片画框并填写类别名。
8. 创建训练任务，平台选择 MaixCAM，模型类型选择目标检测。
9. 训练完成后下载模型文件。
10. 把 `.mud` 和 `.cvimodel` 放到 MaixCAM Pro 的 `/root/models/`。
11. 修改 `皮卡丘识别.py` 里的模型路径。
12. 运行 `皮卡丘识别.py`，测试识别效果。

## 新手推荐阅读顺序

1. [01_先看懂整体流程.md](docs/01_先看懂整体流程.md)
2. [02_用MaixCAM采集数据集.md](docs/02_用MaixCAM采集数据集.md)
3. [03_MaixHub创建数据集与标注.md](docs/03_MaixHub创建数据集与标注.md)
4. [04_MaixHub训练模型.md](docs/04_MaixHub训练模型.md)
5. [05_部署模型到MaixCAMPro.md](docs/05_部署模型到MaixCAMPro.md)
6. [06_代码中必须按实际情况修改的地方.md](docs/06_代码中必须按实际情况修改的地方.md)
7. [07_常见问题.md](docs/07_常见问题.md)

## 官方参考资料

- MaixHub 官网：<https://maixhub.com/>
- Sipeed MaixHub 训练说明：<https://wiki.sipeed.com/maixpy/doc/zh/vision/maixhub_train.html>
- MaixPy YOLO 目标检测说明：<https://en.wiki.sipeed.com/maixpy/doc/en/vision/yolov5.html>

