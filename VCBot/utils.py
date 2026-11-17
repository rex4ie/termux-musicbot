from config import NO_PREVIEW
import asyncio
import os
import shutil
import sys
import re
from yt_dlp import YoutubeDL
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality

YT_REGEX = re.compile(r"^(https?://)?(www\.|m\.|music\.)?(youtube\.com|youtu\.be)/.+")
URL_REGEX = re.compile(r"https?://\S+|(?:www\.)?(?:youtube\.com|youtu\.be|t\.me|telegram\.me)/\S+", re.I)
TG_LINK = re.compile(r"(?:https?://)?(?:t|telegram)\.me/(?:(c)/)?([\w\d_]+)/(?:\d+/)?(\d+)", re.I)
AUDIO_FMT = "bestaudio/best"
VIDEO_FMT = "best[height<=?720][width<=?1280]/best"
VIDEO_Q = {720: VideoQuality.HD_720p, 480: VideoQuality.SD_480p, 360: VideoQuality.SD_360p}


def _js_runtimes():
    # yt-dlp needs a modern JS runtime to unlock YouTube formats. Debian's node is
    # too old, so prefer the deno binary installed into the venv by pip.
    rt = {}
    deno = os.path.join(sys.prefix, "bin", "deno")
    if os.path.exists(deno) or shutil.which("deno"):
        rt["deno"] = {"path": deno} if os.path.exists(deno) else {}
    rt["node"] = {}
    return rt


JS_RUNTIMES = _js_runtimes()

# YouTube often withholds muxed (audio+video) formats from the default client.
# These clients still serve muxed HLS streams, so retry with them on failure.
FALLBACK_CLIENTS = (None, ["tv"], ["ios"], ["web_safari"], ["mweb"], ["android"])
FALLBACK_VIDEO_FMT = "best[acodec!=none][vcodec!=none]/best"


def _extract_once(query, fmt, clients):
    opts = {
        "format": fmt,
        "quiet": True,
        "noplaylist": True,
        "js_runtimes": JS_RUNTIMES,
    }
    if clients:
        opts["extractor_args"] = {"youtube": {"player_client": clients}}
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if "entries" in info:
            info = info["entries"][0]
        title = info.get("title") or "Unknown"
        if info.get("is_live"):
            title = "🔴 " + title
        if len(title) > 34:
            title = title[:35] + "..."
        return title, info["url"], info.get("webpage_url") or query


def _extract(query, fmt):
    err = None
    fmts = (fmt, FALLBACK_VIDEO_FMT) if fmt == VIDEO_FMT else (fmt,)
    for clients in FALLBACK_CLIENTS:
        for f in fmts:
            try:
                return _extract_once(query, f, clients)
            except Exception as e:
                # Any client can fail in its own way ("page needs to be reloaded",
                # missing format, PO token...). Keep trying; report the first error.
                err = err or e
    raise err


async def url_info(url, video=False):
    """Resolve any URL yt-dlp understands (YouTube, SoundCloud, m3u8, radio, direct files)."""
    return await asyncio.to_thread(_extract, url, VIDEO_FMT if video else AUDIO_FMT)


async def yt_search(query, video=False):
    """Search YouTube (or resolve a URL). Returns (title, stream_url, page_url) or raises."""
    q = query if YT_REGEX.match(query) else f"ytsearch1:{query}"
    return await asyncio.to_thread(_extract, q, VIDEO_FMT if video else AUDIO_FMT)


def build_stream(source, type, quality=720):
    if type == "Video":
        return MediaStream(
            source,
            audio_parameters=AudioQuality.HIGH,
            video_parameters=VIDEO_Q.get(quality, VideoQuality.HD_720p),
        )
    return MediaStream(
        source,
        audio_parameters=AudioQuality.HIGH,
        video_flags=MediaStream.Flags.IGNORE,
    )


def parse_quality(text):
    try:
        q = int(text)
    except (TypeError, ValueError):
        return None
    return q if q in VIDEO_Q else None


async def start_or_queue(call_py, msg, chat_id, songname, source, ref, type, quality=0, label="Started Playing"):
    """Play immediately if nothing is playing, else append to the queue. `msg` is the status message to edit."""
    from VCBot.queues import QUEUE, add_to_queue
    if chat_id in QUEUE:
        pos = add_to_queue(chat_id, songname, source, ref, type, quality)
        await msg.edit(f"Queued at **#{pos}**")
        return
    try:
        await call_py.play(chat_id, build_stream(source, type, quality or 720))
        add_to_queue(chat_id, songname, source, ref, type, quality)
        await msg.edit(
            f"**{label} {type} ▶** \n**🎧 SONG** : [{songname}]({ref}) \n**💬 CHAT** : `{chat_id}`",
            link_preview_options=NO_PREVIEW,
        )
    except Exception as e:
        await msg.edit(f"`{e}`")


def _short(name, n=35):
    return name[:n] + "..." if len(name) > n else name


def find_url(msg):
    """First URL in a message: hidden text links, then plain-text URLs, then the link preview."""
    if not msg:
        return None
    for ent in (msg.entities or msg.caption_entities or []):
        if getattr(ent, "url", None):
            return ent.url
    text = msg.text or msg.caption or ""
    m = URL_REGEX.search(text)
    if m:
        return m.group(0).rstrip(").,>]")
    wp = getattr(msg, "web_page", None)
    return getattr(wp, "url", None)


def media_of(msg, video):
    if not msg:
        return None
    if video:
        return msg.video or msg.document or msg.animation or msg.video_note
    return msg.audio or msg.voice or msg.video or msg.document


class ResolveError(Exception):
    pass


async def resolve(client, m, video=False, status=None, _depth=0):
    """Work out what to play for a command.

    Order: command argument, else the replied-to message. A Telegram message link is
    followed to the message it points at. Returns (songname, source, ref, is_live).
    """
    arg = m.text.split(None, 1)[1].strip() if m is not None and len(m.command or []) > 1 else ""
    if video and parse_quality(arg) is not None:
        arg = ""  # "!vplay 480" as a reply: argument is only the quality
    target = m.reply_to_message if m is not None else None
    return await _resolve_from(client, arg, target, video, status, 0)


async def _resolve_from(client, text, msg, video, status, depth):
    if depth > 3:
        raise ResolveError("Too many nested message links")

    # 1. Media attached to the message
    if not text and msg is not None:
        media = media_of(msg, video)
        if media:
            if status:
                await status.edit("`Downloading...`")
            path = await msg.download()
            name = getattr(media, "title", None) or getattr(media, "file_name", None)                 or ("Voice Note" if msg.voice else "Video" if video else "Audio")
            return _short(name), path, msg.link, False
        text = find_url(msg) or (msg.text or msg.caption or "").strip()

    if not text:
        raise ResolveError("Reply to an audio/video, a link, or give something to search")

    url = find_url_text(text)

    # 2. Telegram message link -> fetch that message and resolve it
    if url and TG_LINK.search(url):
        private, chat, msg_id = TG_LINK.search(url).groups()
        chat_id = int("-100" + chat) if private else chat
        if status:
            await status.edit("`Fetching linked message...`")
        try:
            linked = await client.get_messages(chat_id, int(msg_id))
        except Exception as e:
            raise ResolveError(f"Can't open that Telegram link: {e}")
        if not linked or linked.empty:
            raise ResolveError("That Telegram message doesn't exist or I can't see it")
        return await _resolve_from(client, "", linked, video, status, depth + 1)

    # 3. Any other URL: YouTube, live streams, radio, m3u8, direct files...
    if url:
        if status:
            await status.edit("`Resolving link...`")
        try:
            title, src, ref = await url_info(url, video)
            return title, src, url, title.startswith("🔴")
        except Exception as e:
            if YT_REGEX.match(url):
                raise ResolveError(f"YTDL ERROR: {e}")
            # yt-dlp doesn't know it; let ffmpeg try the raw stream (e.g. icecast radio)
            return "Stream 📻", url, url, True

    # 4. Plain text -> YouTube search
    if status:
        await status.edit("`Searching...`")
    try:
        title, src, ref = await yt_search(text, video)
    except Exception as e:
        raise ResolveError(f"Found nothing: {e}")
    return title, src, ref, title.startswith("🔴")


def find_url_text(text):
    m = URL_REGEX.search(text or "")
    if not m:
        return None
    u = m.group(0).rstrip(").,>]")
    return u if u.lower().startswith("http") else "https://" + u
