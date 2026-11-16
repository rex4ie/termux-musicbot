from pyrogram import Client, filters
from pyrogram.types import Message
from config import call_py, HNDLR, play_filter
from VCBot.utils import resolve, ResolveError, start_or_queue, parse_quality


@Client.on_message(play_filter & filters.command(["vplay", "vstream"], prefixes=HNDLR))
async def vplay(client, m: Message):
    """!vplay <search | link> [720|480|360]  or reply to a video / link / t.me message link."""
    Q = 720
    # Optional trailing quality: "!vplay <link> 480" or "!vplay 480" as a reply
    if len(m.command) >= 2 and parse_quality(m.command[-1]) is not None:
        Q = parse_quality(m.command[-1])
        m.command = m.command[:-1]
        m.text = m.text.rsplit(None, 1)[0]
    status = await m.reply("`Processing...`")
    try:
        songname, source, ref, live = await resolve(client, m, video=True, status=status)
    except ResolveError as e:
        return await status.edit(f"`{e}`")
    except Exception as e:
        return await status.edit(f"**ERROR ⚠️** \n`{e}`")
    await start_or_queue(call_py, status, m.chat.id, songname, source, ref or m.link, "Video", Q,
                         label="Started Streaming" if live else "Started Playing")
