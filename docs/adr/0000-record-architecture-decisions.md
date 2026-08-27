# 0000. Record architecture decisions

## Status

Accepted

## Context

This project makes non-trivial design decisions package by package (spec §8:
"Class design is a first-class deliverable, not a byproduct"). Decisions and the
alternatives considered need to survive past the PR that made them, so later
stages (and anyone reading the repo as a portfolio piece) can see why a package
looks the way it does without archaeology through commit history.

We need a lightweight, versioned way to record these decisions.

## Decision

We will use Architecture Decision Records (ADRs), one per non-trivial package
decision, stored as numbered Markdown files in `docs/adr/`, following Michael
Nygard's format:

- **Title** — short noun phrase, prefixed with a zero-padded sequence number
  (`NNNN-kebab-case-title.md`).
- **Status** — Proposed / Accepted / Deprecated / Superseded by ADR-NNNN.
- **Context** — the forces at play: technical, business, constraints. Neutral,
  factual.
- **Decision** — the change being proposed, stated in active voice ("We will
  ..."). Include alternatives considered and why they were rejected.
- **Consequences** — the resulting context after applying the decision: good,
  bad, and neutral.

ADRs are immutable once accepted. A decision that changes later gets a *new*
ADR that supersedes the old one (status updated on the old one, not edited in
place) — the record is a log, not a wiki page.

Per spec §8, every non-trivial package PR (`sim`, `agent`, `forecast`,
`serving`, `eval`, `rl`) includes its ADR, and the `sim` ADR additionally
carries a Mermaid class diagram in `docs/lld/`.

## Consequences

- Every package PR has a design-review artifact reviewers can check against the
  self-review question in spec §8 ("can a consumer understand the package
  without reading its internals?").
- Numbering is sequential and never reused, even if an ADR is later superseded.
- Small overhead per PR — one Markdown file — in exchange for a durable design
  record.
