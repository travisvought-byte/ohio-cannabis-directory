"""Text overlays for the Pillage the Reefer promo video (1080x1080)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W = H = 1080
CALADEA = '/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf'
INTER_XB = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
INTER_B = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
INTER_SB = '/usr/share/fonts/opentype/inter/Inter-SemiBold.otf'
CREAM = (251, 243, 223)
GOLD = (233, 185, 73)
DARK = (12, 33, 26)
SOFT = (205, 214, 206)


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, width):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if draw.textlength(t, font=fnt) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def spaced(draw, xy, text, fnt, fill, tracking):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking
    return x


def spaced_len(draw, text, fnt, tracking):
    return sum(draw.textlength(ch, font=fnt) + tracking for ch in text) - tracking


def lower_third(kicker, main, size=54, pos='bottom'):
    """A dark green card with a gold kicker and a cream headline. Returns RGBA 1080x1080."""
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fk, fm = font(INTER_XB, 29), font(CALADEA, size)
    pad_x, inner_w = 44, W - 2 * 36 - 2 * 44
    lines = wrap(d, main, fm, inner_w)
    lh = int(size * 1.17)
    box_h = 34 + 30 + 18 + lh * len(lines) + 30
    x0, x1 = 36, W - 36
    y1 = H - 44 if pos == 'bottom' else 44 + box_h
    y0 = y1 - box_h
    # soft shadow
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((x0 + 4, y0 + 10, x1 + 4, y1 + 12), 26, fill=(0, 0, 0, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    img = Image.alpha_composite(img, sh)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x0, y0, x1, y1), 24, fill=DARK + (238,), outline=GOLD + (255,), width=3)
    d.rounded_rectangle((x0 + 3, y0 + 3, x0 + 14, y1 - 3), 6, fill=GOLD + (255,))
    ty = y0 + 32
    spaced(d, (x0 + pad_x, ty), kicker.upper(), fk, GOLD, 3)
    ty += 30 + 18
    for ln in lines:
        d.text((x0 + pad_x, ty), ln, font=fm, fill=CREAM)
        ty += lh
    return img


def end_card(logo_path):
    """Full-frame end card, drawn over darkened footage. Returns RGBA."""
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    # darken: a vignette from the centre
    vg = Image.new('L', (W, H), 0)
    vd = ImageDraw.Draw(vg)
    for i in range(40):
        r = 900 - i * 18
        vd.ellipse((W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r), fill=150 + i * 2)
    vg = vg.filter(ImageFilter.GaussianBlur(40))
    dark = Image.new('RGBA', (W, H), (6, 18, 14, 255))
    dark.putalpha(vg.point(lambda v: min(235, v + 20)))
    img = Image.alpha_composite(img, dark)
    logo = Image.open(logo_path).convert('RGBA')
    lw = 470
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    img.alpha_composite(logo, ((W - lw) // 2, 96))
    d = ImageDraw.Draw(img)
    y = 96 + logo.height + 6
    ft = font(CALADEA, 92)
    t = 'Pillage the Reefer'
    d.text(((W - d.textlength(t, font=ft)) / 2 + 3, y + 4), t, font=ft, fill=(0, 0, 0, 160))
    d.text(((W - d.textlength(t, font=ft)) / 2, y), t, font=ft, fill=CREAM)
    y += 112
    f2 = font(INTER_B, 40)
    for t in ['A free pirate game in your browser.', 'Jump in and play.']:
        d.text(((W - d.textlength(t, font=f2)) / 2, y), t, font=f2, fill=CREAM)
        y += 54
    y += 22
    fu = font(INTER_XB, 58)
    t = 'the-reefer.com/pillage'
    tw = d.textlength(t, font=fu)
    d.rounded_rectangle(((W - tw) / 2 - 34, y - 10, (W + tw) / 2 + 34, y + 84), 46, fill=GOLD + (255,))
    d.text(((W - tw) / 2, y + 2), t, font=fu, fill=(26, 22, 8))
    y += 120
    f3 = font(INTER_SB, 27)
    t = 'Adults 21+  ·  Real 1718 history, cartoon weed'
    d.text(((W - d.textlength(t, font=f3)) / 2, y), t, font=f3, fill=SOFT)
    return img


def cup_end_card(logo_path):
    """End card for the Silver Cup cut: same look as end_card, with the contest's words."""
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    vg = Image.new('L', (W, H), 0)
    vd = ImageDraw.Draw(vg)
    for i in range(40):
        r = 900 - i * 18
        vd.ellipse((W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r), fill=150 + i * 2)
    vg = vg.filter(ImageFilter.GaussianBlur(40))
    dark = Image.new('RGBA', (W, H), (6, 18, 14, 255))
    dark.putalpha(vg.point(lambda v: min(235, v + 20)))
    img = Image.alpha_composite(img, dark)
    logo = Image.open(logo_path).convert('RGBA')
    lw = 400
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    img.alpha_composite(logo, ((W - lw) // 2, 120))
    d = ImageDraw.Draw(img)
    y = 120 + logo.height + 4
    ft = font(CALADEA, 92)
    t = 'The Silver Cup'
    d.text(((W - d.textlength(t, font=ft)) / 2 + 3, y + 4), t, font=ft, fill=(0, 0, 0, 160))
    d.text(((W - d.textlength(t, font=ft)) / 2, y), t, font=ft, fill=GOLD)
    y += 112
    f2 = font(INTER_B, 40)
    for t in ['Win silver half dollars in Pillage the Reefer,', 'a free pirate game. December 1 to 4.']:
        d.text(((W - d.textlength(t, font=f2)) / 2, y), t, font=f2, fill=CREAM)
        y += 54
    y += 22
    fu = font(INTER_XB, 58)
    t = 'the-reefer.com/pillage'
    tw = d.textlength(t, font=fu)
    d.rounded_rectangle(((W - tw) / 2 - 34, y - 10, (W + tw) / 2 + 34, y + 84), 46, fill=GOLD + (255,))
    d.text(((W - tw) / 2, y + 2), t, font=fu, fill=(26, 22, 8))
    y += 116
    f3 = font(INTER_SB, 27)
    for t in ['Free  ·  No purchase necessary  ·  Adults 21+', 'US only  ·  Rules on the site']:
        d.text(((W - d.textlength(t, font=f3)) / 2, y), t, font=f3, fill=SOFT)
        y += 38
    return img
