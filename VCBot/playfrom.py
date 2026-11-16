from config import NO_PREVIEW
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from config import bot, call_py, HNDLR, play_filter
from VCBot.queues import QUEUE, add_to_queue
from VCBot.utils import build_stream


@Client.on_message(play_filter & filters.command(["playfrom"], prefixes=HNDLR))
async def playfrom(client, m: Message):
    chat_id = m.chat.id
    if len(m.command) < 2:
        return await m.reply(f"**USAGE:** \n\n`{HNDLR}playfrom [chat_id/username]` \n`{HNDLR}playfrom [chat_id/username] ; [no. of songs]`")
    args = m.text.split(maxsplit=1)[1]
    chat, _, lim = args.partition(";")
    chat = chat.strip()
    limit = int(lim) if lim.strip().isdigit() else 10
    status = await m.reply(f"Searching the last **{limit}** Songs from `{chat}`")
    added = 0
    try:
        async for x in bot.search_messages(chat, limit=limit, filter=enums.MessagesFilter.AUDIO):
            location = await x.download()
            name = x.audio.title or x.audio.file_name or "Audio"
            songname = name[:30] + "..." if len(name) > 30 else name
            if chat_id not in QUEUE:
                await call_py.play(chat_id, build_stream(location, "Audio"))
                await m.reply(f"**Started Playing Songs from {chat} ▶** \n**🎧 SONG** : [{songname}]({x.link}) \n**💬 CHAT** : `{chat_id}`", link_preview_options=NO_PREVIEW)
            add_to_queue(chat_id, songname, location, x.link, "Audio", 0)
            added += 1
        await status.delete()
        await m.reply(f"Added **{added}** SONGS to Queue")
    except Exception as e:
        await status.edit(f"**ERROR** \n`{e}`")
