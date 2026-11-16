import os
from dotenv import load_dotenv
from pyrogram import Client, filters
from pytgcalls import PyTgCalls

load_dotenv()

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION = os.environ["SESSION"]
HNDLR = os.getenv("HNDLR", "!")
GRPPLAY = os.getenv("GROUP_MODE", "True").strip().lower() == "true"

contact_filter = filters.create(
    lambda _, __, m: bool((m.from_user and m.from_user.is_contact) or m.outgoing)
)
# Anyone in group mode, otherwise contacts/self only
play_filter = filters.create(lambda _, __, m: GRPPLAY) | contact_filter

bot = Client(
    "musicplayer",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION,
    plugins=dict(root="VCBot"),
    in_memory=True,
)
call_py = PyTgCalls(bot)

from pyrogram.types import LinkPreviewOptions
NO_PREVIEW = LinkPreviewOptions(is_disabled=True)
