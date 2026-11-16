from config import NO_PREVIEW
from pyrogram import Client, filters
from pyrogram.types import Message
from config import call_py, HNDLR, contact_filter
from VCBot.handlers import skip_current_song, skip_item
from VCBot.queues import QUEUE, clear_queue


@Client.on_message(contact_filter & filters.command(["skip"], prefixes=HNDLR))
async def skip(client, m: Message):
    chat_id = m.chat.id
    if len(m.command) < 2:
        op = await skip_current_song(chat_id)
        if op == 0:
            await m.reply("`Nothing Is Playing`")
        elif op == 1:
            await m.reply("`Queue is Empty, Leaving Voice Chat...`")
        elif op == 2:
            await m.reply("**Some Error Occurred** \n`Clearing the Queues and Leaving the Voice Chat...`")
        else:
            await m.reply(f"**Skipped ⏭** \n**🎧 Now Playing** - [{op[0]}]({op[1]}) | `{op[2]}`", link_preview_options=NO_PREVIEW)
        return
    if chat_id not in QUEUE:
        return await m.reply("`Nothing is Streaming`")
    out = "**Removed the following songs from Queue:-**"
    for x in sorted({int(a) for a in m.command[1:] if a.isdigit()}, reverse=True):
        name = await skip_item(chat_id, x)
        if name:
            out += f"\n**#{x}** - {name}"
    await m.reply(out)


async def _simple(m, action, ok_text):
    if m.chat.id not in QUEUE:
        return await m.reply("`Nothing is Streaming`")
    try:
        await action(m.chat.id)
        await m.reply(ok_text)
    except Exception as e:
        await m.reply(f"**ERROR** \n`{e}`")


@Client.on_message(contact_filter & filters.command(["end", "stop"], prefixes=HNDLR))
async def stop(client, m: Message):
    async def _stop(chat_id):
        clear_queue(chat_id)
        await call_py.leave_call(chat_id)
    await _simple(m, _stop, "**Stopped Streaming ⏹️**")


@Client.on_message(contact_filter & filters.command(["pause"], prefixes=HNDLR))
async def pause(client, m: Message):
    await _simple(m, call_py.pause, "**Paused Streaming ⏸️**")


@Client.on_message(contact_filter & filters.command(["resume"], prefixes=HNDLR))
async def resume(client, m: Message):
    await _simple(m, call_py.resume, "**Resumed Streaming ▶**")
