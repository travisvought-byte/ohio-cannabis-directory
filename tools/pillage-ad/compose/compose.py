"""Cut the Pillage the Reefer promo from the recorded gameplay.

Reads 1620px scene recordings and their pointer tracks, zooms and pans in,
crossfades, draws the pointer and the text cards, and writes a square
1080x1080 video and a vertical 1080x1920 one (silent; audio is muxed after).
"""
import json, math, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import overlays as ov

SRC = '/home/user/reefer/tools/pillage-ad/out'
FPS, OUT = 30, 1080
CSS = 540  # the recorder's viewport, in CSS pixels


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


class Clip:
    """A run of frames from one scene, with a camera move.

    cam(t) gives (zoom, cx, cy) with cx, cy as fractions of the source frame, t from 0 to 1.
    """

    def __init__(self, scene, start, n, cam=None, cursor=True, hold_last=0, cursor_off=None):
        self.scene, self.start, self.n, self.cursor, self.cursor_off = scene, start, n, cursor, cursor_off
        self.cam = cam or (lambda t: (1.0, 0.5, 0.5))
        self.hold_last = hold_last
        self.proc = None
        self.size = None
        self.last = None
        try:
            self.track = json.load(open(f'{SRC}/{scene}.cursor.json'))
        except FileNotFoundError:
            self.track = []
        self.vis = self._smooth_on()

    def _smooth_on(self):
        on = [t[2] for t in self.track]
        out = []
        for i in range(len(on)):
            # fade the pointer in over 5 frames and out over 6
            if on[i]:
                k = 0
                while k < 5 and i - k - 1 >= 0 and on[i - k - 1]:
                    k += 1
                out.append(min(1.0, (k + 1) / 5))
            else:
                k = 0
                while k < 6 and i - k - 1 >= 0 and not on[i - k - 1]:
                    k += 1
                out.append(max(0.0, 1 - (k + 1) / 6) if i - k - 1 >= 0 and on[i - k - 1] else 0.0)
        return out

    def open(self):
        probe = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', f'{SRC}/{self.scene}.mp4']).decode().strip().split(',')
        self.size = int(probe[0])
        end = self.start + self.n
        self.proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', f'{SRC}/{self.scene}.mp4', '-vf', f'trim=start_frame={self.start}:end_frame={end},setpts=PTS-STARTPTS',
                                      '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)

    def frame(self, i):
        """Frame i of the clip (0-based), already framed to 1080x1080."""
        if self.proc is None:
            self.open()
        S = self.size
        if i < self.n:
            buf = self.proc.stdout.read(S * S * 3)
            if len(buf) == S * S * 3:
                self.last = Image.frombuffer('RGB', (S, S), buf)
        src = self.last
        t = i / max(1, self.n + self.hold_last - 1)
        z, cx, cy = self.cam(t)
        w = S / z
        x0 = min(max(0, cx * S - w / 2), S - w)
        y0 = min(max(0, cy * S - w / 2), S - w)
        img = src.resize((OUT, OUT), Image.LANCZOS, box=(x0, y0, x0 + w, y0 + w))
        if self.cursor and self.track:
            si = min(self.start + min(i, self.n - 1), len(self.track) - 1)
            x, y, on, age = self.track[si]
            a = self.vis[si] if si < len(self.vis) else 0
            if self.cursor_off is not None and si > self.cursor_off:
                a *= max(0.0, 1 - (si - self.cursor_off) / 6)
            if a > 0.01:
                k = OUT / w
                px, py = (x * S / CSS - x0) * k, (y * S / CSS - y0) * k
                img = draw_pointer(img, px, py, a, age, z)
        return img

    def close(self):
        if self.proc:
            self.proc.stdout.close()
            self.proc.wait()


def draw_pointer(img, x, y, alpha, age, zoom):
    """A fingertip: a soft white dot with a dark ring, and a ripple when it taps."""
    r = 25 * min(1.35, max(1.0, zoom * 0.8))
    lay = Image.new('RGBA', (OUT, OUT), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    press = 1.0
    if 0 <= age <= 6:
        press = 0.82 + 0.18 * ease(age / 6)
    rr = r * press
    if 0 <= age <= 16:
        k = age / 16
        R = rr + 60 * ease(k)
        d.ellipse((x - R, y - R, x + R, y + R), outline=(255, 255, 255, int(230 * (1 - k) * alpha)), width=5)
    sh = Image.new('RGBA', (OUT, OUT), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((x - rr + 3, y - rr + 6, x + rr + 3, y + rr + 6), fill=(0, 0, 0, int(110 * alpha)))
    sh = sh.filter(ImageFilter.GaussianBlur(6))
    lay = Image.alpha_composite(sh, lay)
    d = ImageDraw.Draw(lay)
    d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(255, 255, 255, int(150 * alpha)), outline=(20, 40, 32, int(220 * alpha)), width=4)
    out = img.convert('RGBA')
    out.alpha_composite(lay)
    return out.convert('RGB')


class Card:
    """A text card on the timeline: rises in, holds, fades out."""

    def __init__(self, img, t_in, t_out, rise=26):
        self.img, self.t_in, self.t_out, self.rise = img, t_in, t_out, rise

    def apply(self, frame, t):
        if t < self.t_in or t >= self.t_out:
            return frame
        k_in = ease((t - self.t_in) / 10)
        k_out = ease((self.t_out - t) / 8)
        a = min(k_in, k_out)
        dy = int(round(self.rise * (1 - k_in)))
        lay = self.img
        if a < 0.999:
            r, g, b, al = lay.split()
            lay = Image.merge('RGBA', (r, g, b, al.point(lambda v: int(v * a))))
        out = frame.convert('RGBA')
        out.alpha_composite(lay, (0, dy) if dy >= 0 else (0, 0))
        return out.convert('RGB')


class EndCard:
    def __init__(self, img, t_in):
        self.img, self.t_in = img, t_in

    def apply(self, frame, t):
        if t < self.t_in:
            return frame
        k = ease((t - self.t_in) / 14)
        base = frame.filter(ImageFilter.GaussianBlur(2 + 8 * k))
        lay = self.img
        s = 1.05 - 0.05 * ease((t - self.t_in) / 22)
        if abs(s - 1) > 0.001:
            sz = int(OUT * s)
            lay = lay.resize((sz, sz), Image.BICUBIC)
            off = (sz - OUT) // 2
            lay = lay.crop((off, off, off + OUT, off + OUT))
        if k < 0.999:
            r, g, b, al = lay.split()
            lay = Image.merge('RGBA', (r, g, b, al.point(lambda v: int(v * k))))
        out = base.convert('RGBA')
        out.alpha_composite(lay)
        return out.convert('RGB')


def render(timeline, cards, total, out_sq, out_vert=None, xfade=8):
    """timeline: list of clips played back to back with `xfade`-frame crossfades."""
    starts, t = [], 0
    for c in timeline:
        starts.append(t)
        t += c.n + c.hold_last - xfade
    enc = lambda path, w, h: subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(FPS), '-i', '-',
                                               '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', path], stdin=subprocess.PIPE)
    sq = enc(out_sq, OUT, OUT)
    vt = enc(out_vert, 1080, 1920) if out_vert else None
    vert_frame = VerticalFrame() if out_vert else None
    for f in range(total):
        layers = []
        for c, s in zip(timeline, starts):
            L = c.n + c.hold_last
            if s <= f < s + L:
                layers.append((c, f - s, s, L))
        if not layers:
            layers = [(timeline[-1], f - starts[-1], starts[-1], timeline[-1].n + timeline[-1].hold_last)]
        img = layers[0][0].frame(layers[0][1])
        if len(layers) > 1:
            c2, i2, s2, _ = layers[1]
            k = ease((f - s2 + 1) / (xfade + 1))
            img = Image.blend(img, c2.frame(i2), k)
        for cd in cards:
            img = cd.apply(img, f)
        sq.stdin.write(img.tobytes())
        if vt:
            vt.stdin.write(vert_frame.make(img, f).tobytes())
        if f % 60 == 0:
            print('frame', f, '/', total, flush=True)
    for c in timeline:
        c.close()
    sq.stdin.close(); sq.wait()
    if vt:
        vt.stdin.close(); vt.wait()


VERTICAL_LINE = 'Free to play in your browser'


class VerticalFrame:
    """The square video in the middle of a 9:16 frame, over a blurred copy of itself, with the name above and the address below."""

    def __init__(self):
        self.top = Image.new('RGBA', (1080, 420), (0, 0, 0, 0))
        d = ImageDraw.Draw(self.top)
        logo = Image.open('/home/user/reefer/assets/the-reefer/flag-900.webp').convert('RGBA')
        lw = 250
        logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
        self.top.alpha_composite(logo, ((1080 - lw) // 2, 70))
        ft = ov.font(ov.CALADEA, 74)
        t = 'Pillage the Reefer'
        y = 70 + logo.height + 6
        d.text(((1080 - d.textlength(t, font=ft)) / 2 + 3, y + 4), t, font=ft, fill=(0, 0, 0, 150))
        d.text(((1080 - d.textlength(t, font=ft)) / 2, y), t, font=ft, fill=ov.CREAM)
        self.bot = Image.new('RGBA', (1080, 420), (0, 0, 0, 0))
        d = ImageDraw.Draw(self.bot)
        f2 = ov.font(ov.INTER_B, 40)
        t = VERTICAL_LINE
        d.text(((1080 - d.textlength(t, font=f2)) / 2, 74), t, font=f2, fill=ov.CREAM)
        fu = ov.font(ov.INTER_XB, 54)
        t = 'the-reefer.com/pillage'
        tw = d.textlength(t, font=fu)
        d.rounded_rectangle(((1080 - tw) / 2 - 32, 150, (1080 + tw) / 2 + 32, 238), 44, fill=ov.GOLD + (255,))
        d.text(((1080 - tw) / 2, 160), t, font=fu, fill=(26, 22, 8))

    def make(self, sq, f):
        bg = sq.resize((240, 240), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5)).resize((1920, 1920), Image.BICUBIC).crop((420, 0, 1500, 1920))
        bg = Image.blend(bg, Image.new('RGB', bg.size, (6, 22, 18)), 0.55).convert('RGBA')
        bg.alpha_composite(self.top, (0, 0))
        bg.alpha_composite(self.bot, (0, 1500))
        bg = bg.convert('RGB')
        bg.paste(sq, (0, 420))
        return bg


if __name__ == '__main__':
    print('import me')
