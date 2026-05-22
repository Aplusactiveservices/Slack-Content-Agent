#!/usr/bin/env python3
"""
Anthony's Daily Content Creator Brief — GitHub Actions / Cloud Version
Runs at 11 AM UTC daily (≈6–7 AM ET). No local files — Slack + image only.
"""

import os, sys, json, datetime, urllib.request, traceback, io
from zoneinfo import ZoneInfo
from openai import OpenAI
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from textwrap import fill as tw_fill

# ── Config (from environment variables) ───────────────────────────
SLACK_WEBHOOK = os.environ["SLACK_WEBHOOK"]
OPENAI_KEY    = os.environ["OPENAI_API_KEY"]
ET            = ZoneInfo("America/New_York")

PLATFORM_COLORS = {
    "YouTube AI":   "#FF4B4B",
    "LinkedIn":     "#0A66C2",
    "TikTok HBCU":  "#69C9D0",
    "TikTok Music": "#C850C0",
}

# ── Weekly schedule (Python weekday: Mon=0 … Sun=6) ───────────────
SCHEDULE = {
    6: {"day": "Sunday",    "emoji": "☀️",  "platform": "LinkedIn",     "focus": "Value/Tool Drop — 5 AI tools any business owner can use today"},
    0: {"day": "Monday",    "emoji": "🏛️",  "platform": "TikTok HBCU",  "focus": "Story/Lesson — HBCU experience + real-world business value"},
    1: {"day": "Tuesday",   "emoji": "🤖",  "platform": "YouTube AI",   "focus": "Tutorial/Brand — AI education for minorities and beginners"},
    2: {"day": "Wednesday", "emoji": "🎵",  "platform": "TikTok Music", "focus": "Behind-the-Scenes — music creation process, voice memo to finished track"},
    3: {"day": "Thursday",  "emoji": "💼",  "platform": "LinkedIn",     "focus": "Story Post — AI entrepreneurship origin story, authenticity"},
    4: {"day": "Friday",    "emoji": "🏛️",  "platform": "TikTok HBCU",  "focus": "Pride/Belonging — the HBCU campus feeling and what it gives you"},
    5: {"day": "Saturday",  "emoji": "🎵",  "platform": "TikTok Music", "focus": "Music-First — emotional/lifestyle content, let the song lead"},
}

# ── Competitor context per platform ───────────────────────────────
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
Anthony's UNCLAIMED LANE: Practical AI education for Black entrepreneurs — no jargon, no gatekeeping, real-life application. Nobody owns this lane on LinkedIn. Every post should end with a CTA that brings people back to his story.
""",
    "TikTok HBCU": """
Competitors (study what's WORKING for them right now):
• HBCU Alumni (@hbcualum) — 70K followers. What's working: nostalgia + bands + inter-school debate drives comment wars (comments = reach).
• HBCU Grad (@hbcugrads) — 205M+ views on hashtag. What's working: chapter-level Greek life specificity drives shares within friend groups.
• QuailNotFunny (@quailnotfunny) — 78K followers. What's working: provocateur hooks, multi-part series format keeps people coming back.
Anthony's UNCLAIMED LANE: HBCU alumnus who actually built something and came back to teach — belonging + humor + real-world wisdom. Every video should have the "you already know this feeling" hook that pulls in the community before he adds his unique angle.
""",
    "TikTok Music": """
Competitors (study what's WORKING for them right now):
• Zeddy Will (@willzeddy) — NYC confidence rap. What's working: POV skits + music combo, viral participation mechanics (strut/dance trends get remixed).
• Nic D (@iamnicd) — Raw, simple TikTok. What's working: love + wordplay, humble captions ("glad this found its audience"), sincere and unpolished = trust.
• Connor Price (@connorprice__) — What's working: platform-first strategy, globe-spinning series (72M views one ep), copyright-free music = organic spread.
Anthony's UNCLAIMED LANE: Calm artist who shows the AI + creative process behind the music. That intersection (chill music + AI production process) is completely open. Let the audio lead, keep visuals minimal and lifestyle-focused.
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
Unique positioning: Anthony sits at the intersection of tech, Black culture, and calm lifestyle. That combination doesn't exist anywhere else. Every piece of content should feel like it could ONLY come from him.
Growth challenges to actively address: increasing YouTube watch time, restarting HBCU TikTok growth, building a loyal music listener base.
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

ANTHONY'S BRAND — read this carefully before writing anything:
{BRAND_VOICE}

TODAY'S CONTENT FOCUS: {focus}

COMPETITOR INTELLIGENCE — what's actually working right now:
{comp}

Your job is to generate content that:

1. GROUNDS THE SCRIPT IN WHAT'S WORKING: Study the competitor tactics above. Identify the specific format, hook style, or structural move that's driving results for similar creators RIGHT NOW, then adapt it for Anthony's unique lane. Name the tactic you're borrowing and why.

2. TRENDS FOR TODAY, {date_str}: Research what's currently dominating {platform} in this niche. Your trending_note should be specific and actionable — not generic ("AI is popular") but precise ("Short-form 'I tried X for 30 days' format is getting 3-5x normal reach on YouTube AI this week").

3. IS PERSONAL TO ANTHONY'S BRAND: Every word of the script should sound like it could ONLY come from Anthony. Calm confidence. No hype. If it could be posted by any AI creator, rewrite it. His angle — teaching AI to everyday people especially minorities, HBCU community, and calm lifestyle music — should be woven into the content naturally, not bolted on.

4. FOLLOWS PLATFORM BEST PRACTICES:
   - TikTok: Hook within first 2 seconds, pattern interrupt, text overlay matters, comment prompt at end
   - LinkedIn: Value in first line (no "I'm excited to share"), story-driven, concrete takeaway
   - YouTube: Strong open that answers "why watch this?", thumbnail text integration, watch-time retention mechanics built into script structure

5. BUILDS ANTHONY AS A CREATOR: Each piece of content should slightly expand his brand — make him more recognizable, more trusted, more likely to be followed. Think about what makes someone subscribe after seeing this.

Return ONLY a valid JSON object — no markdown, no code fences, no explanation. Use exactly these keys:
{{
  "what_to_post": "one-line description of the specific post",
  "best_time": "best posting time in EST",
  "why_it_works": "3 sentences: (1) the competitor tactic you borrowed and adapted, (2) why this angle hits different for Anthony vs. competitors, (3) what watch/engagement mechanic is built in",
  "hook": "the exact opening hook line — must stop the scroll in under 2 seconds",
  "script": "full script or post body — include scene directions for video, pacing notes, text overlays. Written in Anthony's voice. Should feel personal and real.",{yt_fields}
  "trending_note": "one specific sentence on what format/topic is trending RIGHT NOW in this niche that shaped this content choice"
}}"""

    client = OpenAI(api_key=OPENAI_KEY)
    resp = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=3000,
        messages=[
            {"role": "system", "content": "You are Anthony's AI content strategist. You study what's working for competitors and translate it into content that fits Anthony's unique brand. Return only valid JSON — no markdown blocks, no extra text."},
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
        "why_it_works": "Sunday professionals scroll before the week starts. Value content hits hardest here. Nick Saraev's 'copy my workflow' format adapted for Anthony's lane.",
        "hook": "Most people are waiting until they 'fully understand' AI. That's the wrong move.",
        "script": "Post the AI tools list with a comment prompt asking what they'd automate. Keep it 5 bullets, plain language, no jargon. End: 'Drop a 🤖 if you're using any of these.'",
        "thumbnail_prompt": None, "description": None, "trending_note": "AI productivity tools are dominating LinkedIn feeds."},
    0: {"what_to_post": "What my HBCU taught me about business", "best_time": "7:00 PM EST",
        "why_it_works": "Monday evening HBCU TikTok is active. Lesson angle works on Mondays. HBCU Alumni's nostalgia format adapted with Anthony's real-world business layer.",
        "hook": "The thing my HBCU taught me about business that I didn't realize until years later...",
        "script": "Story about a specific HBCU moment that was actually a business lesson. Calm delivery. End with: 'Drop your school below 👇 let's see who's out here.'",
        "thumbnail_prompt": None, "description": None, "trending_note": "HBCU community content spikes Monday evenings."},
    1: {"what_to_post": "AI For Us — origin video + 3 beginner tools", "best_time": "Upload by 12:00 PM EST",
        "why_it_works": "Tuesday is peak YouTube upload day. Nate Herk's beginner-first format + Anthony's minority angle = untapped audience. Origin videos build long-term channel identity.",
        "hook": "Nobody in AI is talking to us. So I taught myself — and now I'm coming back to show you how.",
        "script": "Origin story + walk through 3 beginner AI tools with screen share. Calm, no hype. Close: 'Subscribe — I drop one of these every week and I'm not going anywhere.'",
        "thumbnail_prompt": "Anthony centered, calm direct eye contact. Bold text: 'AI FOR US'. Dark navy background, subtle tech texture.",
        "description": "Everyone's teaching AI. But who's teaching it for regular people?\n\nBreaking down the 3 AI tools I use every week — no tech background needed.\n\nSubscribe for weekly AI breakdowns that don't leave you behind.",
        "trending_note": "AI tool tutorials are the #1 performing format in this niche right now."},
    2: {"what_to_post": "Voice memo to finished song — behind the scenes", "best_time": "8:00 PM EST",
        "why_it_works": "Wednesday evening is midweek music discovery time. Nic D's raw/humble format — let the music speak, keep text minimal.",
        "hook": "This started as a voice memo at 2am...",
        "script": "Play raw voice memo → finished track. Let the music breathe. One honest text overlay: 'Made this one for the late nights.' Let it run 30–45 seconds.",
        "thumbnail_prompt": None, "description": None, "trending_note": "Behind-the-scenes music creation is spiking on TikTok."},
    3: {"what_to_post": "I grew up thinking tech wasn't for me — origin story", "best_time": "8:00 AM EST",
        "why_it_works": "Thursday AM is LinkedIn's peak for personal story content. Patrick Dang's transformation hook adapted for Anthony's real story.",
        "hook": "I grew up thinking tech was for other people. Then I built an AI business.",
        "script": "Story: outside of tech → YouTube + trial and error → now teaching others. Calm, honest. End: 'Follow if you're building something most people don't understand yet.'",
        "thumbnail_prompt": None, "description": None, "trending_note": "Founder origin stories are LinkedIn's top engagement format this week."},
    4: {"what_to_post": "You only understand this if you went to an HBCU", "best_time": "6:00 PM EST",
        "why_it_works": "Friday evening is celebration mode. QuailNotFunny's insider hook format — the 'you only know if you know' mechanic drives shares.",
        "hook": "You only understand this if you went to an HBCU...",
        "script": "Describe the specific feeling of being on an HBCU campus. The belonging. Calm, not loud. End: 'Drop your school 👇 let's go.'",
        "thumbnail_prompt": None, "description": None, "trending_note": "HBCU pride content peaks on Fridays across all platforms."},
    5: {"what_to_post": "Music plays first — one honest line of text", "best_time": "4:00 PM EST",
        "why_it_works": "Saturday afternoon is peak music discovery. Connor Price's audio-forward format — let the music create the mood before anything else.",
        "hook": "[First 3 seconds: play the opening hook of the song — no talking]",
        "script": "Music starts immediately. No talking. Text overlay: 'Made this when I needed to feel like myself again.' Let it run 30–45 seconds. Humble caption.",
        "thumbnail_prompt": None, "description": None, "trending_note": "Calm/lifestyle music content outperforms on Saturday afternoons."},
}

# ── Image card generation ──────────────────────────────────────────
def generate_brief_image(sched, content, now_et):
    platform = sched["platform"]
    color    = PLATFORM_COLORS.get(platform, "#4A90E2")
    BG       = "#0D1117"
    CARD     = "#161B22"
    LINE     = "#30363D"
    WHITE    = "#FFFFFF"
    MUTED    = "#8B949E"

    fig = plt.figure(figsize=(12, 7.5), facecolor=BG)
    ax  = fig.add_axes([0.02, 0.03, 0.96, 0.94])
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7.5)
    ax.axis("off")
    ax.set_facecolor(BG)

    # Outer card
    ax.add_patch(patches.FancyBboxPatch(
        (0.15, 0.15), 11.7, 7.2,
        boxstyle="round,pad=0.2",
        lw=1.5, edgecolor=color, facecolor=CARD
    ))

    # Header strip
    ax.add_patch(patches.Rectangle(
        (0.15, 6.55), 11.7, 0.8,
        lw=0, facecolor=color, alpha=0.13
    ))

    # Platform label
    ax.text(0.55, 6.97, f"{sched['emoji']}  {platform.upper()}",
            ha="left", va="center", fontsize=15, fontweight="bold", color=color)

    # Date label
    ax.text(11.65, 6.97,
            f"{sched['day']}  ·  {now_et.strftime('%b %d, %Y')}",
            ha="right", va="center", fontsize=10.5, color=MUTED)

    # Header divider
    ax.plot([0.3, 11.7], [6.5, 6.5], color=color, lw=0.9, alpha=0.4)

    # ── WHAT TO POST (left) ──────────────────────────────────────
    ax.text(0.55, 6.23, "WHAT TO POST",
            ha="left", va="center", fontsize=7, fontweight="bold", color=color)
    what = tw_fill(content.get("what_to_post", ""), width=46)
    what_lines = '\n'.join(what.split('\n')[:2])
    ax.text(0.55, 5.82, what_lines,
            ha="left", va="center", fontsize=11, color=WHITE, linespacing=1.4)

    # ── BEST TIME (right) ────────────────────────────────────────
    ax.text(7.8, 6.23, "BEST TIME",
            ha="left", va="center", fontsize=7, fontweight="bold", color=color)
    ax.text(7.8, 5.82, content.get("best_time", ""),
            ha="left", va="center", fontsize=13, fontweight="bold", color=WHITE)

    ax.plot([0.3, 11.7], [5.2, 5.2], color=LINE, lw=0.7)

    # ── HOOK ─────────────────────────────────────────────────────
    ax.text(0.55, 4.97, "HOOK",
            ha="left", va="center", fontsize=7, fontweight="bold", color=color)
    hook = content.get("hook", "")
    if len(hook) > 130:
        hook = hook[:127] + "..."
    hook_w = '\n'.join(tw_fill(hook, width=85).split('\n')[:2])
    ax.text(0.55, 4.53, f'"{hook_w}"',
            ha="left", va="center", fontsize=11.5, color=WHITE,
            style="italic", linespacing=1.5)

    ax.plot([0.3, 11.7], [3.75, 3.75], color=LINE, lw=0.7)

    # ── WHY IT WORKS (left 55%) ──────────────────────────────────
    ax.text(0.55, 3.52, "WHY IT WORKS",
            ha="left", va="center", fontsize=7, fontweight="bold", color=color)
    why = content.get("why_it_works", "")
    if len(why) > 300:
        why = why[:297] + "..."
    why_w = '\n'.join(tw_fill(why, width=50).split('\n')[:4])
    ax.text(0.55, 2.88, why_w,
            ha="left", va="center", fontsize=9, color=MUTED, linespacing=1.45)

    # Vertical separator
    ax.plot([6.5, 6.5], [0.65, 3.7], color=LINE, lw=0.7)

    # ── TRENDING NOW (right 45%) ─────────────────────────────────
    ax.text(6.75, 3.52, "TRENDING NOW",
            ha="left", va="center", fontsize=7, fontweight="bold", color=color)
    trend = content.get("trending_note", "")
    if len(trend) > 170:
        trend = trend[:167] + "..."
    trend_w = '\n'.join(tw_fill(trend, width=32).split('\n')[:4])
    ax.text(6.75, 2.88, trend_w,
            ha="left", va="center", fontsize=9, color=MUTED, linespacing=1.45)

    # Bottom bar
    ax.plot([0.3, 11.7], [0.62, 0.62], color=color, lw=0.5, alpha=0.3)
    ax.text(6.0, 0.4,
            "Anthony's Content Creator AI  ·  AI-refreshed daily",
            ha="center", va="center", fontsize=7.5, color="#484F58")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=BG, edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.read()

# ── Image upload (commits brief.png to repo, returns raw GitHub URL) ─
def upload_image(img_bytes):
    import subprocess

    with open("brief.png", "wb") as f:
        f.write(img_bytes)

    subprocess.run(["git", "config", "user.email", "actions@github.com"], capture_output=True)
    subprocess.run(["git", "config", "user.name", "GitHub Actions"], capture_output=True)
    subprocess.run(["git", "add", "brief.png"], capture_output=True)

    diff = subprocess.run(["git", "diff", "--staged", "--quiet"])
    if diff.returncode != 0:
        subprocess.run(["git", "commit", "-m", "chore: daily brief image [skip ci]"], capture_output=True)
        subprocess.run(["git", "push"], capture_output=True)

    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if repo and sha:
        return f"https://raw.githubusercontent.com/{repo}/{sha}/brief.png"
    return None

# ── Slack block helpers ────────────────────────────────────────────
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

def build_blocks(sched, content, now_et, refreshed, image_url=None):
    day, emoji, platform = sched["day"], sched["emoji"], sched["platform"]
    date_str   = now_et.strftime("%B %d, %Y")
    refresh_ts = now_et.strftime("%I:%M %p ET") if refreshed else "static fallback"

    blocks = []

    if image_url:
        # Visual card at top — quick glance view
        blocks.append({
            "type": "image",
            "image_url": image_url,
            "alt_text": f"Content brief for {day} — {platform}",
        })
        blocks.append({"type": "divider"})
        # Small label before script
        blocks.append({"type": "section", "text": {"type": "mrkdwn",
            "text": f"*📜 SCRIPT — {platform} ({day})*"}})
    else:
        # Text-only fallback header
        blocks.append({"type": "header", "text": {
            "type": "plain_text",
            "text": f"{emoji} Anthony's Content Brief — {day}, {date_str}",
            "emoji": True,
        }})
        blocks.append({"type": "divider"})
        blocks.append({"type": "section", "fields": [
            {"type": "mrkdwn", "text": f"*📱 Platform*\n{platform}"},
            {"type": "mrkdwn", "text": f"*⏰ Best Time*\n{content['best_time']}"},
        ]})
        blocks.append({"type": "section", "text": {"type": "mrkdwn",
            "text": f"*📝 What to Post*\n{content['what_to_post']}"}})
        if content.get("trending_note"):
            blocks.append({"type": "section", "text": {"type": "mrkdwn",
                "text": f"*📈 Trending*\n_{content['trending_note']}_"}})
        blocks.append({"type": "section", "text": {"type": "mrkdwn",
            "text": f"*🎣 Hook*\n\"{content['hook']}\""}})
        blocks.append({"type": "divider"})
        blocks.append({"type": "section", "text": {"type": "mrkdwn",
            "text": f"*📜 SCRIPT*"}})

    blocks.extend(_chunks(content["script"]))

    if content.get("thumbnail_prompt"):
        blocks.append({"type": "divider"})
        blocks.append({"type": "section", "text": {"type": "mrkdwn",
            "text": f"*🖼️ THUMBNAIL PROMPT*\n{content['thumbnail_prompt']}"}})

    if content.get("description"):
        blocks.append({"type": "divider"})
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "*📄 DESCRIPTION*"}})
        blocks.extend(_chunks(content["description"]))

    blocks.append({"type": "context", "elements": [
        {"type": "mrkdwn", "text": f"🤖 AI-refreshed {refresh_ts}  ·  Content Creator AI Agent"}
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

    # Generate content
    content, refreshed = None, False
    try:
        log("Calling OpenAI API...")
        content   = generate_content(sched, now_et)
        refreshed = True
        log("AI content generated.")
    except Exception as e:
        log(f"AI generation failed — using fallback. Error: {e}")
        content = FALLBACK.get(weekday, {})

    # Generate brief card image and upload
    image_url = None
    try:
        log("Generating brief card image...")
        img_bytes = generate_brief_image(sched, content, now_et)
        log("Uploading image...")
        image_url = upload_image(img_bytes)
        log(f"Image uploaded: {image_url}")
    except Exception as e:
        log(f"Image step failed (sending text-only): {e}")

    # Send to Slack
    try:
        blocks   = build_blocks(sched, content, now_et, refreshed, image_url)
        response = send_slack(blocks)
        log(f"Slack response: {response}")
    except Exception as e:
        log(f"Slack send failed: {e}\n{traceback.format_exc()}")
        sys.exit(1)

    log("=== Daily run complete ===\n")

if __name__ == "__main__":
    main()
