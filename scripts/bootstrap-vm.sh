#!/usr/bin/env bash
# Bootstrap a fresh Ubuntu 24.04 (arm64) VM for ride-pulse development.
# Target: Oracle Cloud Always Free Ampere A1 (4 OCPU / 24 GB), or any Ubuntu box.
#
# Usage (on the VM, as the default 'ubuntu' user):
#   curl -fsSL https://raw.githubusercontent.com/r03922123/ride_sharing/main/scripts/bootstrap-vm.sh | bash
#   # or: git clone the repo first, then: bash scripts/bootstrap-vm.sh
#
# Best-effort: a failed optional step warns and continues.
set -u

REPO_URL="https://github.com/r03922123/ride_sharing.git"
REPO_DIR="$HOME/ride_sharing"

echo "==> apt packages"
sudo apt-get update -y
sudo apt-get install -y --no-install-recommends \
  tmux git build-essential ca-certificates curl gnupg jq unzip \
  || echo "WARN: some apt packages failed"

echo "==> Node.js 20 + Claude Code"
if ! command -v node >/dev/null; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - \
    && sudo apt-get install -y nodejs \
    || echo "WARN: Node install failed"
fi
sudo npm install -g @anthropic-ai/claude-code \
  || echo "WARN: claude-code install failed (retry: sudo npm i -g @anthropic-ai/claude-code)"

echo "==> uv"
if ! command -v uv >/dev/null && [ ! -x "$HOME/.local/bin/uv" ]; then
  curl -LsSf https://astral.sh/uv/install.sh | sh || echo "WARN: uv install failed"
fi
grep -q '.local/bin' "$HOME/.bashrc" || echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"

echo "==> Docker (for the Phase 1 compose stack)"
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sh || echo "WARN: Docker install failed"
  sudo usermod -aG docker "$USER" && echo "NOTE: log out/in (or 'newgrp docker') for docker without sudo"
fi

echo "==> Clone repo"
if [ ! -d "$REPO_DIR/.git" ]; then
  git clone "$REPO_URL" "$REPO_DIR" || echo "WARN: clone failed"
fi

cat <<EOF

  VM bootstrap complete (best-effort).

  Next:
    cd $REPO_DIR
    tmux new -s dev
    claude                 # approve the device code from a phone browser
    # then: "Read docs/superpowers/specs/2026-08-27-...-design.md and begin Phase 0"

  Detach:  Ctrl-b then d       Reattach:  tmux attach -t dev
  Phone:   any SSH app -> host = <public-ip>, user = ubuntu, your private key

  Hardening (recommended, 2 min):
    sudo apt-get install -y fail2ban
    # SSH is already key-only on Oracle images; keep the box updated:
    sudo apt-get upgrade -y

EOF
