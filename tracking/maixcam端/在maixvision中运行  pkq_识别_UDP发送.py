from maix import camera, display, image, nn, app, time
import os
import socket

MODEL_PATH = "/root/models/model_280927.mud"

# 改成电脑在同一 WiFi/热点下的 IPv4 地址。
PC_IP = "192.0.2.10"
PC_PORT = 8899

CONF_TH = 0.5
IOU_TH = 0.45
SEND_INTERVAL_MS = 50

# 如果 MaixCAM 屏幕上目标在左下，但电脑 GUI 显示到右上，
# 说明视觉坐标和屏幕观感相反。这里先把发送给电脑的 dx/dy 反向。
SEND_INVERT_X = True
SEND_INVERT_Y = True

print("model exists:", os.path.exists(MODEL_PATH))
print("send udp to:", PC_IP, PC_PORT)

detector = nn.YOLOv5(model=MODEL_PATH)

cam = camera.Camera(
    detector.input_width(),
    detector.input_height(),
    detector.input_format()
)
disp = display.Display()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
last_send_ms = 0

while not app.need_exit():
    img = cam.read()
    objs = detector.detect(img, conf_th=CONF_TH, iou_th=IOU_TH)

    img_cx = img.width() // 2
    img_cy = img.height() // 2
    img.draw_cross(img_cx, img_cy, color=image.COLOR_BLUE, size=16)

    best_obj = None
    for obj in objs:
        if best_obj is None or obj.score > best_obj.score:
            best_obj = obj

    now_ms = time.ticks_ms()

    if best_obj:
        obj = best_obj
        cx = obj.x + obj.w // 2
        cy = obj.y + obj.h // 2
        dx = cx - img_cx
        dy = cy - img_cy
        send_dx = -dx if SEND_INVERT_X else dx
        send_dy = -dy if SEND_INVERT_Y else dy

        img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
        img.draw_cross(cx, cy, color=image.COLOR_GREEN, size=12)
        img.draw_line(img_cx, img_cy, cx, cy, color=image.COLOR_YELLOW)
        img.draw_string(5, 5, f"dx={dx}, dy={dy}", color=image.COLOR_GREEN)
        img.draw_string(5, 25, f"send={send_dx},{send_dy}", color=image.COLOR_GREEN)
        img.draw_string(5, 45, f"score={obj.score:.2f}", color=image.COLOR_GREEN)

        if now_ms - last_send_ms >= SEND_INTERVAL_MS:
            msg = f"TARGET,{send_dx},{send_dy},{obj.score:.3f}\n"
            sock.sendto(msg.encode("ascii"), (PC_IP, PC_PORT))
            last_send_ms = now_ms
    else:
        img.draw_string(5, 5, "target lost", color=image.COLOR_RED)
        if now_ms - last_send_ms >= SEND_INTERVAL_MS:
            sock.sendto(b"LOST\n", (PC_IP, PC_PORT))
            last_send_ms = now_ms

    disp.show(img)
