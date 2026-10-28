"""Renders design-system previews (palette + type specimen) from tokens.json and the fonts in this repo.

usage: python tools/make_previews.py            (run from the repo root)
needs: pip install pillow
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
TOK = json.loads((ROOT / "tokens" / "tokens.json").read_text(encoding="utf-8"))
DISPLAY = str(ROOT / "fonts" / "BugWarDisplay-Regular.ttf")
BODY = str(ROOT / "fonts" / "Rubik-Black.ttf")
S = 2


def hx(v):
    v = v.lstrip("#")
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


C = {f"{g}.{k}": hx(v["value"]) for g, grp in TOK["color"].items() for k, v in grp.items()}


def styled(text, font, fill, slant=0.0, outline=2, shadow=3):
    o, sh = outline * S, shadow * S
    bb = font.getbbox(text, stroke_width=o)
    w, h = bb[2] - bb[0] + 4 * S, bb[3] - bb[1] + sh + 4 * S
    img = Image.new("RGBA", (w + int(h * abs(slant)) + 4 * S, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x, y = 2 * S - bb[0], 2 * S - bb[1]
    d.text((x, y + sh), text, font=font, fill=C["text.shadow"], stroke_width=o, stroke_fill=C["text.shadow"])
    d.text((x, y), text, font=font, fill=fill, stroke_width=o, stroke_fill=C["text.outline"])
    if slant:
        img = img.transform(img.size, Image.AFFINE, (1, slant, -slant * h, 0, 1, 0), resample=Image.BICUBIC)
    return img


def panel(d, box, face, lip, r, lipw, edge=None):
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0 + lipw, x1, y1 + lipw], r, fill=lip)
    d.rounded_rectangle([x0, y0, x1, y1], r, fill=face)
    if edge:
        d.line([x0 + r, y0 + S, x1 - r, y0 + S], fill=edge, width=2 * S)


def meta_font(size):
    return ImageFont.truetype(BODY, size * S)


def palette(out):
    groups = [(g, list(grp.items())) for g, grp in TOK["color"].items()]
    W = 1600
    rows = sum((len(items) + 5) // 6 for _, items in groups)
    H = 110 + rows * 150 + len(groups) * 50
    img = Image.new("RGBA", (W * S, H * S), C["background.base"] + (255,))
    d = ImageDraw.Draw(img)
    img.alpha_composite(styled("Палитра · Deep Teal & Honey", ImageFont.truetype(DISPLAY, 44 * S), C["text.primary"], 0.12), (30 * S, 24 * S))
    y = 100
    for g, items in groups:
        d.text((30 * S, y * S), g.upper(), font=meta_font(18), fill=C["text.muted"])
        y += 34
        for i, (k, v) in enumerate(items):
            col, row = i % 6, i // 6
            x0, y0 = 30 + col * 258, y + row * 150
            panel(d, (x0 * S, y0 * S, (x0 + 240) * S, (y0 + 80) * S), hx(v["value"]), C["surface.panelLip"], 14 * S, 5 * S)
            d.text((x0 * S, (y0 + 92) * S), f"{g}.{k}", font=meta_font(16), fill=C["text.primary"])
            d.text((x0 * S, (y0 + 114) * S), v["value"], font=meta_font(15), fill=C["text.secondary"])
        y += ((len(items) + 5) // 6) * 150 + 16
    img.convert("RGB").resize((W, H), Image.LANCZOS).save(out)


def specimen(out):
    W, H = 1600, 740
    img = Image.new("RGBA", (W * S, H * S), C["background.base"] + (255,))
    d = ImageDraw.Draw(img)
    disp = lambda s: ImageFont.truetype(DISPLAY, s * S)
    img.alpha_composite(styled("BugWar Display", disp(72), C["text.primary"], 0.12, 3, 5), (30 * S, 20 * S))
    d.text((34 * S, 120 * S), "крупные элементы · наклон 0.12 · обводка 2 px · жёсткая тень вниз", font=meta_font(18), fill=C["text.muted"])
    lines = ["АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ", "абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
             "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz", "0123456789 !?.,:;—+-/%"]
    y = 160
    for ln in lines:
        img.alpha_composite(styled(ln, disp(40), C["text.primary"], 0.12), (30 * S, y * S))
        y += 66
    # sample UI
    bx, by, bw, bh = 30, y + 20, 300, 96
    d.rounded_rectangle([bx * S, (by + 6) * S, (bx + bw) * S, (by + bh + 6) * S], 16 * S, fill=C["primary.lip"])
    grad = Image.new("RGBA", (bw * S, bh * S))
    gd = ImageDraw.Draw(grad)
    for yy in range(bh * S):  # smooth vertical gradient top -> bottom
        t = yy / (bh * S - 1)
        gd.line([(0, yy), (bw * S, yy)], fill=tuple(int(a + (b - a) * t) for a, b in zip(C["primary.top"], C["primary.bottom"])) + (255,))
    mask = Image.new("L", (bw * S, bh * S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, bw * S - 1, bh * S - 1], 16 * S, fill=255)
    img.paste(grad, (bx * S, by * S), mask)
    d.ellipse([(bx + bw - 26) * S, (by + 10) * S, (bx + bw - 16) * S, (by + 20) * S], fill=C["primary.spark"])
    b = styled("В БОЙ", disp(52), C["text.primary"], 0.12, 3, 5)
    img.alpha_composite(b, ((bx * S + (bw * S - b.width) // 2), (by * S + (bh * S - b.height) // 2)))
    t = styled("Цветочный луг", disp(48), C["text.primary"], 0.12, 2, 4)
    img.alpha_composite(t, ((bx + bw + 40) * S, (by + 18) * S))
    y2 = by + bh + 40
    d.text((34 * S, y2 * S), "Rubik Black — цифры и мелкий текст · без наклона · обводка 1 px", font=meta_font(18), fill=C["text.muted"])
    for i, (txt, sz) in enumerate([("12 450   320   1240 / 2 000   Миссии 5/10", 30), ("Жуки готовы к бою! Гусеница · Жук-олень", 24)]):
        img.alpha_composite(styled(txt, ImageFont.truetype(BODY, sz * S), C["text.cream"], 0, 1, 2), (30 * S, (y2 + 34 + i * 48) * S))
    img.convert("RGB").resize((W, H), Image.LANCZOS).save(out)


if __name__ == "__main__":
    palette(ROOT / "previews" / "palette.png")
    specimen(ROOT / "previews" / "typography.png")
    print("previews written")
