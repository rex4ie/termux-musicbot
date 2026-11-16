"""Generate a Pyrogram/Kurigram string session for this bot.

Run:  python genstring.py
You'll be asked for your phone number and the login code Telegram sends you.
The SESSION string is printed and (optionally) written into .env.
"""
import asyncio
import os
from dotenv import load_dotenv
from pyrogram import Client

load_dotenv()


async def main():
    api_id = os.getenv("API_ID") or input("API_ID: ").strip()
    api_hash = os.getenv("API_HASH") or input("API_HASH: ").strip()
    async with Client("genstring", api_id=int(api_id), api_hash=api_hash, in_memory=True) as app:
        session = await app.export_session_string()
        me = await app.get_me()
    print(f"\nLogged in as {me.first_name} (id {me.id})")
    print("\nSESSION string (keep it secret, it gives full access to your account):\n")
    print(session)
    if input("\nWrite API_ID/API_HASH/SESSION into .env? [Y/n] ").strip().lower() in ("", "y", "yes"):
        lines = []
        if os.path.exists(".env"):
            with open(".env") as f:
                lines = [l for l in f if not l.startswith(("API_ID=", "API_HASH=", "SESSION="))]
        else:
            lines = ["HNDLR=!\n", "GROUP_MODE=True\n"]
        lines += [f"API_ID={api_id}\n", f"API_HASH={api_hash}\n", f"SESSION={session}\n"]
        with open(".env", "w") as f:
            f.writelines(lines)
        print("Saved to .env")


if __name__ == "__main__":
    asyncio.run(main())
