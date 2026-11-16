import os
import sys
from time import time
from datetime import datetime, timezone
from pyrogram import Client, filters
from pyrogram.types import Message
from config import HNDLR, contact_filter, GRPPLAY

START_TIME = datetime.now(timezone.utc)
UNITS = (("Week", 604800), ("Day", 86400), ("Hour", 3600), ("Min", 60), ("Sec", 1))


def human_time(seconds):
    parts = []
    for unit, div in UNITS:
        amount, seconds = divmod(int(seconds), div)
        if amount:
            parts.append(f"{amount} {unit}{'' if amount == 1 else 's'}")
    return ", ".join(parts) or "0 Secs"


@Client.on_message(contact_filter & filters.command(["ping"], prefixes=HNDLR))
async def ping(client, m: Message):
    start = time()
    r = await m.reply_text("`...`")
    delta = (time() - start) * 1000
    uptime = human_time((datetime.now(timezone.utc) - START_TIME).total_seconds())
    mode = "Enabled" if GRPPLAY else "Disabled"
    await r.edit(f"`{delta:.3f} ms` \n**Uptime ⏳** - `{uptime}` \n**Group Mode** - `{mode}`")


@Client.on_message(contact_filter & filters.command(["restart"], prefixes=HNDLR))
async def restart(client, m: Message):
    await m.reply("`Restarting...`")
    os.execl(sys.executable, sys.executable, *sys.argv)


@Client.on_message(contact_filter & filters.command(["help"], prefixes=HNDLR))
async def help(client, m: Message):
    h = HNDLR
    await m.reply(
        f"**HELP MENU 🛠** \n\n__USER COMMANDS__ (Anyone can Use if `GROUP_MODE` is `True`): \n"
        f"`{h}play` \n`{h}vplay` \n`{h}stream` (For Radio links) \n`{h}vstream` (For .m3u8 / live links) \n"
        f"`{h}playfrom [channel] ; [n]` - Plays last n songs from channel \n`{h}playlist` / `{h}queue` \n\n"
        f"__SUDO COMMANDS__ (You and Your Contacts): \n`{h}ping` \n`{h}skip` \n`{h}pause` and `{h}resume` \n"
        f"`{h}stop` / `{h}end` \n`{h}help` \n`{h}restart` \n`{h}repo`"
    )


@Client.on_message(contact_filter & filters.command(["repo", "source"], prefixes=HNDLR))
async def source(client, m: Message):
    await m.reply("Find us at: [rex4ie/termux-musicbot](https://github.com/rex4ie/termux-musicbot)")
