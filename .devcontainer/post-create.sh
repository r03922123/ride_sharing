#!/usr/bin/env bash
# Best-effort provisioning for the ride-pulse dev container.
# Deliberately does NOT use `set -e`: a failed optional step must not fail the
# container build. Every step logs a warning and continues; always exits 0.
set -u

echo "==> Installing uv (Python package/env manager)"
if curl -LsSf https://astral.sh/uv/install.sh | sh; then
  :
else
  echo "WARN: uv install failed — install later with: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi
export PATH="$HOME/.local/bin:$PATH"
grep -q '.local/bin' ~/.bashrc || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

echo "==> Installing Claude Code"
npm install -g @anthropic-ai/claude-code \
  || echo "WARN: claude-code install failed — install later with: npm i -g @anthropic-ai/claude-code"

if [ -f pyproject.toml ]; then
  echo "==> Syncing Python dependencies"
  "$HOME/.local/bin/uv" sync || echo "WARN: uv sync failed — run 'uv sync' after checking pyproject.toml"
fi

cat <<'EOF'

  Dev container ready (best-effort provisioning complete).

  1. Authenticate Claude Code:   claude
  2. Work inside tmux:           tmux new -s dev   (Ctrl-b d to detach)
  3. Stop the Codespace when idle to conserve free hours.

EOF

exit 0
