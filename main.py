import asyncio
from pytgcalls import idle
from config import bot, call_py
import VCBot.handlers  # noqa: F401  (registers pytgcalls handlers)


async def main():
    await call_py.start()  # also starts the pyrogram client
    print("UserBot + VC client started")
    await idle()


if __name__ == "__main__":
    # Must reuse the loop PyTgCalls captured when config.py created it;
    # asyncio.run() would start a new loop and break voice-chat calls.
    call_py.loop.run_until_complete(main())
