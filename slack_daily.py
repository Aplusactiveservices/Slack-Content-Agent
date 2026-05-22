#!/usr/bin/env python3
"""
Anthony's Daily Content Creator Brief — GitHub Actions / Cloud Version
Runs at 11 AM UTC daily (6-7 AM ET). Sends daily brief to Slack.
"""

import os, sys, json, datetime, urllib.request, traceback
from zoneinfo import ZoneInfo
from openai import OpenAI

# ── Config ────────────────────────────────────────────────────────
SLACK_WEBHOOK = os.environ["SLACK_WEBHOOK"]
OPENAI_KEY    = os.environ["OPENAI_API_KEY"]
ET            = ZoneInfo("America/New_York")

# ── Weekly schedule ───────────────────────────────────────────────
SCHEDULE = {
    6: {"day": "Sunday",    "emoji": "☀️",  "platform": "LinkedIn",     "focus": "Value/Tool Drop — 5 AI tools any business owner can use today"},
    0: {"day": "Monday",    "emoji": "🏛️",  "platform": "TikTok HBCU",  "focus": "Story/Lesson — HBCU experience + real-world business value"},
    1: {"day": "Tuesday",   "emoji": "🤖",  "platform": "YouTube AI",   "focus": "Tutorial/Brand — AI education for minorities and beginners"},
    2: {"day": "Wednesday", "emoji": "🎵",  "platform": "TikTok Music", "focus": "Behind-the-Scenes — music creation process, voice memo to finished track"},
    3: {"day": "Thursday",  "emoji": "💼",  "platform": "LinkedIn",     "focus": "Story Post — AI entrepreneurship origin story, authenticity"},
    4: {"day": "Friday",    "emoji": "🏛️",  "platform": "TikTok HBCU",  "focus": "Pride/Belonging — the HBCU campus feeling and what it gives you"},
    5: {"day": "Saturday",  "emoji": "🎵",  "platform": "TikTok Music", "focus": "Music-First — emotional/lifestyle content, let the song lead"},
}

# ── Competitor context ────────────────────────────────────────────
COMP_CONTEXT = {
    "YouTube AI": """
Competitors (study what's WORKING for them right now):
• Sandy Lee (@sandyleeai) — Creator-to-creator AI automation. n8n pipelines. Warm, accessible tone. 10K subs in 4 months. What's working: relatable "I built this as a creator" framing + very specific tool walkthroughs.
• Liam Ottley (@LiamOttley) — 700K subs. What's working: ~29-min long-form, income transparency, "I'll show you what I actually made" hooks, anti-guru tone.
• Nick Saraev (@nicksaraev) — n8n + Make.com. What's working: specific dollar amounts in every title, free resources, "copy my workflow" format (875K views on one video).
• Nate Herk (@nateherk) — 680K subs in 18 months. What's working: near-daily uploads, beginner-first language, Goldman Sachs credibility used sparingly as trust anchor.
Anthony's UNCLAIMED LANE: None of them talk to Black/minority professionals. He owns "AI for us — for real people, not tech bros." This angle is wide open and should be front and center in every script.
""",
    "LinkedIn": """
Competitors (study what's WORKING for them right now):
• Kasey Brown — 200K followers. What's working: contrarian hooks ("You don't need a website"), comment-for-resource CTAs, posting 2x/week so each post gets more dwell time.
• Patrick Dang — Transformation/story hooks. What's working: "From X to Y in Z time" structure, YouTube-to-LinkedIn repurpose flywheel.
• Shubham Saboo — Daily posts. What's working: always attaches a free resource, uses a 55K-star GitHub repo as trust anchor.
Anthony's UNCLAIMED LANE: Practical AI education for Black entrepreneurs — no jargon, no gatekeeping, real-life application. Nobody owns this lane on LinkedIn.
""",
    "TikTok HBCU": """
Competitors (study what's WORKING for them right now):
• HBCU Alumni (@hbcualum) — 70K followers. What's working: nostalgia + bands + inter-school debate drives comment wars.
• HBCU Grad (@hbcugrads) — 205M+ views on hashtag. What's working: chapter-level Greek life specificity drives shares within friend groups.
• QuailNotFunny (@quailnotfunny) — 78K followers. What's working: provocateur hooks, multi-part series format keeps people coming back.
Anthony's UNCLAIMED LANE: HBCU alumnus who actually built something and came back to teach — belonging + humor + real-world wisdom.
""",
    "TikTok Music": """
Competitors (study what's WORKING for them right now):
• Zeddy Will (@willzeddy) — NYC confidence rap. What's working: POV skits + music combo, viral participation mechanics.
• Nic D (@iamnicd) — Raw, simple TikTok. What's working: love + wordplay, humble captions, sincere and unpolished = trust.
• Connor Price (@connorprice__) — What's working: platform-first strategy, globe-spinning series (72M views one ep).
Anthony's UNCLAIMED LANE: Calm artist who shows the AI + creative process behind the music. That intersection is completely open.
""",
}

BRAND_VOICE = """
ANTHONY'S BRAND — internalize this before writing a single word:
Voice: Calm, relatable, concise, educational, lifestyle-driven, authentic confidence. NOT hype. NOT guru. NOT tech-bro.
Platforms: LinkedIn (AI business), YouTube AI (AI education for minorities), YouTube Music + TikTok Music (calm lifestyle music), TikTok HBCU (community + belonging).
Core mission: Teach AI to everyday people especially minorities. Build real community. Grow authentically.
Content pillars:
  — AI content = education + inspiration. Make people feel like THEY can do this too.
  — HBCU content = belonging + humor + real value. Bring people back to that feeling.
  — Music content = calm lifestyle + emotional connection. Let the music speak first.
Unique positioning: Anthony sits at the intersection of tech, Black culture, and calm lifestyle. That combination doesn't exist anywhere else.
"""

# ── Logging ───────────────────────────────────────────────────────
def log(msg):
    ts = datetime.datetime.now(ET).strftime("%Y-%m-%d %H:%M:%S ET")
    print(f"[{ts}] {msg}", flush=True)

# ── AI Content Generation ──────────────────────────────────────────
def generate_content(sched, now_et):
    platform = sched["platform"]
    day      = sched["day"]
    focus    = sched["focus"]
    comp     = COMP_CONTEXT.get(platform, "")
    date_str = now_et.strftime("%B %d, %Y")
    is_yt    = "YouTube" in platform

    yt_fields = """
  "thumbnail_prompt": "detailed prompt for the YouTube thumbnail visual",
  "description": "full YouTube video description ready to copy-paste",""" if is_yt else """
  "thumbnail_prompt": null,
  "description": null,"""

    prompt = f"""Today is {date_str} ({day}). Generate a fresh daily content brief for Anthony's {platform} channel.

ANTHONY'S BRAND:
{BRAND_VOICE}

TODAY'S CONTENT FOCUS: {focus}

COMPETITOR INTELLIGENCE:
{comp}

Return ONLY a valid JSON object. Use exactly these keys:
{{
  "what_to_post": "one-line description of the specific post",
  "best_time": "best posting time in EST",
  "why_it_works": "3 sentences on why this content works",
  "hook": "the exact opening hook line",
  "script": "full script or post body in Anthony's voice",{yt_fields}
  "trending_note": "one specific sentence on what format/topic is trending RIGHT NOW"
}}"""

    client = OpenAI(api_key=OPENAI_KEY)
    resp = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=3000,
        messages=[
            {"role": "system", "content": "You are Anthony's AI content strategist. Return only valid JSON — no markdown blocks, no extra text."},
            {"role": "user", "content": prompt},
        ],
    )
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

# ── Fallback static content ────────────────────────────────────────
FALLBACK = {
    6: {"what_to_post": "5 AI tools any business owner can use today", "best_time": "11:00 AM EST",
        "why_it_works": "Sunday professionals scroll before the week starts.",
        "hook": "Most people are waiting until they 'fully understand' AI. That's the wrong move.",
        "script": "Post the AI tools list. Keep it 5 bullets, plain language. End: 'Drop a robot emoji if you're using any of these.'",
        "thumbnail_prompt": None, "description": None, "trending_note": "AI productivity tools are dominating LinkedIn feeds."},
    0: {"what_to_post": "What my HBCU taught me about business", "best_time": "7:00 PM EST",
        "why_it_works": "Monday evening HBCU TikTok is active.",
        "hook": "The thing my HBCU taught me about business that I didn't realize until years later...",
        "script": "Story about a specific HBCU moment. End: 'Drop your school below let's see who's out here.'",
        "thumbnail_prompt": None, "description": None, "trending_note": "HBCU community content spikes Monday evenings."},
    1: {"what_to_post": "AI For Us — origin video + 3 beginner tools", "best_time": "Upload by 12:00 PM EST",
        "why_it_works": "Tuesday is peak YouTube upload day.",
        "hook": "Nobody in AI is talking to us. So I taught myself — and now I'm coming back to show you how.",
        "script": "Origin story + walk through 3 beginner AI tools. Close: 'Subscribe — I drop one of these every week.'",
        "thumbnail_prompt": "Anthony centered, calm direct eye contact. Bold text: 'AI FOR US'. Dark navy background.",
        "description": "Everyone's teaching AI. But who's teaching it for regular people?\n\nBreaking down the 3 AI tools I use every week.\n\nSubscribe for weekly AI breakdowns.",
        "trending_note": "AI tool tutorials are the top performing format in this niche right now."},
    2: {"what_to_post": "Voice memo to finished song — behind the scenes", "best_time": "8:00 PM EST",
        "why_it_works": "Wednesday evening is midweek music discovery time.",
        "hook": "This started as a voice memo at 2am...",
        "script": "Play raw voice memo then finished track. Text overlay: 'Made this one for the late nights.'",
        "thumbnail_prompt": None, "description": None, "trending_note": "Behind-the-scenes music creation is spiking on TikTok."},
    3: {"what_to_post": "I grew up thinking tech wasn't for me — origin story", "best_time": "8:00 AM EST",
        "why_it_works": "Thursday AM is LinkedIn peak for personal story content.",
        "hook": "I grew up thinking tech was for other people. Then I built an AI business.",
        "script": "Story: outside of tech to now teaching others. End: 'Follow if you're building something most people don't understand yet.'",
        "thumbnail_prompt": None, "description": None, "trending_note": "Founder origin stories are LinkedIn's top engagement format."},
    4: {"what_to_post": "You only understand this if you went to an HBCU", "best_time": "6:00 PM EST",
        "why_it_works": "Friday evening is celebration mode.",
        "hook": "You only understand this if you went to an HBCU...",
        "script": "Describe the specific feeling of being on an HBCU campus. End: 'Drop your school let's go.'",
        "thumbnail_prompt": None, "description": None, "trending_note": "HBCU pride content peaks on Fridays."},
    5: {"what_to_post": "Music plays first — one honest line of text", "best_time": "4:00 PM EST",
        "why_it_works": "Saturday afternoon is peak music discovery.",
        "hook": "[First 3 seconds: play the opening hook of the song — no talking]",
        "script": "Music starts immediately. Text overlay: 'Made this when I needed to feel like myself again.' 30-45 seconds.",
        "thumbnail_prompt": None, "description": None, "trending_note": "Calm/lifestyle music content outperforms on Saturday afternoons."},
}

# ── Slack blocks ───────────────────────────────────────────────────
def _chunks(text, limit=2900):
    blocks = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut == -1:
            cut = limit
        blocks.append(text[:cut])
        text = text[cut:].lstrip("\n")
    blocks.append(text)
    return [{"type": "section", "text": {"type": "mrkdwn", "text": c}} for c in blocks if c.strip()]

def build_blocks(sched, content, now_et, refreshed):
    day, emoji, platform = sched["day"], sched["emoji"], sched["platform"]
    date_str   = now_et.strftime("%B %d, %Y")
    refresh_ts = now_et.strftime("%I:%M %p ET") if refreshed else "static fallback"

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} Anthony's Content Brief — {day}, {date_str}", "emoji": True}},
        {"type": "divider"},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": f"*Platform*\n{platform}"},
            {"type": "mrkdwn", "text": f"*Best Time*\n{content['best_time']}"},
        ]},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*What to Post*\n{content['what_to_post']}"}},
    ]

    if content.get("trending_note"):
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Trending*\n_{content['trending_note']}_"}})

    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Hook*\n\"{content['hook']}\""}})
    blocks.append({"type": "divider"})
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "*Script*"}})
    blocks.extend(_chunks(content["script"]))

    if content.get("thumbnail_prompt"):
        blocks.append({"type": "divider"})
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Thumbnail Prompt*\n{content['thumbnail_prompt']}"}})

    if content.get("description"):
        blocks.append({"type": "divider"})
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "*Description*"}})
        blocks.extend(_chunks(content["description"]))

    blocks.append({"type": "context", "elements": [
        {"type": "mrkdwn", "text": f"AI-refreshed {refresh_ts}  |  Content Creator AI Agent"}
    ]})

    return blocks

# ── Send to Slack ──────────────────────────────────────────────────
def send_slack(blocks):
    payload = json.dumps({"blocks": blocks}).encode("utf-8")
    req = urllib.request.Request(
        SLACK_WEBHOOK,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode("utf-8")

# ── Main ───────────────────────────────────────────────────────────
def main():
    now_et  = datetime.datetime.now(ET)
    weekday = now_et.weekday()
    log(f"=== Daily run started | {now_et.strftime('%B %d, %Y (%A)')} | weekday={weekday} ===")

    sched = SCHEDULE.get(weekday)
    if not sched:
        log("No schedule entry for today — exiting.")
        return

    log(f"Platform: {sched['platform']}")

    content, refreshed = None, False
    try:
        log("Calling OpenAI API...")
        content   = generate_content(sched, now_et)
        refreshed = True
        log("AI content generated.")
    except Exception as e:
        log(f"AI generation failed — using fallback. Error: {e}")
        content = FALLBACK.get(weekday, {})

    try:
        blocks   = build_blocks(sched, content, now_et, refreshed)
        response = send_slack(blocks)
        log(f"Slack response: {response}")
    except Exception as e:
        log(f"Slack send failed: {e}\n{traceback.format_exc()}")
        sys.exit(1)

    log("=== Daily run complete ===\n")

if __name__ == "__main__":
    main()
