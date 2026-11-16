from pyrogram import Client, filters
from pyrogram.types import Message
from config import call_py, HNDLR, play_filter
from VCBot.utils import resolve, ResolveError, start_or_queue


@Client.on_message(play_filter & filters.command(["play", "stream"], prefixes=HNDLR))
async def play(client, m: Message):
    """!play <search | link>  or reply to: audio/voice/video, a YouTube or stream link,
    or a t.me message link that points at any of those."""
    status = await m.reply("`Processing...`")
    try:
        songname, source, ref, live = await resolve(client, m, video=False, status=status)
    except ResolveError as e:
        return await status.edit(f"`{e}`")
    except Exception as e:
        return await status.edit(f"**ERROR ⚠️** \n`{e}`")
    await start_or_queue(call_py, status, m.chat.id, songname, source, ref or m.link, "Audio",
                         label="Started Streaming" if live else "Started Playing")
