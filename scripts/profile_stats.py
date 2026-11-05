"""Render profile cards from GitHub's contribution API; standard library only.

Run with GH_TOKEN and PROFILE_LOGIN. No token or raw API response is written.
Commit totals follow GitHub contribution rules; they are not all-time git totals.
"""

import calendar
import datetime as dt
import html
import json
import os
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BG = '#15111f'
CARD = '#211a30'
TEXT = '#f5f1fc'
MUTED = '#b2a6c8'
ACCENT = '#b8a1ff'
SECONDARY = '#dfd0ff'
LEVELS = {'NONE': '#292137', 'FIRST_QUARTILE': '#493766',
          'SECOND_QUARTILE': '#72569e', 'THIRD_QUARTILE': '#9477ce',
          'FOURTH_QUARTILE': ACCENT}

QUERY = '''query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date weekday contributionCount contributionLevel }
        }
      }
    }
  }
}'''


def fetch_collection(login, now):
    # Exactly 365 inclusive UTC calendar dates, with no future days.
    start = dt.datetime.combine(now.date() - dt.timedelta(days=364), dt.time(), dt.timezone.utc)
    variables = {'login': login, 'from': start.isoformat(), 'to': now.isoformat()}
    request = urllib.request.Request(
        'https://api.github.com/graphql',
        data=json.dumps({'query': QUERY, 'variables': variables}).encode(),
        headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
                 'Content-Type': 'application/json', 'User-Agent': 'profile-stats'},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = json.load(response)
    if payload.get('errors') or not payload.get('data', {}).get('user'):
        raise RuntimeError('GitHub contribution query failed; keeping previous cards.')
    return payload['data']['user']['contributionsCollection']


def text(x, y, value, size=20, color=MUTED, weight=400, extra=''):
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
            f'font-weight="{weight}" {extra}>{html.escape(str(value))}</text>')


def svg(height, title, description, elements):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" '
            f'viewBox="0 0 1200 {height}" role="img" aria-labelledby="title desc">'
            f'<title id="title">{html.escape(title)}</title>'
            f'<desc id="desc">{html.escape(description)}</desc>'
            f'<rect x=".5" y=".5" width="1199" height="{height-1}" rx="24" '
            f'fill="{BG}" stroke="#383047"/>'
            '<g font-family="Arial,Helvetica,sans-serif">' + ''.join(elements) + '</g></svg>\n')


def activity_summary(collection, today):
    days = sorted((day for week in collection['contributionCalendar']['weeks']
                   for day in week['contributionDays'] if day['date'] <= today.isoformat()),
                  key=lambda day: day['date'])
    active = longest = streak = 0
    previous = None
    for day in days:
        date = dt.date.fromisoformat(day['date'])
        if day['contributionCount']:
            active += 1
            streak = streak + 1 if previous == date - dt.timedelta(days=1) else 1
            longest = max(longest, streak)
        else:
            streak = 0
        previous = date
    return days, active, longest


def render(collection, now):
    days, active, longest = activity_summary(collection, now.date())
    if not days:
        raise ValueError('GitHub returned an empty contribution calendar.')
    period = f"{days[0]['date']} — {days[-1]['date']}"
    metrics = [
        ('Commit contributions', collection['totalCommitContributions'], ACCENT),
        ('Total contributions', collection['contributionCalendar']['totalContributions'], ACCENT),
        ('Pull requests opened', collection['totalPullRequestContributions'], ACCENT),
        ('Code reviews', collection['totalPullRequestReviewContributions'], SECONDARY),
        ('Days with activity', active, SECONDARY),
        ('Longest streak · days', longest, SECONDARY),
    ]
    parts = [text(40, 47, 'BUILDING, ONE CONTRIBUTION AT A TIME', 18, ACCENT, 700,
                  'letter-spacing="2"'), text(40, 82, period + ' · last 12 months', 20)]
    for index, (label, value, accent) in enumerate(metrics):
        x = 40 + (index % 3) * 380
        y = 111 + (index // 3) * 147
        parts.append(f'<rect x="{x}" y="{y}" width="360" height="128" rx="14" fill="{CARD}"/>')
        parts.extend([text(x+23, y+39, label, 21),
                      text(x+23, y+99, f'{value:,}', 53, TEXT, 700),
                      f'<rect x="{x+318}" y="{y+27}" width="5" height="73" rx="2.5" fill="{accent}"/>'])
    parts.append(text(40, 424, 'SOURCE / GITHUB CONTRIBUTIONS API', 16, MUTED, 400, 'letter-spacing="1.5"'))
    parts.append(text(1160, 424, 'UPDATED ' + now.strftime('%d %b %Y').upper(), 16, MUTED, 400, 'text-anchor="end"'))
    description = period + '. ' + '; '.join(f'{label}: {value:,}' for label, value, _ in metrics)
    metrics_svg = svg(452, 'GitHub activity — ' + period, description, parts)

    parts = [text(40, 48, 'A YEAR OF SHOWING UP', 18, ACCENT, 700, 'letter-spacing="2"'),
             text(40, 82, 'Daily contributions · ' + period, 20)]
    first = dt.date.fromisoformat(days[0]['date'])
    sunday = first - dt.timedelta(days=(first.weekday()+1) % 7)
    last_month = None
    for day in days:
        date = dt.date.fromisoformat(day['date'])
        week = (date - sunday).days // 7
        x, y = 75 + week*20, 126 + day['weekday']*21
        if date.month != last_month and (date.day == 1 or last_month is None):
            # The first partial month is labelled only if there is room before the next.
            if date.day <= 15:
                parts.append(text(x, 113, calendar.month_abbr[date.month], 16))
            last_month = date.month
        color = LEVELS[day['contributionLevel']]
        parts.append(f'<rect x="{x}" y="{y}" width="16" height="16" rx="4" fill="{color}">'
                     f'<title>{day["date"]}: {day["contributionCount"]} contributions</title></rect>')
    for label, row in [('M', 1), ('W', 3), ('F', 5)]:
        parts.append(text(40, 139 + row*21, label, 15))
    parts.append(text(40, 316, f'{active:,} active days / {longest:,}-day longest streak', 19, TEXT))
    parts.append(text(932, 316, 'Less', 15))
    for index, color in enumerate(LEVELS.values()):
        parts.append(f'<rect x="{978+index*23}" y="302" width="17" height="17" rx="4" fill="{color}"/>')
    parts.append(text(1100, 316, 'More', 15))
    return metrics_svg, svg(350, 'Daily GitHub activity — ' + period,
                            f'{active} active days. Longest streak: {longest} days. ' + period, parts)


def main():
    now = dt.datetime.now(dt.timezone.utc)
    collection = fetch_collection(os.environ.get('PROFILE_LOGIN', 'moh0405'), now)
    metrics, activity = render(collection, now)
    # Complete fetching and rendering before touching either existing asset.
    assets = ROOT / 'assets'
    assets.mkdir(exist_ok=True)
    (assets / 'metrics.svg').write_text(metrics, encoding='utf-8')
    (assets / 'activity.svg').write_text(activity, encoding='utf-8')
    print('Updated profile cards from GitHub contribution data.')


if __name__ == '__main__':
    main()
