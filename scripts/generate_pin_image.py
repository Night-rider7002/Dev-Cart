#!/usr/bin/env python3
"""
generate_pin_image.py
Usage: python3 generate_pin_image.py "<image_url>" "<title_text>" "<output_path>"
Output: Saves JPEG to output_path, prints path to stdout.

Dependencies: pip install pillow requests
"""

import sys
import os
import json
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PIN_W, PIN_H = 1000, 1500
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # pre-installed in most Linux Docker images
FALLBACK_FONT_SIZE = 48
GRADIENT_STRENGTH = 200  # 0-255 alpha at darkest


def download_image(url: str) -> Image.Image:
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    img = Image.open(BytesIO(resp.content)).convert("RGB")
    return img


def fit_and_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Scale-to-fill then center-crop. Avoids distortion."""
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def add_gradient_overlay(img: Image.Image) -> Image.Image:
    """Bottom-up dark gradient for text legibility."""
    gradient = Image.new("L", (PIN_W, PIN_H), 0)
    draw = ImageDraw.Draw(gradient)
    for y in range(PIN_H):
        # Linear ramp: top=transparent, bottom=GRADIENT_STRENGTH
        alpha = int((y / PIN_H) ** 2 * GRADIENT_STRENGTH)
        draw.line([(0, y), (PIN_W, y)], fill=alpha)

    black_layer = Image.new("RGB", (PIN_W, PIN_H), (0, 0, 0))
    img = Image.composite(black_layer, img, gradient)
    return img


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = font.getbbox(test)
        if bbox[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def render_text(img: Image.Image, title: str) -> Image.Image:
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(FONT_PATH, FALLBACK_FONT_SIZE)
    except IOError:
        font = ImageFont.load_default()

    margin = 60
    max_text_width = PIN_W - (margin * 2)
    lines = wrap_text(title, font, max_text_width)

    line_height = FALLBACK_FONT_SIZE + 12
    total_text_height = len(lines) * line_height
    y_start = PIN_H - total_text_height - 80  # 80px from bottom

    for line in lines:
        bbox = font.getbbox(line)
        x = (PIN_W - (bbox[2] - bbox[0])) // 2  # center-aligned
        # Drop shadow for contrast
        draw.text((x + 2, y_start + 2), line, font=font, fill=(0, 0, 0, 180))
        draw.text((x, y_start), line, font=font, fill=(255, 255, 255, 255))
        y_start += line_height

    return img


def add_brand_badge(img: Image.Image, label: str = "🎓 Hostel Engineer Picks") -> Image.Image:
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(FONT_PATH, 28)
    except IOError:
        font = ImageFont.load_default()

    pad_x, pad_y = 20, 10
    bbox = font.getbbox(label)
    rect_x1, rect_y1 = 40, 40
    rect_x2 = rect_x1 + bbox[2] + pad_x * 2
    rect_y2 = rect_y1 + bbox[3] + pad_y * 2

    draw.rounded_rectangle([rect_x1, rect_y1, rect_x2, rect_y2], radius=8, fill=(255, 90, 0))
    draw.text((rect_x1 + pad_x, rect_y1 + pad_y), label, font=font, fill=(255, 255, 255))
    return img


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(json.dumps({"error": "Usage: script.py <image_url> <title> <output_path>"}))
        sys.exit(1)

    image_url, title, output_path = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        img = download_image(image_url)
        img = fit_and_crop(img, PIN_W, PIN_H)
        img = add_gradient_overlay(img)
        img = render_text(img, title)
        img = add_brand_badge(img)
        img.save(output_path, "JPEG", quality=92, optimize=True)
        print(json.dumps({"output_path": output_path, "error": None}))
    except Exception as e:
        print(json.dumps({"output_path": None, "error": str(e)}))
        sys.exit(1)
