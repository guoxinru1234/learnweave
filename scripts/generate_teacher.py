# backend/scripts/generate_teacher.py
from PIL import Image, ImageDraw
import os

def create_teacher_silhouette():
    """生成一个简单的老师剪影 PNG（透明背景）"""
    width, height = 300, 400
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 颜色：深灰色（像黑板前的老师剪影）
    color = (50, 50, 60, 220)

    # 头（圆形）
    head_radius = 40
    head_center = (width // 2, 100)
    draw.ellipse(
        [head_center[0] - head_radius, head_center[1] - head_radius,
         head_center[0] + head_radius, head_center[1] + head_radius],
        fill=color
    )

    # 身体（梯形/矩形）
    body_left = width // 2 - 55
    body_right = width // 2 + 55
    body_top = 130
    body_bottom = 330
    draw.rectangle([body_left, body_top, body_right, body_bottom], fill=color)

    # 左臂
    draw.line([body_left, 160, body_left - 50, 220], fill=color, width=20)
    # 右臂（拿粉笔/指黑板）
    draw.line([body_right, 160, body_right + 60, 190], fill=color, width=20)

    # 腿
    draw.line([body_left + 10, body_bottom, body_left, 390], fill=color, width=18)
    draw.line([body_right - 10, body_bottom, body_right, 390], fill=color, width=18)

    # 保存
    os.makedirs("media/images", exist_ok=True)
    img.save("media/images/teacher_silhouette.png")
    print("✅ 老师剪影已生成: media/images/teacher_silhouette.png")
    return "media/images/teacher_silhouette.png"

if __name__ == "__main__":
    create_teacher_silhouette()