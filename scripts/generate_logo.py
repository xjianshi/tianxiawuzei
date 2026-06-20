from __future__ import annotations

from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ICONSET = ASSETS / "tianxiawuzei.iconset"


def rounded_rectangle_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    return mask


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make_logo(size: int = 1024) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bg = Image.new("RGBA", (size, size), (8, 30, 34, 255))
    mask = rounded_rectangle_mask(size, 220)
    image.alpha_composite(Image.composite(bg, Image.new("RGBA", (size, size)), mask))

    draw = ImageDraw.Draw(image)
    for y in range(size):
        teal = int(28 + 35 * (1 - y / size))
        blue = int(38 + 28 * (y / size))
        draw.line((0, y, size, y), fill=(8, teal, blue, 255))

    # subtle warning halo
    halo = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    halo_draw = ImageDraw.Draw(halo)
    halo_draw.ellipse((210, 150, 814, 754), outline=(225, 38, 51, 90), width=34)
    halo = halo.filter(ImageFilter.GaussianBlur(12))
    image.alpha_composite(halo)

    # shield
    shield = [
        (512, 150),
        (780, 258),
        (728, 666),
        (512, 842),
        (296, 666),
        (244, 258),
    ]
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.polygon([(x + 16, y + 18) for x, y in shield], fill=(0, 0, 0, 95))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    image.alpha_composite(shadow)

    draw = ImageDraw.Draw(image)
    draw.polygon(shield, fill=(215, 226, 224, 255), outline=(255, 255, 255, 230))
    inner = [(512, 216), (704, 294), (668, 626), (512, 754), (356, 626), (320, 294)]
    draw.polygon(inner, fill=(30, 61, 65, 255))

    # red alert core
    draw.ellipse((416, 334, 608, 526), fill=(224, 36, 48, 255))
    draw.ellipse((456, 374, 568, 486), fill=(255, 88, 82, 255))

    # Chinese character
    fnt = font(218)
    text = "警"
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tx = (size - (bbox[2] - bbox[0])) // 2 - bbox[0]
    ty = 522 - (bbox[3] - bbox[1]) // 2 - bbox[1]
    draw.text((tx + 5, ty + 7), text, font=fnt, fill=(0, 0, 0, 120))
    draw.text((tx, ty), text, font=fnt, fill=(246, 248, 244, 255))

    # bottom alert bar
    draw.rounded_rectangle((360, 760, 664, 808), radius=24, fill=(224, 36, 48, 255))
    draw.rounded_rectangle((404, 774, 620, 794), radius=10, fill=(255, 215, 128, 255))
    return image


def write_iconset(logo: Image.Image) -> None:
    ICONSET.mkdir(parents=True, exist_ok=True)
    specs = [
        ("icon_16x16.png", 16),
        ("icon_16x16@2x.png", 32),
        ("icon_32x32.png", 32),
        ("icon_32x32@2x.png", 64),
        ("icon_128x128.png", 128),
        ("icon_128x128@2x.png", 256),
        ("icon_256x256.png", 256),
        ("icon_256x256@2x.png", 512),
        ("icon_512x512.png", 512),
        ("icon_512x512@2x.png", 1024),
    ]
    for name, size in specs:
        logo.resize((size, size), Image.Resampling.LANCZOS).save(ICONSET / name)


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    logo = make_logo()
    logo.save(ASSETS / "logo.png")
    write_iconset(logo)
    subprocess.run(["iconutil", "-c", "icns", str(ICONSET), "-o", str(ASSETS / "tianxiawuzei.icns")], check=True)
    print(ASSETS / "logo.png")
    print(ASSETS / "tianxiawuzei.icns")


if __name__ == "__main__":
    main()

