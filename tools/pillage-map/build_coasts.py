#!/usr/bin/env python3
"""Build pillage/coasts.js: the five seas of Pillage the Reefer, drawn from real coastlines.

Owner's request, November 26, 2026: the maps should match reality, or a faithful picture of it, with nothing made
up. Every coastline here comes from Natural Earth (public domain), 1:10m land and minor islands. Each sea is a
Mercator window onto the real Caribbean, and all five share one scale, so a day's sail covers the same ground
everywhere. The windows meet edge to edge, so a ship that sails off one chart comes in on the next at the same
spot. Ports, dig sites and the hideout sit at their real latitude and longitude. Islands too small to see at this
scale are drawn at a small minimum size, at their real position. The chart has to leave a ship room to pass, so
channels narrower than about two miles close up, as they do on any small-scale chart.

Usage:
  curl -sSfO https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_land.geojson
  curl -sSfO https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_minor_islands.geojson
  python3 -m pip install shapely pillow
  python3 tools/pillage-map/build_coasts.py DIR_WITH_THE_TWO_FILES [--preview OUTDIR]
"""
import json
import math
import os
import sys

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon, box, shape
from shapely.ops import nearest_points, polylabel, unary_union

K = 140.0        # map units per degree of longitude, on every sea (about 0.75 km a unit at these latitudes)
EDGE = 60        # land is kept this far past each edge, so coasts run off the chart
CLOSE = 1.5      # islands and shores closer than twice this are joined (about 2 km)
TOL = 0.55       # outlines are simplified to within this many units
SMALL = 20       # islands smaller than this across are drawn as small round islands (blobs)
MIN_RX, MIN_RY = 5.0, 3.5   # the smallest blob, so a real cay a few hundred yards long can still be seen
DROP = 1.0       # unnamed islands under this many units across are left off
CELL, MARGIN, SHIP_R = 20, 13, 7   # the game engine's route grid (pillage/engine.js)
RECT = 36        # depth of a sea's exit strip
IN = 30          # a ship arriving from another sea starts this far inside the exit strip
EDGE_CLEAR = 22  # an exit only spans water at least this far from land, at the edge and where ships arrive

# ---------------------------------------------------------------- the seas
SEAS = {
    'windward': dict(west=-80.2, east=-66.4, south=16.6, north=21.75),
    'straits': dict(west=-83.8, east=-74.3, south=21.75, north=30.3),
    'gulf': dict(west=-98.2, east=-83.8, south=17.8, north=30.6),
    'main': dict(west=-82.3, east=-66.4, south=8.4, north=16.6),
    'antilles': dict(west=-66.4, east=-58.9, south=9.9, north=18.9),
}
# Seas that meet: (sea, its edge, the other sea, its edge). The shared stretch is where both windows touch.
LINKS = [
    ('windward', 'top', 'straits', 'bottom'),
    ('windward', 'bottom', 'main', 'top'),
    ('windward', 'right', 'antilles', 'left'),
    ('straits', 'left', 'gulf', 'right'),
    ('main', 'right', 'antilles', 'left'),
]
LABEL_TO = {'windward': 'To the Windward Passage', 'straits': 'To the Florida Straits', 'gulf': 'To the Gulf of Mexico',
            'main': 'To the Spanish Main', 'antilles': 'To the Lesser Antilles'}


def merc(lat):
    return math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))


def unmerc(y):
    return math.degrees(2 * math.atan(math.exp(math.radians(y))) - math.pi / 2)


def frame(mid):
    s = SEAS[mid]
    w = round(K * (s['east'] - s['west']))
    h = round(K * (merc(s['north']) - merc(s['south'])))
    return w, h


def to_xy(mid, lon, lat):
    s = SEAS[mid]
    return ((lon - s['west']) * K, (merc(s['north']) - merc(lat)) * K)


def to_ll(mid, x, y):
    s = SEAS[mid]
    return (s['west'] + x / K, unmerc(merc(s['north']) - y / K))


# ---------------------------------------------------------------- names (latitude, longitude)
# One point inside each island or coast worth naming. True marks a name drawn on the chart.
NAMES = [
    # mainland coasts first: the first name found inside a piece names it
    ('Tierra Firme', 9.6, -74.8, True), ('Tierra Firme', 10.0, -64.5, False), ('Tierra Firme', 9.0, -79.5, False), ('New Spain', 19.9, -97.7, True),
    ('Florida', 28.4, -81.6, True), ('Florida', 26.2, -81.0, False),
    ('Cuba', 20.3, -76.2, True), ('Cuba', 22.4, -79.9, True), ('Cuba', 21.4, -78.0, False), ('Cuba', 22.45, -84.0, False),
    ('Cuba', 22.6, -83.3, False), ('Cuba', 20.1, -74.6, False), ('Cuba', 21.0, -77.2, False),
    ('Hispaniola', 19.2, -71.3, True), ('Hispaniola', 18.6, -70.2, False), ('Hispaniola', 18.3, -73.5, False),
    ('Jamaica', 18.15, -77.3, True), ('Puerto Rico', 18.22, -66.2, True), ('Puerto Rico', 18.2, -66.9, True),
    ('Gonâve', 18.85, -73.05, False), ('Tortuga', 20.05, -72.8, False), ('Île-à-Vache', 18.07, -73.64, False),
    ('Navassa', 18.40, -75.012, False), ('Great Inagua', 21.05, -73.4, True), ('Little Inagua', 21.48, -73.0, False),
    ('Caicos Islands', 21.8, -71.8, False), ('Turks Islands', 21.45, -71.14, False), ('Cayman Brac', 19.71, -79.8, False),
    ('Little Cayman', 19.69, -80.05, False), ('Beata', 17.58, -71.52, False), ('Alto Velo', 17.48, -71.65, False),
    ('Saona', 18.15, -68.7, False), ('Catalina', 18.36, -68.98, False), ('Mona', 18.08, -67.9, False), ('Desecheo', 18.38, -67.48, False),
    ('Pedro Cays', 17.0, -77.8, False), ('Morant Cays', 17.41, -75.98, False), ('Hogsty Reef', 21.68, -73.85, False),
    ('The Cayemites', 18.6, -73.75, False),
    ('Isle of Pines', 21.75, -82.85, False), ('Andros', 24.4, -78.0, True), ('Andros', 24.8, -78.0, False), ('Andros', 24.0, -77.7, False),
    ('New Providence', 25.03, -77.4, False), ('Eleuthera', 25.2, -76.2, False), ('Eleuthera', 24.9, -76.2, False), ('Eleuthera', 25.45, -76.6, False),
    ('Grand Bahama', 26.65, -78.4, True), ('Abaco', 26.4, -77.1, True), ('Abaco', 26.8, -77.4, False), ('Bimini', 25.73, -79.28, False),
    ('Cat Island', 24.4, -75.5, False), ('Long Island', 23.2, -75.1, False), ('San Salvador', 24.05, -74.48, False),
    ('Rum Cay', 23.68, -74.85, False), ('Conception Island', 23.84, -75.12, False), ('Dry Tortugas', 24.628, -82.873, False),
    ('Marquesas Keys', 24.57, -82.13, False), ('Key West', 24.555, -81.78, False), ('Cay Sal', 23.69, -80.4, False),
    ('Alacranes Reef', 22.384, -89.684, False), ('Cayo Arcas', 20.2, -91.97, False), ('Cayo Arenas', 22.12, -91.4, False),
    ('Triángulos', 20.95, -92.23, False), ('Isla de Sacrificios', 19.175, -96.092, False), ('Isla Lobos', 21.45, -97.23, False),
    ('Isla Mujeres', 21.23, -86.73, False), ('Cozumel', 20.42, -86.92, False), ('Contoy', 21.5, -86.8, False),
    ('Isla del Carmen', 18.65, -91.7, False), ('Dauphin Island', 30.25, -88.15, False),
    ('Curaçao', 12.2, -69.0, False), ('Aruba', 12.52, -69.97, False), ('Bonaire', 12.18, -68.27, False),
    ('Providencia', 13.35, -81.375, False), ('San Andrés', 12.55, -81.72, False), ('Serrana Bank', 14.29, -80.37, False),
    ('Serranilla Bank', 15.83, -79.85, False), ('Roncador', 13.57, -80.08, False), ('Quita Sueño', 14.3, -81.12, False),
    ('Tierra Bomba', 10.36, -75.57, False), ('Isla Fuerte', 9.39, -76.18, False), ('Escudo de Veraguas', 9.1, -81.55, False),
    ('Los Monjes', 12.37, -70.9, False), ('La Orchila', 11.8, -66.18, False),
    ('Vieques', 18.12, -65.45, False), ('Culebra', 18.31, -65.29, False), ('St. Thomas', 18.34, -64.93, False),
    ('St. John', 18.33, -64.74, False), ('Tortola', 18.43, -64.62, False), ('Virgin Gorda', 18.48, -64.4, False),
    ('Anegada', 18.73, -64.33, False), ('St. Croix', 17.73, -64.75, False), ('Anguilla', 18.22, -63.05, False),
    ('Saint Martin', 18.07, -63.06, False), ('Saint Barthélemy', 17.9, -62.83, False), ('Saba', 17.63, -63.24, False),
    ('St. Eustatius', 17.49, -62.97, False), ('St. Kitts', 17.3, -62.75, False), ('Nevis', 17.15, -62.58, False),
    ('Barbuda', 17.63, -61.8, False), ('Antigua', 17.08, -61.8, True), ('Redonda', 16.94, -62.35, False),
    ('Montserrat', 16.74, -62.19, False), ('Guadeloupe', 16.2, -61.65, True), ('Guadeloupe', 16.3, -61.45, False),
    ('Les Saintes', 15.87, -61.6, False), ('Marie-Galante', 15.93, -61.27, False), ('La Désirade', 16.32, -61.07, False),
    ('Dominica', 15.42, -61.35, True), ('Martinique', 14.65, -61.0, True), ('St. Lucia', 13.9, -60.97, True),
    ('St. Vincent', 13.25, -61.2, True), ('Bequia', 13.0, -61.23, False), ('Mustique', 12.88, -61.18, False),
    ('Canouan', 12.71, -61.33, False), ('Mayreau', 12.64, -61.39, False), ('Tobago Cays', 12.632, -61.355, False),
    ('Union Island', 12.6, -61.43, False), ('Carriacou', 12.48, -61.45, False), ('Grenada', 12.12, -61.68, True),
    ('Barbados', 13.17, -59.55, True), ('Tobago', 11.25, -60.68, True), ('Trinidad', 10.45, -61.25, True),
    ('Margarita', 11.0, -63.9, True), ('Coche', 10.78, -63.95, False), ('Cubagua', 10.82, -64.18, False),
    ('La Tortuga', 10.95, -65.3, False), ('La Blanquilla', 11.85, -64.6, False), ('Los Testigos', 11.38, -63.1, False),
    ('Isla de Aves', 15.67, -63.62, False),
]
# Extra names drawn on a long coast that already has one.
REGION_LABELS = [('Yucatán', 20.4, -89.0), ('Louisiana', 30.3, -91.8), ('Florida', 30.42, -84.6), ('Venezuela', 9.8, -68.5),
                 ('Panama', 8.75, -80.0)]
# Chains of little cays share a name.
GROUPS = [
    ('Padre Island', 25.9, -97.7, 27.62, -96.9),
    ('Jardines de la Reina', 20.4, -79.4, 21.1, -77.6), ('Jardines del Rey', 22.0, -81.0, 23.3, -77.3),
    ('The Keys', 24.4, -82.0, 25.4, -80.1), ('Dry Tortugas', 24.55, -83.0, 24.75, -82.75), ('The Exumas', 23.4, -76.7, 24.8, -75.7),
    ('Berry Islands', 25.3, -78.1, 25.95, -77.6), ('Bimini', 25.5, -79.4, 25.8, -79.2), ('Cay Sal Bank', 23.4, -80.6, 24.1, -79.5),
    ('Ragged Islands', 21.9, -76.0, 23.0, -75.5), ('Abaco', 25.8, -78.2, 27.4, -76.8), ('Los Colorados', 22.4, -84.4, 23.0, -83.3),
    ('Pedro Cays', 16.8, -78.0, 17.2, -77.6), ('Morant Cays', 17.3, -76.1, 17.5, -75.9), ('Turks Islands', 21.1, -71.3, 21.6, -71.0),
    ('Caicos Islands', 21.3, -72.6, 22.0, -71.4), ('The Cayemites', 18.5, -73.9, 18.7, -73.6),
    ('Rosario Islands', 10.1, -75.85, 10.25, -75.65), ('San Bernardo Islands', 9.65, -75.95, 9.85, -75.75),
    ('San Blas Islands', 9.2, -79.1, 9.6, -77.8), ('Los Roques', 11.7, -66.95, 12.0, -66.5), ('Las Aves', 11.9, -67.8, 12.1, -67.3),
    ('Serrana Bank', 14.2, -80.5, 14.5, -80.2), ('Roncador', 13.4, -80.2, 13.7, -79.9), ('Serranilla Bank', 15.7, -80.0, 16.0, -79.7),
    ('Quita Sueño', 14.0, -81.3, 14.6, -81.0), ('Bocas del Toro', 9.0, -82.4, 9.6, -81.9), ('Alburquerque Cays', 12.1, -81.95, 12.25, -81.75),
    ('The Grenadines', 12.3, -61.7, 13.1, -61.1), ('The Virgin Islands', 17.6, -65.1, 18.8, -64.2), ('Les Saintes', 15.8, -61.7, 15.92, -61.55),
    ('Los Frailes', 11.1, -63.8, 11.25, -63.65), ('Los Hermanos', 11.7, -64.5, 11.85, -64.35), ('Alacranes Reef', 22.3, -89.8, 22.6, -89.55),
    ('The Chandeleur Islands', 29.3, -89.1, 30.1, -88.7),
]
# Small islands to draw even when the coastline data leaves them out: the dig sites and well-known banks.
ENSURE = ['Alacranes Reef', 'Cayo Arcas', 'Cayo Arenas', 'Triángulos', 'Serrana Bank', 'Roncador', 'Serranilla Bank', 'Quita Sueño',
          'Tobago Cays', 'Dry Tortugas', 'Navassa', 'Morant Cays', 'Pedro Cays', 'Isla de Aves', 'Isla de Sacrificios', 'Isla Lobos',
          'Hogsty Reef', 'Cay Sal', 'Los Monjes', 'Redonda', 'Desecheo']

# Ports: the town, and a point out in the harbor roads to anchor near.
PORTS = {
    'tortuga': dict(map='windward', town=(20.035, -72.80), sea=(20.02, -73.06)),
    'portroyal': dict(map='windward', town=(17.937, -76.841), sea=(17.895, -76.84)),
    'petitgoave': dict(map='windward', town=(18.432, -72.866), sea=(18.47, -72.87)),
    'havana': dict(map='straits', town=(23.137, -82.355), sea=(23.175, -82.36)),
    'nassau': dict(map='straits', town=(25.075, -77.343), sea=(25.105, -77.35)),
    'staugustine': dict(map='straits', town=(29.894, -81.313), sea=(29.88, -81.22)),
    'veracruz': dict(map='gulf', town=(19.197, -96.137), sea=(19.21, -96.09)),
    'cartagena': dict(map='main', town=(10.423, -75.550), sea=(10.43, -75.59)),
    'portobelo': dict(map='main', town=(9.553, -79.655), sea=(9.59, -79.68)),
    'willemstad': dict(map='main', town=(12.107, -68.934), sea=(12.085, -68.94)),
    'barbados': dict(map='antilles', town=(13.097, -59.616), sea=(13.085, -59.64)),
}
STASHES = {
    's1': dict(map='windward', name='Navassa', at=(18.40, -75.012)),
    's2': dict(map='straits', name='Dry Tortugas', at=(24.628, -82.873)),
    's3': dict(map='main', name='Providencia', at=(13.35, -81.375)),
    'alacranes': dict(map='gulf', name='Alacranes Reef', at=(22.384, -89.684)),
    'tobagocays': dict(map='antilles', name='Tobago Cays', at=(12.632, -61.355)),
    'emerald': dict(map='main', name='Serrana Bank', at=(14.29, -80.37)),
}
HIDEOUT = dict(map='windward', name='Île-à-Vache', at=(18.07, -73.64), sea=(18.12, -73.66))

# Sea lanes the patrols and merchantmen keep to, in latitude and longitude. Each point moves to the nearest open water.
PATROLS = {
    'windward': [
        ('customs', [(17.7, -76.6), (18.2, -75.0), (19.6, -74.2), (20.25, -72.8), (19.6, -74.2), (18.6, -73.2), (17.9, -74.2)]),
        ('merchant', [(18.9, -79.5), (17.5, -78.0), (17.4, -75.5), (17.6, -72.0), (17.4, -68.5), (17.0, -70.0), (17.2, -76.0)]),
    ],
    'straits': [
        ('customs', [(23.4, -82.4), (24.2, -82.0), (24.0, -80.8), (23.4, -81.2)]),
        ('customs', [(25.3, -77.6), (25.7, -77.0), (24.6, -76.3), (25.3, -77.6), (24.3, -77.3)]),
        ('merchant', [(23.3, -83.6), (23.4, -82.0), (24.2, -80.2), (25.6, -79.6), (27.0, -79.6), (29.5, -80.9), (27.0, -79.6), (24.0, -80.4)]),
    ],
    'gulf': [
        ('customs', [(19.4, -95.8), (21.0, -96.6), (22.5, -93.0), (22.0, -90.5), (20.0, -93.5)]),
        ('merchant', [(19.4, -95.8), (22.0, -94.0), (23.0, -90.0), (23.5, -86.0), (23.6, -84.2), (26.0, -86.0), (28.8, -88.3), (26.0, -92.0)]),
    ],
    'main': [
        ('customs', [(10.6, -75.75), (11.5, -74.5), (12.8, -72.5), (12.4, -69.5), (11.6, -73.5)]),
        ('merchant', [(9.8, -79.8), (10.6, -77.5), (10.6, -75.8), (12.0, -75.0), (12.5, -70.5), (12.0, -68.5), (13.5, -72.0), (12.8, -79.0)]),
    ],
    'antilles': [
        ('customs', [(13.0, -59.7), (14.5, -60.6), (16.0, -60.9), (15.0, -62.0), (13.4, -61.6), (12.2, -60.6)]),
        ('merchant', [(17.5, -66.0), (17.0, -63.5), (16.5, -62.0), (15.0, -61.2), (13.0, -60.5), (11.0, -61.0), (12.5, -62.5), (15.5, -63.0)]),
    ],
}


# ---------------------------------------------------------------- the engine's island shapes, copied exactly
def imul(a, b):
    return (a * b) & 0xffffffff


def rng(seed):
    a = seed & 0xffffffff

    def r():
        nonlocal a
        a = (a + 0x6D2B79F5) & 0xffffffff
        t = a
        t = imul(t ^ (t >> 15), t | 1)
        t = (t ^ ((t + imul(t ^ (t >> 7), t | 61)) & 0xffffffff)) & 0xffffffff
        return ((t ^ (t >> 14)) & 0xffffffff) / 4294967296
    return r


def blob_pts(spec):
    cx, cy, rx, ry, rot, seed = spec
    r = rng(seed * 7919 + 13)
    p1, p2, p3 = r() * 6.283, r() * 6.283, r() * 6.283
    n = int(min(48, max(16, math.floor((rx + ry) / 3 + 0.5))))
    c, s, pts = math.cos(rot), math.sin(rot), []
    for i in range(n):
        t = i / n * math.pi * 2
        k = 1 + 0.11 * math.sin(2 * t + p1) + 0.07 * math.sin(3 * t + p2) + 0.04 * math.sin(5 * t + p3)
        x, y = math.cos(t) * rx * k, math.sin(t) * ry * k
        pts.append((cx + x * c - y * s, cy + x * s + y * c))
    return pts


# ---------------------------------------------------------------- building one sea
def load(src):
    region = box(-100, 6, -56, 33)
    parts = []
    for f in ('ne_10m_land.geojson', 'ne_10m_minor_islands.geojson'):
        with open(os.path.join(src, f)) as fh:
            for feat in json.load(fh)['features']:
                g = shape(feat['geometry'])
                if g.intersects(region):
                    parts.append(g.intersection(region))
    return unary_union(parts)


def polys_of(g):
    if g.is_empty:
        return []
    if g.geom_type == 'Polygon':
        return [g]
    out = []
    for p in getattr(g, 'geoms', []):
        out.extend(polys_of(p))
    return out


def ring(poly):
    return [[int(round(x)), int(round(y))] for x, y in list(poly.exterior.coords)[:-1]]


def build_sea(mid, world):
    s = SEAS[mid]
    w, h = frame(mid)
    md = EDGE / K
    win = box(s['west'] - md, s['south'] - md, s['east'] + md, s['north'] + md)
    geo = world.intersection(win)
    top = merc(s['north'])
    proj = shapely.transform(geo, lambda c: np.column_stack(((c[:, 0] - s['west']) * K,
                                                             (top - np.degrees(np.log(np.tan(np.pi / 4 + np.radians(c[:, 1]) / 2)))) * K)))
    proj = proj.buffer(CLOSE, quad_segs=4).buffer(-CLOSE, quad_segs=4)
    xy = lambda lat, lon: to_xy(mid, lon, lat)
    names = [(n, Point(xy(la, lo)), lab) for n, la, lo, lab in NAMES]
    lands, pieces = [], []
    for p in polys_of(proj):
        p = Polygon(p.exterior)
        if not p.is_valid:
            p = p.buffer(0)
        minx, miny, maxx, maxy = p.bounds
        size = max(maxx - minx, maxy - miny)
        name, label = None, None
        for n, pt, lab in names:
            if p.buffer(3).contains(pt):
                name = n
                if lab and -40 < pt.x < w + 40:
                    label = pt
                break
        if name is None:
            c = p.centroid
            lon, lat = to_ll(mid, c.x, c.y)
            for n, so, we, no, ea in GROUPS:
                if so <= lat <= no and we <= lon <= ea:
                    name = n
                    break
        if name is None and size < DROP:
            continue
        if maxx < -EDGE or minx > w + EDGE or maxy < -EDGE or miny > h + EDGE:
            continue
        pieces.append(dict(poly=p, size=size, name=name, label=label))
    # unnamed cays take the name of the nearest named land
    named = [q for q in pieces if q['name'] and q['size'] >= SMALL]
    for q in pieces:
        if q['name']:
            continue
        best, bd = None, 90
        for r in named:
            d = q['poly'].distance(r['poly'])
            if d < bd:
                best, bd = r, d
        q['name'] = 'a cay off ' + best['name'] if best else 'a lonely cay'
    # real islands the data leaves out, at their real spot
    for n, la, lo, lab in NAMES:
        if n not in ENSURE:
            continue
        x, y = to_xy(mid, lo, la)
        if not (0 <= x <= w and 0 <= y <= h):
            continue
        pt = Point(x, y)
        if any(q['poly'].distance(pt) < 4 for q in pieces):
            continue
        pieces.append(dict(poly=pt.buffer(MIN_RX), size=2 * MIN_RX, name=n, label=None, added=True))
    seed = 0
    for q in sorted(pieces, key=lambda q: (-q['size'], q['poly'].centroid.x)):
        p, seed = q['poly'], seed + 1
        L = {'name': q['name']}
        if q['size'] < SMALL:
            c = p.centroid
            mrr = p.minimum_rotated_rectangle
            cs = list(mrr.exterior.coords) if mrr.geom_type == 'Polygon' else [(c.x - 1, c.y), (c.x + 1, c.y), (c.x + 1, c.y), (c.x - 1, c.y)]
            e1 = (cs[1][0] - cs[0][0], cs[1][1] - cs[0][1])
            e2 = (cs[2][0] - cs[1][0], cs[2][1] - cs[1][1])
            a, b = math.hypot(*e1), math.hypot(*e2)
            if b > a:
                e1, a, b = e2, b, a
            rot = math.atan2(e1[1], e1[0]) if a > 0 else 0.0
            if rot > math.pi / 2:
                rot -= math.pi
            if rot < -math.pi / 2:
                rot += math.pi
            rx, ry = max(a / 2, MIN_RX), max(b / 2, MIN_RY)
            L['blob'] = [int(round(c.x)), int(round(c.y)), round(rx, 1), round(ry, 1), round(rot, 2), seed]
            q['game'] = Polygon(blob_pts(L['blob']))
        else:
            sp = p.simplify(TOL, preserve_topology=True)
            sp = Polygon(sp.exterior) if sp.geom_type == 'Polygon' else p
            pts = ring(sp)
            gp = Polygon(pts)
            if not gp.is_valid:
                gp = gp.buffer(0)
                gp = max(polys_of(gp), key=lambda g: g.area)
                pts = ring(gp)
                gp = Polygon(pts)
            L['coast'] = pts
            q['game'] = gp
            if q['size'] > 60:
                inner = [ring(r) for r in polys_of(gp.buffer(-12).simplify(2.0)) if r.area > 400]
                if inner:
                    L['inner'] = inner
            if q['label'] is not None:
                L['label'] = [int(round(q['label'].x)), int(round(q['label'].y))]
        if q['name'] and not q['name'].startswith('a '):
            # a named island of some size gets its name on the chart
            if 'label' not in L and q['size'] >= 40 and q['name'] not in [l['name'] for l in lands if 'label' in l]:
                vis = p.intersection(box(40, 30, w - 40, h - 30))
                if not vis.is_empty and vis.area > 600:
                    lp = polylabel(max(polys_of(vis), key=lambda g: g.area), tolerance=2)
                    L['label'] = [int(round(lp.x)), int(round(lp.y))]
        lands.append(L)
        q['land'] = L
    game_land = unary_union([q['game'] for q in pieces])
    return dict(w=w, h=h, lands=lands, pieces=pieces, land=game_land)


# ---------------------------------------------------------------- the route grid, as the engine builds it
def nav_grid(sea):
    w, h, land = sea['w'], sea['h'], sea['land']
    cols, rows = math.ceil(w / CELL), math.ceil(h / CELL)
    xs = (np.arange(cols) + 0.5) * CELL
    ys = (np.arange(rows) + 0.5) * CELL
    gx, gy = np.meshgrid(xs, ys)
    pts = shapely.points(gx.ravel(), gy.ravel())
    shapely.prepare(land)
    d = shapely.distance(land, pts)
    blocked = (d < MARGIN).reshape(rows, cols)
    sea['nav'] = dict(cols=cols, rows=rows, blocked=blocked, dist=d.reshape(rows, cols))
    # the open water a ship can reach from the middle of the biggest stretch of sea
    seen = np.zeros_like(blocked)
    best = None
    for r0 in range(rows):
        for c0 in range(cols):
            if blocked[r0, c0] or seen[r0, c0]:
                continue
            comp, q = [], [(r0, c0)]
            seen[r0, c0] = True
            while q:
                r, c = q.pop()
                comp.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < rows and 0 <= cc < cols and not blocked[rr, cc] and not seen[rr, cc]:
                        if dr and dc and (blocked[r, cc] or blocked[rr, c]):
                            continue
                        seen[rr, cc] = True
                        q.append((rr, cc))
            if best is None or len(comp) > len(best):
                best = comp
    sea['open'] = set(best)


def land_dist(sea, x, y):
    return sea['land'].distance(Point(x, y))


def free_cell_near(sea, x, y, clear=MARGIN + 3, reach=400):
    """The centre of a reachable route cell nearest (x, y), with room for a ship."""
    nav, best, bd = sea['nav'], None, reach
    for (r, c) in sea['open']:
        cx, cy = (c + 0.5) * CELL, (r + 0.5) * CELL
        d = math.hypot(cx - x, cy - y)
        if d < bd and nav['dist'][r, c] >= clear:
            best, bd = (cx, cy), d
    return best


def snap_inside(sea, x, y, depth=4):
    land, pt = sea['land'], Point(x, y)
    if land.buffer(-depth).contains(pt):
        return x, y
    inner = land.buffer(-depth)
    target = inner if not inner.is_empty else land
    near = nearest_points(target, pt)[0]
    return near.x, near.y


# ---------------------------------------------------------------- exits between seas
def edge_line(mid, edge, lo, hi):
    """Points along an edge of a sea, between two longitudes (top, bottom) or latitudes (left, right)."""
    s = SEAS[mid]
    out = []
    n = max(2, int((hi - lo) * K / 2))
    for i in range(n + 1):
        v = lo + (hi - lo) * i / n
        if edge in ('top', 'bottom'):
            lat = s['north'] if edge == 'top' else s['south']
            out.append((v, lat))
        else:
            lon = s['west'] if edge == 'left' else s['east']
            out.append((lon, v))
    return out


def inward(edge, x, y, d, w, h):
    return {'top': (x, d), 'bottom': (x, h - d), 'left': (d, y), 'right': (w - d, y)}[edge]


def make_exits(seas):
    exits = {mid: [] for mid in SEAS}
    for a, ea, b, eb in LINKS:
        A, B = SEAS[a], SEAS[b]
        if ea in ('top', 'bottom'):
            lo, hi = max(A['west'], B['west']), min(A['east'], B['east'])
        else:
            lo, hi = max(A['south'], B['south']), min(A['north'], B['north'])
        run, best = [], []
        for lon, lat in edge_line(a, ea, lo, hi):
            ok = True
            for mid, edge in ((a, ea), (b, eb)):
                sea = seas[mid]
                x, y = to_xy(mid, lon, lat)
                for d in (0, RECT / 2, RECT + IN, RECT + IN + CELL):
                    px, py = inward(edge, x, y, d, sea['w'], sea['h'])
                    if land_dist(sea, px, py) < EDGE_CLEAR:
                        ok = False
            if ok:
                run.append((lon, lat))
            else:
                if len(run) > len(best):
                    best = run
                run = []
        if len(run) > len(best):
            best = run
        if len(best) < 2:
            raise SystemExit('no open water between ' + a + ' and ' + b)
        for mid, edge, other in ((a, ea, b), (b, eb, a)):
            sea = seas[mid]
            p0, p1 = to_xy(mid, *best[0]), to_xy(mid, *best[-1])
            w, h = sea['w'], sea['h']
            if edge in ('top', 'bottom'):
                x0, x1 = sorted((p0[0], p1[0]))
                x0, x1 = max(x0 + 6, 0), min(x1 - 6, w)
                y = 0 if edge == 'top' else h - RECT
                rect = [round(x0), y, round(x1 - x0), RECT]
                at = [round((x0 + x1) / 2), 12 if edge == 'top' else h - 12]
            else:
                y0, y1 = sorted((p0[1], p1[1]))
                y0, y1 = max(y0 + 6, 0), min(y1 - 6, h)
                x = 0 if edge == 'left' else w - RECT
                rect = [x, round(y0), RECT, round(y1 - y0)]
                at = [10 if edge == 'left' else w - 10, round((y0 + y1) / 2)]
            exits[mid].append({'to': other, 'rect': rect, 'label': LABEL_TO[other], 'at': at})
    return exits


# ---------------------------------------------------------------- putting it together
def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    preview = None
    if '--preview' in args:
        i = args.index('--preview')
        preview = args[i + 1]
        del args[i:i + 2]
    world = load(args[0])
    seas = {}
    for mid in SEAS:
        seas[mid] = build_sea(mid, world)
        nav_grid(seas[mid])
        print(mid, seas[mid]['w'], 'x', seas[mid]['h'], len(seas[mid]['lands']), 'lands', file=sys.stderr)
    exits = make_exits(seas)
    out = {'k': K, 'seas': {}, 'ports': {}, 'stashes': {}, 'hideout': None}
    for mid, sea in seas.items():
        s = SEAS[mid]
        pat = []
        for kind, route in PATROLS[mid]:
            pts = []
            for lat, lon in route:
                x, y = to_xy(mid, lon, lat)
                f = free_cell_near(sea, x, y, clear=30, reach=300)
                if not f:
                    raise SystemExit('patrol point in no open water: ' + mid + ' ' + str((lat, lon)))
                pts.append([round(f[0]), round(f[1])])
            pat.append({'kind': kind, 'route': pts})
        labels = []
        for n, la, lo in REGION_LABELS:
            x, y = to_xy(mid, lo, la)
            if 40 < x < sea['w'] - 40 and 20 < y < sea['h'] - 20 and sea['land'].contains(Point(x, y)):
                labels.append({'name': n, 'at': [round(x), round(y)]})
        out['seas'][mid] = {'w': sea['w'], 'h': sea['h'], 'geo': {'west': s['west'], 'east': s['east'], 'south': s['south'], 'north': s['north']},
                            'lands': sea['lands'], 'labels': labels, 'exits': exits[mid], 'patrols': pat}
    for pid, p in PORTS.items():
        sea, mid = seas[p['map']], p['map']
        tx, ty = to_xy(mid, p['town'][1], p['town'][0])
        tx, ty = snap_inside(sea, tx, ty)
        hx, hy = to_xy(mid, p['sea'][1], p['sea'][0])
        dock = free_cell_near(sea, hx, hy)
        if not dock:
            raise SystemExit('no anchorage for ' + pid)
        out['ports'][pid] = {'dock': [round(dock[0]), round(dock[1])], 'town': [round(tx), round(ty)], 'll': list(p['town'])}
        for L in out['seas'][mid]['lands']:
            if 'label' in L and math.hypot(L['label'][0] - tx, L['label'][1] - ty) < 45:
                del L['label']
        print(pid, 'town moved', round(math.hypot(tx - to_xy(mid, p['town'][1], p['town'][0])[0], ty - to_xy(mid, p['town'][1], p['town'][0])[1]), 1),
              'dock from town', round(math.hypot(dock[0] - tx, dock[1] - ty)), file=sys.stderr)
    for sid, st in STASHES.items():
        sea, mid = seas[st['map']], st['map']
        x, y = to_xy(mid, st['at'][1], st['at'][0])
        q = min(sea['pieces'], key=lambda q: q['game'].distance(Point(x, y)))
        c = q['game'].centroid if q['size'] < SMALL else Point(*snap_inside(sea, x, y))
        if sid == 'emerald':
            q['land']['haze'] = True
            q['land']['label'] = [round(c.x), round(c.y)]
        out['stashes'][sid] = {'at': [round(c.x), round(c.y)], 'll': list(st['at']), 'island': q['name']}
        print(sid, 'on', q['name'], 'moved', round(math.hypot(c.x - x, c.y - y), 1), file=sys.stderr)
    H, sea = HIDEOUT, seas[HIDEOUT['map']]
    x, y = to_xy(H['map'], H['at'][1], H['at'][0])
    q = min(sea['pieces'], key=lambda q: q['game'].distance(Point(x, y)))
    c = q['game'].centroid
    hx, hy = to_xy(H['map'], H['sea'][1], H['sea'][0])
    dock = free_cell_near(sea, hx, hy)
    out['hideout'] = {'at': [round(c.x), round(c.y)], 'dock': [round(dock[0]), round(dock[1])], 'll': list(H['at'])}
    for mid, S in out['seas'].items():
        print(mid, 'blobs', sum(1 for L in S['lands'] if 'blob' in L), 'coasts', sum(1 for L in S['lands'] if 'coast' in L), file=sys.stderr)
        print('   ', sorted(set(L['name'] for L in S['lands'])), file=sys.stderr)
        print('    labels', [L['name'] for L in S['lands'] if 'label' in L] + [l['name'] for l in S['labels']], file=sys.stderr)
    body = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
    js = ('/* Pillage the Reefer: the real coastlines of the five seas. Generated by tools/pillage-map/build_coasts.py from\n'
          '   Natural Earth 1:10m land and minor islands (public domain, naturalearthdata.com). Do not edit by hand. */\n'
          'window.PILLAGE_COASTS = ' + body + ';\n')
    dest = os.path.join(os.path.dirname(__file__), '..', '..', 'pillage', 'coasts.js')
    with open(dest, 'w') as fh:
        fh.write(js)
    print('wrote', os.path.relpath(dest), len(js) // 1024, 'KB', file=sys.stderr)
    if preview:
        draw_previews(out, seas, preview)


def draw_previews(out, seas, outdir):
    from PIL import Image, ImageDraw
    os.makedirs(outdir, exist_ok=True)
    for mid, S in out['seas'].items():
        sc = 0.75
        im = Image.new('RGB', (int(S['w'] * sc), int(S['h'] * sc)), (42, 169, 189))
        d = ImageDraw.Draw(im)
        nav = seas[mid]['nav']
        for r in range(nav['rows']):
            for c in range(nav['cols']):
                if nav['blocked'][r, c]:
                    d.rectangle([c * CELL * sc, r * CELL * sc, (c + 1) * CELL * sc, (r + 1) * CELL * sc], fill=(36, 150, 170))
        for L in S['lands']:
            pts = L['coast'] if 'coast' in L else blob_pts(L['blob'])
            d.polygon([(x * sc, y * sc) for x, y in pts], fill=(220, 200, 120) if L.get('haze') else (100, 165, 83), outline=(236, 216, 160))
            for rg in L.get('inner', []):
                d.polygon([(x * sc, y * sc) for x, y in rg], fill=(79, 140, 67))
        for L in S['lands']:
            if 'label' in L:
                d.text((L['label'][0] * sc, L['label'][1] * sc), L['name'], fill=(10, 40, 10), anchor='mm')
        for lb in S['labels']:
            d.text((lb['at'][0] * sc, lb['at'][1] * sc), lb['name'], fill=(60, 20, 10), anchor='mm')
        for e in S['exits']:
            x, y, w, h = e['rect']
            d.rectangle([x * sc, y * sc, (x + w) * sc, (y + h) * sc], outline=(255, 255, 255), width=2)
            d.text((e['at'][0] * sc, e['at'][1] * sc), e['to'], fill=(255, 255, 255), anchor='mm')
        for p in S['patrols']:
            col = (200, 30, 30) if p['kind'] == 'customs' else (250, 250, 250)
            d.line([(x * sc, y * sc) for x, y in p['route']], fill=col, width=1)
        for pid, P in out['ports'].items():
            if PORTS[pid]['map'] != mid:
                continue
            d.ellipse([P['town'][0] * sc - 4, P['town'][1] * sc - 4, P['town'][0] * sc + 4, P['town'][1] * sc + 4], fill=(150, 20, 20))
            d.ellipse([P['dock'][0] * sc - 3, P['dock'][1] * sc - 3, P['dock'][0] * sc + 3, P['dock'][1] * sc + 3], fill=(255, 255, 0))
            d.text((P['town'][0] * sc, P['town'][1] * sc - 12), pid, fill=(120, 0, 0), anchor='mm')
        for sid, T in out['stashes'].items():
            if STASHES[sid]['map'] != mid:
                continue
            x, y = T['at']
            d.line([(x * sc - 6, y * sc - 6), (x * sc + 6, y * sc + 6)], fill=(180, 0, 0), width=2)
            d.line([(x * sc + 6, y * sc - 6), (x * sc - 6, y * sc + 6)], fill=(180, 0, 0), width=2)
        if HIDEOUT['map'] == mid:
            x, y = out['hideout']['dock']
            d.rectangle([x * sc - 3, y * sc - 3, x * sc + 3, y * sc + 3], fill=(255, 120, 0))
        im.save(os.path.join(outdir, mid + '.png'))


if __name__ == '__main__':
    main()
