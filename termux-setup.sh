#!/data/data/com.termux/files/usr/bin/bash
# termux-musicbot installer. On a clean Termux, run:
#   apt update && apt full-upgrade -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold && apt install -y curl && curl -fsSL https://raw.githubusercontent.com/rex4ie/termux-musicbot/main/termux-setup.sh | bash
# Safe to re-run: it updates the code and packages and keeps your .env.
#
# The voice-call engine only ships standard-Linux (glibc) builds, which can't run on
# Android's libc, so the bot runs in a Debian container via proot-distro (no root needed).
set -e
REPO="${REPO:-https://github.com/rex4ie/termux-musicbot}"
APP=/root/termux-musicbot
ROOTFS_HINT="$HOME/.musicbot-env-import"

echo "[1/5] Updating Termux packages..."
apt update && apt full-upgrade -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold   # apt, not pkg: pkg needs curl, which a partial upgrade can break
apt install -y proot-distro

echo "[2/5] Installing Debian container (skipped if present)..."
proot-distro install debian 2>/dev/null || echo "  Debian already installed"

# Bring along a .env from an older zip install, if there is one
ENV_SRC=""
for f in "$HOME/termux-musicbot/.env" "$HOME/TG-MusicPlayer/.env" "$HOME/.env"; do
  [ -f "$f" ] && { ENV_SRC="$f"; break; }
done
mkdir -p "$ROOTFS_HINT"; rm -f "$ROOTFS_HINT/.env"
[ -n "$ENV_SRC" ] && cp "$ENV_SRC" "$ROOTFS_HINT/.env"

echo "[3/5] Installing ffmpeg, Node.js and git..."
echo "[4/5] Downloading the bot and installing Python 3.12 + packages (takes a while)..."
proot-distro login debian --bind "$ROOTFS_HINT:/mnt/envimport" -- bash -c "
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y ffmpeg nodejs git curl ca-certificates
if [ ! -x /root/.local/bin/uv ]; then curl -LsSf https://astral.sh/uv/install.sh | sh; fi
export PATH=/root/.local/bin:\$PATH

if [ -d $APP/.git ]; then
  git -C $APP pull --ff-only
else
  git clone $REPO $APP
fi
cd $APP

# .env: keep the existing one; else import from an old install
if [ ! -f .env ]; then
  for f in /mnt/envimport/.env /root/TG-MusicPlayer/.env; do
    [ -f \$f ] && { cp \$f .env; echo '  Imported your existing .env'; break; }
  done
fi
chmod 600 .env 2>/dev/null || true

uv venv --python 3.12 --allow-existing venv
uv pip install --python venv/bin/python -r requirements.txt
"
rm -rf "$ROOTFS_HINT"

echo "[5/5] Installing the 'musicbot' command..."
cat > "$PREFIX/bin/musicbot" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
APP=/root/termux-musicbot
run() { proot-distro login debian -- bash -c "export PATH=/root/.local/bin:\$PATH; cd $APP && $1"; }
case "$1" in
  ""|start)
    termux-wake-lock 2>/dev/null || true
    run "while true; do ./venv/bin/python main.py; echo 'Bot exited, restarting in 5s... (Ctrl+C twice to stop)'; sleep 5; done" ;;
  update)
    run "git pull --ff-only && uv pip install --python venv/bin/python -r requirements.txt && echo 'Updated. Start with: musicbot'" ;;
  session) run "./venv/bin/python genstring.py" ;;
  env)     run "\${EDITOR:-nano} .env 2>/dev/null || vi .env" ;;
  shell)   proot-distro login debian -- bash -c "cd $APP; exec bash" ;;
  *) echo "usage: musicbot [start|update|session|env|shell]" ;;
esac
SH
chmod +x "$PREFIX/bin/musicbot"

echo
if proot-distro login debian -- test -f "$APP/.env"; then
  echo "Done. Start the bot with:  musicbot"
else
  echo "Done. Log in with 'musicbot session', then start with 'musicbot'."
fi
