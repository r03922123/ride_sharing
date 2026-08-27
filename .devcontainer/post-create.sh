#!/usr/bin/env bash
# Provision the ride-pulse dev environment (runs once, after the container is created).
set -euo pipefail

echo "==> Installing uv (Python package/env manager)"
curl -LsSf https://astral.sh/uv/install.sh | sh
if ! grep -q '.local/bin' ~/.bashrc; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi
export PATH="$HOME/.local/bin:$PATH"

echo "==> Installing Claude Code"
npm install -g @anthropic-ai/claude-code

echo "==> Syncing Python dependencies (if pyproject.toml exists)"
if [ -f pyproject.toml ]; then
  uv sync || echo "uv sync failed (expected before the project is scaffolded) — continuing"
fi

cat <<'EOF'

  Dev container ready.

  1. Authenticate Claude Code:   claude
     (prints a URL + device code — approve it from your phone browser;
      uses your existing subscription, no extra cost)

  2. Work inside tmux so long runs survive disconnects:
       tmux new -s dev
       # ... start `claude` or a training run ...
       # Ctrl-b then d  to detach.  `tmux attach -t dev`  to resume.

  3. Stop the Codespace when idle (Codespaces menu) to conserve free hours —
     the container state is preserved for up to 30 days.

EOF
