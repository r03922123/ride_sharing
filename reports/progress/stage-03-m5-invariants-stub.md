# Stage 3 — M5 invariants + mdp stub + CLI
**Status:** done · ruff·mypy·pytest 86 passed, 1 skipped
- `tests/sim/des/test_invariants.py` (conservation, spec §11): rider ≤ 1 terminal
  state (completed XOR cancelled); no cancel after match; per-rider lifecycle
  ordering (Requested < Matched < Pickup < Trip); driver set ⊆ fleet; no driver
  double-booked (match/trip interval depth stays in {0,1}); ≥1 completed trip.
  **These caught two real ordering bugs** → fixed by adding a monotonic `seq`
  column and sorting the event frame by `(ts, seq)` (total causal order).
- `sim/mdp/interface.py` — `MdpSimulator` runtime-checkable Protocol +
  `NotImplementedMdpSimulator` (both methods raise, message cites Phase 6 /
  ADR-0002). `tests/sim/mdp/test_stub.py`.
- `tests/sim/test_des_mdp_consistency.py` — assertion written, `@pytest.mark.skip`
  ("sim.mdp is implemented in Phase 6").
- `sim/des/runner.py` + CLI `ridepulse sim run --config --out` + Makefile `sim:`.

## Real `make sim` (24h Wed, 2500 drivers, nearest_driver r=3km)
requests 102,111 · completed 98,110 · cancel_rate 0.0299 · mean_wait 2.72 min ·
p90_wait 7.43 min · driver_idle 60.9 %. Plausible.

## Next
- M6 ADR + diagram + **self-merge Stage 3 → Phase 0 Done**.
