# ride-pulse

Phased ML portfolio project: **ride-sharing demand intelligence** on NYC TLC open
data. Serves forecasting / ETA models behind APIs, exposes them to an LLM
ops-assistant agent, and includes rigorous evaluation studies (simulated online
experiment, agent benchmark, off-policy evaluation of an RL repositioning policy).

**Status:** design phase — implementation not started.

**Design spec:**
[`docs/superpowers/specs/2026-08-27-ride-sharing-ml-portfolio-design.md`](docs/superpowers/specs/2026-08-27-ride-sharing-ml-portfolio-design.md)

## Development (remote, laptop-optional)

The repo ships a devcontainer that provisions Python 3.11, `uv`, Docker, Node,
and Claude Code.

1. **GitHub → Code ▸ Codespaces ▸ Create codespace on main.**
2. When the container is ready, authenticate the agent:

   ```
   claude
   ```

   It prints a URL and device code — approve from a phone browser. Uses your
   existing subscription; no extra cost.
3. Run work inside `tmux` so it survives disconnects:

   ```
   tmux new -s dev
   # start `claude` or a training run
   # Ctrl-b then d to detach; `tmux attach -t dev` to resume
   ```
4. Stop the Codespace when idle to conserve free hours; state persists ~30 days.

For long unattended runs (large backtest sweeps, Phase 6 DQN training), an
Oracle Cloud Always Free Ampere A1 VM (4 cores / 24 GB, always on) running the
same steps under `tmux` is the fallback. See spec §17.
