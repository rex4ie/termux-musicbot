from config import NO_PREVIEW
from pyrogram import Client, filters
from pyrogram.types import Message
from config import HNDLR, play_filter
from VCBot.queues import QUEUE, get_queue


@Client.on_message(play_filter & filters.command(["playlist", "queue"], prefixes=HNDLR))
async def playlist(client, m: Message):
    if m.chat.id not in QUEUE:
        return await m.reply("`Nothing is Streaming`")
    q = get_queue(m.chat.id)
    text = f"**🎧 NOW PLAYING:** \n[{q[0][0]}]({q[0][2]}) | `{q[0][3]}`"
    if len(q) > 1:
        text += " \n\n**⏯ PLAYLIST:**"
        for i, item in enumerate(q[1:], 1):
            text += f"\n**#{i}** - [{item[0]}]({item[2]}) | `{item[3]}`"
    await m.reply(text, link_preview_options=NO_PREVIEW)
