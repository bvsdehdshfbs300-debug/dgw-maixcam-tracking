from maix import camera, display, image, nn, app
import os

model_path = "/root/models/model_280927.mud"

print("model exists:", os.path.exists(model_path))

detector = nn.YOLOv5(model=model_path)

cam = camera.Camera(
      detector.input_width(),
      detector.input_height(),
      detector.input_format()
  )
disp = display.Display()

while not app.need_exit():
      img = cam.read()
      objs = detector.detect(img, conf_th=0.5, iou_th=0.45)

      for obj in objs:
          img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)

          cx = obj.x + obj.w // 2
          cy = obj.y + obj.h // 2
          img.draw_cross(cx, cy, color=image.COLOR_GREEN, size=12)

          msg = f"{detector.labels[obj.class_id]} {obj.score:.2f}"
          img.draw_string(obj.x, obj.y, msg, color=image.COLOR_RED)

      disp.show(img)