"""The Silver Cup cut: the same frames and sounds as build.py, with the contest's cards and end card."""
import os, sys, subprocess
import compose as C
import overlays as ov
import audio

C.SRC = sys.argv[1] if len(sys.argv) > 1 else C.SRC
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else '/home/user/adwork/render'
LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 else None
os.makedirs(OUTDIR, exist_ok=True)
X = 8  # crossfade frames
C.VERTICAL_LINE = 'The Silver Cup  ·  Win silver, December 1 to 4'


def lerp(a, b, k):
    return a + (b - a) * k


def move(z0, z1, c0, c1):
    """A camera move from zoom z0 at centre c0 to zoom z1 at centre c1."""
    return lambda t: (lerp(z0, z1, C.ease(t)), lerp(c0[0], c1[0], C.ease(t)), lerp(c0[1], c1[1], C.ease(t)))


# scene, first frame, frame count, camera
title = C.Clip('title', 0, 72, move(1.0, 1.06, (0.5, 0.5), (0.5, 0.47)), cursor=False)
sail = C.Clip('sail', 20, 125, move(1.05, 1.2, (0.52, 0.48), (0.6, 0.5)), cursor=False)
market = C.Clip('market', 50, 91, move(1.1, 1.16, (0.5, 0.42), (0.5, 0.40)), cursor_off=116)
hist = C.Clip('tavern', 26, 94, move(1.1, 1.15, (0.5, 0.44), (0.5, 0.40)), cursor=False)
hire = C.Clip('tavern', 140, 96, move(1.1, 1.14, (0.5, 0.44), (0.5, 0.40)), cursor_off=215)
meet = C.Clip('fight', 40, 44, move(1.1, 1.2, (0.55, 0.5), (0.62, 0.5)), cursor=False)
fire = C.Clip('fight', 100, 150, move(1.1, 1.14, (0.5, 0.46), (0.5, 0.42)), cursor_off=187)
away = C.Clip('castoff', 0, 150, move(1.05, 1.15, (0.5, 0.5), (0.5, 0.5)), cursor=False)
timeline = [title, sail, market, hist, hire, meet, fire, away]

starts, t = [], 0
for c in timeline:
    starts.append(t)
    t += c.n + c.hold_last - X
total = t + X
S = dict(zip(['title', 'sail', 'market', 'hist', 'hire', 'meet', 'fire', 'away'], starts))
at = lambda clip, name, src_frame: S[name] + (src_frame - clip.start)

cards = [
    C.Card(ov.lower_third('The Silver Cup  ·  December 1 to 4', 'Win real silver in a free pirate game.'), 14, S['sail'] + 4),
    C.Card(ov.lower_third('Top three captains win', '10, 5 and 1 silver half dollars.'), S['sail'] + 12, S['market'] + 2),
    C.Card(ov.lower_third('True story', 'Every rope and sail was hemp. The word canvas comes from cannabis.'), S['market'] + 10, S['hist'] + 2),
    C.Card(ov.lower_third('Fair and square', 'Every Cup run is replayed move by move before it counts.'), S['hist'] + 10, S['hire'] + 2),
    C.Card(ov.lower_third('Henry Morgan’s trick, 1669', 'Hire a fire ship and send her into the enemy.'), S['hire'] + 10, S['meet'] + 2),
    C.Card(ov.lower_third('Roll the d20', 'A natural 20, and the pirates go up like a bonfire.'), at(fire, 'fire', 167) + 4, S['away'] + 2),
    C.EndCard(ov.cup_end_card('/home/user/reefer/assets/the-reefer/flag-900.webp'), S['away'] + 24),
]

# the game's own sounds where the game plays them: a coin for the purchase, the fanfare for the hire,
# and for the fire ship a boom and the fanfare
fps = C.FPS
events = [
    (at(market, 'market', 96) / fps, 'coin', 4.5),
    (at(hire, 'hire', 195) / fps, 'fanfare', 2.6),
    (at(fire, 'fire', 167) / fps, 'boom', 5.0),
    (at(fire, 'fire', 167) / fps + 0.35, 'fanfare', 2.6),
]

if LIMIT:
    total = min(total, LIMIT)
print('total frames', total, 'seconds %.2f' % (total / fps), S)
sq, vt, wav = f'{OUTDIR}/square-silent.mp4', f'{OUTDIR}/vertical-silent.mp4', f'{OUTDIR}/sound.wav'
audio.build(total / fps, events, wav)
C.render(timeline, cards, total, sq, vt, xfade=X)
for v, name in [(sq, 'silver-cup-ad-square.mp4'), (vt, 'silver-cup-ad-vertical.mp4')]:
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', v, '-i', wav, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', f'{OUTDIR}/{name}'])
print('done')
