import datetime as dt
import html
import json
import math
import os
import urllib.request

USERNAME = "Harsheys_26"
ENDPOINT = "https://leetcode.com/graphql"

QUERY = """
query UserProfile($username: String!) {
  allQuestionsCount {
    difficulty
    count
  }
  matchedUser(username: $username) {
    submitStatsGlobal {
      acSubmissionNum {
        difficulty
        count
        submissions
      }
      totalSubmissionNum {
        difficulty
        count
        submissions
      }
    }
    profile {
      ranking
      reputation
    }
    submissionCalendar
  }
  userContestRanking(username: $username) {
    attendedContestsCount
    rating
    globalRanking
    topPercentage
  }
}
"""

def as_int(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0

def mapped(rows):
    return {row["difficulty"]: as_int(row["count"]) for row in rows}

def fmt(value):
    return f"{as_int(value):,}"

def esc(value):
    return html.escape(str(value))

def fetch_data():
    payload = json.dumps({
        "query": QUERY,
        "variables": {"username": USERNAME}
    }).encode("utf-8")

    request = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (GitHubActions)",
            "Origin": "https://leetcode.com",
            "Referer": "https://leetcode.com/",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))

    if result.get("errors"):
        raise RuntimeError(result["errors"][0].get("message", "LeetCode API error"))

    data = result.get("data", {})
    if not data.get("matchedUser"):
        raise RuntimeError("LeetCode user not found: " + USERNAME)

    return data

def current_streak(calendar_text):
    if not calendar_text:
        return 0

    try:
        calendar = json.loads(calendar_text)
    except Exception:
        return 0

    active_days = set()
    for timestamp, count in calendar.items():
        if as_int(count) <= 0:
            continue
        try:
            active_days.add(
                dt.datetime.fromtimestamp(
                    int(timestamp),
                    tz=dt.timezone.utc
                ).date()
            )
        except Exception:
            continue

    cursor = dt.datetime.now(dt.timezone.utc).date()
    streak = 0
    while cursor in active_days:
        streak += 1
        cursor -= dt.timedelta(days=1)

    return streak

def progress_width(value, total, max_width=430):
    if total <= 0:
        return 0
    return max_width * min(1, max(0, value / total))

def build_svg(data):
    user = data["matchedUser"]
    totals = mapped(data["allQuestionsCount"])
    solved = mapped(user["submitStatsGlobal"]["acSubmissionNum"])
    submissions = mapped(user["submitStatsGlobal"]["totalSubmissionNum"])

    easy = solved.get("Easy", 0)
    medium = solved.get("Medium", 0)
    hard = solved.get("Hard", 0)
    total = solved.get("All", easy + medium + hard)

    total_questions = totals.get(
        "All",
        totals.get("TOTAL", totals.get("Easy", 0) + totals.get("Medium", 0) + totals.get("Hard", 0))
    )

    total_submissions = submissions.get("All", 0)
    ranking = as_int(user.get("profile", {}).get("ranking"))
    streak = current_streak(user.get("submissionCalendar"))

    contest = data.get("userContestRanking") or {}
    rating = round(float(contest.get("rating") or 0))
    contest_count = as_int(contest.get("attendedContestsCount"))
    contest_rank = as_int(contest.get("globalRanking"))
    top_pct = contest.get("topPercentage")

    width = 920
    height = 500
    radius = 78
    circumference = 2 * math.pi * radius
    ratio = min(1, total / max(total_questions, 1))
    ring_end = circumference * (1 - ratio)

    parts = []
    add = parts.append

    add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">')
    add(f'''
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#080B14"/>
    <stop offset="55%" stop-color="#11172A"/>
    <stop offset="100%" stop-color="#21143A"/>
  </linearGradient>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#312E81"/>
    <stop offset="50%" stop-color="#8B5CF6"/>
    <stop offset="100%" stop-color="#2563EB"/>
  </linearGradient>
  <linearGradient id="ring" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#A78BFA"/>
    <stop offset="100%" stop-color="#22D3EE"/>
  </linearGradient>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="3.5" result="blur"/>
    <feMerge>
      <feMergeNode in="blur"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
  <style>
    .title{{font:700 26px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;fill:#F8FAFC}}
    .sub{{font:500 14px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;fill:#94A3B8}}
    .label{{font:700 15px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;fill:#E2E8F0}}
    .value{{font:800 25px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;fill:#FFFFFF}}
    .small{{font:500 12px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;fill:#94A3B8}}
    .ring{{stroke-dasharray:{circumference:.2f};stroke-dashoffset:{circumference:.2f};animation:ring 1.6s ease-out .1s both}}
    .fill{{transform-origin:left center;transform:scaleX(0);animation:fill 1.2s ease-out both}}
    .pop{{animation:pop .65s ease-out both}}
    .pulse{{animation:pulse 2.4s ease-in-out infinite}}
    @keyframes ring{{from{{stroke-dashoffset:{circumference:.2f}}}to{{stroke-dashoffset:{ring_end:.2f}}}}}
    @keyframes fill{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
    @keyframes pop{{0%{{opacity:0;transform:scale(.78)}}70%{{opacity:1;transform:scale(1.05)}}100%{{opacity:1;transform:scale(1)}}}}
    @keyframes pulse{{0%,100%{{opacity:.65}}50%{{opacity:1}}}}
  </style>
</defs>''')

    add('<rect x="8" y="8" width="904" height="484" rx="28" fill="url(#bg)" stroke="url(#edge)" stroke-width="2"/>')
    add('<circle cx="62" cy="62" r="26" fill="#FFA116"/>')
    add('<text x="62" y="69" text-anchor="middle" font-family="Arial" font-weight="800" font-size="21" fill="#111827">LC</text>')
    add(f'<text x="103" y="57" class="title">LeetCode Analytics</text>')
    add(f'<text x="103" y="80" class="sub">@{esc(USERNAME)} · live profile data</text>')
    add('<circle class="pulse" cx="856" cy="54" r="6" fill="#22D3EE"/>')
    add('<text x="870" y="59" class="small">LIVE</text>')

    add(f'<g transform="translate(34 126)"><circle cx="120" cy="120" r="{radius}" fill="none" stroke="#252B3F" stroke-width="16"/>')
    add(f'<circle class="ring" cx="120" cy="120" r="{radius}" fill="none" stroke="url(#ring)" stroke-width="16" stroke-linecap="round" transform="rotate(-90 120 120)" filter="url(#glow)"/>')
    add(f'<text x="120" y="113" text-anchor="middle" class="value">{fmt(total)}</text>')
    add('<text x="120" y="138" text-anchor="middle" class="sub">problems solved</text>')
    add(f'<text x="120" y="159" text-anchor="middle" class="small">of {fmt(total_questions)}</text></g>')

    add('<g transform="translate(402 130)">')
    add('<text x="0" y="0" class="label">Difficulty Breakdown</text>')

    rows = [
        ("Easy", easy, totals.get("Easy", 1), "#22C55E", 45, ".15s"),
        ("Medium", medium, totals.get("Medium", 1), "#F59E0B", 125, ".30s"),
        ("Hard", hard, totals.get("Hard", 1), "#EF4444", 205, ".45s"),
    ]

    for name, value, denom, color, y, delay in rows:
        width_value = progress_width(value, denom)
        add(f'<text x="0" y="{y}" class="label">{name}</text>')
        add(f'<text x="86" y="{y}" class="sub">{fmt(value)} / {fmt(denom)}</text>')
        add(f'<rect x="0" y="{y+15}" width="430" height="12" rx="6" fill="#252B3F"/>')
        add(f'<rect class="fill" x="0" y="{y+15}" width="{width_value:.1f}" height="12" rx="6" fill="{color}" style="animation-delay:{delay}"/>')

    add('<text x="0" y="285" class="label">Profile Metrics</text>')

    cards = [
        ("Current Streak", fmt(streak), "days"),
        ("Submissions", fmt(total_submissions), ""),
        ("Contest Rating", fmt(rating) if rating else "—", ""),
    ]

    for index, (label, value, suffix) in enumerate(cards):
        x = index * 205
        delay = 0.15 + index * 0.13
        add(f'<g class="pop" style="animation-delay:{delay:.2f}s"><rect x="{x}" y="305" width="190" height="78" rx="16" fill="#111827" stroke="#2D3343"/>')
        add(f'<text x="{x+18}" y="333" class="small">{label}</text>')
        add(f'<text x="{x+18}" y="366" class="value">{value}</text>')
        if suffix:
            add(f'<text x="{x+85}" y="366" class="small">{suffix}</text>')
        add('</g>')

    add('</g>')

    top_text = f' · Top {float(top_pct):.1f}%' if top_pct else ''
    rank_text = fmt(contest_rank) if contest_rank else "—"
    add(f'<text x="38" y="458" class="sub">Rank: {fmt(ranking) if ranking else "—"} · Contests: {fmt(contest_count) if contest_count else "—"} · Global contest rank: {rank_text}{top_text}</text>')
    add('<text x="882" y="458" text-anchor="end" class="small">Auto-updated by GitHub Actions</text>')
    add('</svg>')

    return "".join(parts)

def main():
    os.makedirs("dist", exist_ok=True)
    data = fetch_data()
    with open("dist/leetcode-card.svg", "w", encoding="utf-8") as file:
        file.write(build_svg(data))

if __name__ == "__main__":
    main()
