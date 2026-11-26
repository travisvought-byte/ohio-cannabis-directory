#!/usr/bin/env python3
"""Writes the Silver Cup's prize values into the contest page and the official rules, from one silver spot price.

    python3 tools/pillage-contest/prize_values.py --spot 41.38 --source Kitco --when "2:11 PM Eastern on November 26, 2026"

Each page keeps its values between <!-- prize-values:start --> and <!-- prize-values:end -->, so a refresh changes
nothing else. The coin weights are the US Mint's: a 90% silver half dollar (1964 and earlier) holds 0.3617 troy ounces
of silver, and a 40% silver half dollar (1965 to 1970) holds 0.1479. The mix for 1st and 2nd is an assumption, stated
on both pages, because the sponsor picks the coins.
"""
import argparse
import html
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
NINETY, FORTY = 0.3617, 0.1479
# (place, coins, how many 90% and 40% halves are assumed). Third place is one coin of either kind.
PLACES = [('1st place', 10, 5, 5), ('2nd place', 5, 3, 2)]


def money(x):
    return '${:,.2f}'.format(x)


def oz(x):
    return '{:.3f}'.format(x)


def values(spot):
    rows = []
    for place, coins, a, b in PLACES:
        ozt = a * NINETY + b * FORTY
        rows.append((place, coins, a, b, ozt, ozt * spot))
    low = sum(r[4] for r in rows) + FORTY
    high = sum(r[4] for r in rows) + NINETY
    return rows, low, high


def rules_block(spot, source, when, kind):
    rows, low, high = values(spot)
    src = html.escape(source) + (', ' + html.escape(kind) if kind else '')
    out = ['<!-- prize-values:start -->',
           '<p>At the silver spot price of <b>{} a troy ounce</b> ({} price at {}), the silver in the prizes is worth about:</p>'.format(money(spot), src, html.escape(when)),
           '<div class="table-wrap"><table class="vals">',
           '<thead><tr><th scope="col">Prize</th><th scope="col">Coins (assumed mix)</th><th scope="col">Silver</th><th scope="col">Worth about</th></tr></thead>',
           '<tbody>']
    for place, coins, a, b, ozt, usd in rows:
        out.append('<tr><th scope="row">{}</th><td>{} halves: {} of 90% and {} of 40%</td><td>{} oz</td><td>{}</td></tr>'.format(place, coins, a, b, oz(ozt), money(usd)))
    out.append('<tr><th scope="row">3rd place</th><td>1 half, 40% or 90%</td><td>{} to {} oz</td><td>{} to {}</td></tr>'.format(oz(FORTY), oz(NINETY), money(FORTY * spot), money(NINETY * spot)))
    out.append('<tr><th scope="row">All three</th><td>16 halves</td><td>{} to {} oz</td><td>{} to {}</td></tr>'.format(oz(low), oz(high), money(low * spot), money(high * spot)))
    out += ['</tbody></table></div>',
            '<p class="muted">One 90% silver half dollar holds 0.3617 troy ounces of silver, about {} at that price. One 40% silver half dollar holds 0.1479 troy ounces, about {}.</p>'.format(money(NINETY * spot), money(FORTY * spot)),
            '<!-- prize-values:end -->']
    return '\n'.join(out)


def page_block(spot, source, when, kind):
    rows, low, high = values(spot)
    src = html.escape(source) + (', ' + html.escape(kind) if kind else '')
    first, second = rows
    out = ['<!-- prize-values:start -->',
           '<ol class="prizes">',
           '<li><b>1st place:</b> 10 silver half dollars, about {} oz of silver, worth about {}.</li>'.format(oz(first[4]), money(first[5])),
           '<li><b>2nd place:</b> 5 silver half dollars, about {} oz of silver, worth about {}.</li>'.format(oz(second[4]), money(second[5])),
           '<li><b>3rd place:</b> 1 silver half dollar, worth {} to {}.</li>'.format(money(FORTY * spot), money(NINETY * spot)),
           '</ol>',
           '<p class="muted">Values are approximate, at the silver spot price of {} a troy ounce ({} price at {}), and they move with the price of silver. They assume first place gets five 90% and five 40% halves and second place three 90% and two 40%. The sponsor picks the coins: every one is at least 40% silver, and about half of them are 90%. All three prizes together come to about {} to {}. <a href="contest-rules.html#prizes">The details are in the official rules.</a></p>'.format(
               money(spot), src, html.escape(when), money(low * spot), money(high * spot)),
           '<!-- prize-values:end -->']
    return '\n'.join(out)


def write(path, block):
    p = ROOT / path
    s = p.read_text()
    new, n = re.subn(r'<!-- prize-values:start -->.*?<!-- prize-values:end -->', lambda m: block, s, flags=re.S)
    if n != 1:
        raise SystemExit('{}: expected one prize-values block, found {}'.format(path, n))
    p.write_text(new)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--spot', type=float, required=True, help='silver spot price, US dollars a troy ounce')
    ap.add_argument('--source', required=True, help='where the price came from, like Kitco')
    ap.add_argument('--when', required=True, help='when the price was read, like "2:11 PM Eastern on November 26, 2026"')
    ap.add_argument('--kind', default='bid', help='which price it is, like bid (default)')
    a = ap.parse_args()
    write('pillage/contest-rules.html', rules_block(a.spot, a.source, a.when, a.kind))
    write('pillage/contest.html', page_block(a.spot, a.source, a.when, a.kind))
    print('prize values written at', money(a.spot))


if __name__ == '__main__':
    main()
