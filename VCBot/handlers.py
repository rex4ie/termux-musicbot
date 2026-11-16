from config import NO_PREVIEW
from pytgcalls import filters as fl
from pytgcalls.types import StreamEnded, ChatUpdate
from config import bot, call_py
from VCBot.queues import QUEUE, get_queue, pop_an_item, clear_queue
from VCBot.utils import build_stream


async def skip_current_song(chat_id):
    if chat_id not in QUEUE:
        return 0
    chat_queue = get_queue(chat_id)
    if len(chat_queue) == 1:
        clear_queue(chat_id)
        await call_py.leave_call(chat_id)
        return 1
    try:
        songname, url, link, type, q = chat_queue[1]
        await call_py.play(chat_id, build_stream(url, type, q))
        pop_an_item(chat_id)
        return [songname, link, type]
    except Exception as e:
        print(e)
        clear_queue(chat_id)
        try:
            await call_py.leave_call(chat_id)
        except Exception:
            pass
        return 2


async def skip_item(chat_id, x):
    chat_queue = get_queue(chat_id)
    if not chat_queue or not (0 < x < len(chat_queue)):
        return 0
    return chat_queue.pop(x)[0]


@call_py.on_update(fl.stream_end())
async def on_end_handler(_, update: StreamEnded):
    # Video streams emit an end event for both audio and video; act once.
    if update.stream_type != StreamEnded.Type.AUDIO:
        return
    chat_id = update.chat_id
    op = await skip_current_song(chat_id)
    if op == 1:
        await bot.send_message(chat_id, "`Queue is Empty, Leaving Voice Chat...`")
    elif op == 2:
        await bot.send_message(chat_id, "**Some Error Occurred** \n`Clearing the Queues and Leaving the Voice Chat...`")
    elif op:
        await bot.send_message(chat_id, f"**🎧 Now Playing** \n[{op[0]}]({op[1]}) | `{op[2]}`", link_preview_options=NO_PREVIEW)


@call_py.on_update(fl.chat_update(
    ChatUpdate.Status.CLOSED_VOICE_CHAT | ChatUpdate.Status.KICKED | ChatUpdate.Status.LEFT_GROUP
))
async def close_handler(_, update: ChatUpdate):
    clear_queue(update.chat_id)
