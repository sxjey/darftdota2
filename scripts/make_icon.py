"""
Генерация иконки приложения.
Создаёт простую тематическую иконку через PIL.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUT_DIR = Path(__file__).parent.parent / "assets"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / "app_icon.ico"


def make_icon():
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []
    
    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Тёмный фон-круг с градиентом
        pad = max(1, size // 16)
        # тень/круг
        draw.ellipse([pad, pad, size - pad, size - pad],
                     fill=(28, 32, 48, 255), outline=(76, 175, 239, 255),
                     width=max(1, size // 32))
        
        # Внутренний градиентный эффект — просто круг чуть светлее в центре
        inner_pad = size // 4
        draw.ellipse([inner_pad, inner_pad, size - inner_pad, size - inner_pad],
                     fill=(45, 52, 75, 255))
        
        # Буква D в центре
        try:
            font_size = int(size * 0.55)
            font = ImageFont.truetype("arialbd.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()
        
        text = "D"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (size - tw) // 2 - bbox[0]
        y = (size - th) // 2 - bbox[1]
        draw.text((x, y), text, fill=(76, 175, 239, 255), font=font)
        
        images.append(img)
    
    # Сохраняем как multi-size ICO
    images[0].save(
        OUT_PATH,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    print(f"✓ Иконка сохранена: {OUT_PATH}")


if __name__ == "__main__":
    make_icon()
