# DESIGN.md — Complainify visual system

World: **The Register**. A university ledger that happens to be software.
Paper ground, ink text, hairline rules, one oxblood accent. Trust through
order. Applies to: landing, submit, tracker. The admin console keeps its
operational chrome; Register speaks through shared pills, ranks, and type.

## Tokens

| Role | Light | Dark (`[data-theme="dark"]`) |
|---|---|---|
| Ground | `--reg-paper` `#FAF6EF` (see `.sit`) | `#0A1322` |
| Card | `#FFFDF8` | `#0C1729` |
| Ink | `#0F2A43` | `#F2EFE6` / `#EAF1FB` |
| Muted | `#51606F` | `#9FB2C8` |
| Hairline | `#E4DCC8` | `#1E2C45` |
| Accent (actions, critical flags only) | oxblood `#8C2F1B` | `#A63E24` / links `#D08A63` |

Shadows carry offset + blur, tinted to ink — never flat black, never
hard-offset blocks. No gradients except the legacy brand button (being
phased out in favor of flat oxblood). No glass outside true overlays.

## Type

- Display/ranks: **Bitter** (slab, ledger record character), tight
  tracking, `text-wrap: balance` on headings.
- UI/body: **Inter**. Ticket IDs/numbers: system mono + tabular figures.
- Lead paragraphs capped at ~44ch.

## Priority pills (shared everywhere)

Pill = tinted bg + 1px tint border + icon + uppercase label. Never color
alone. `.pr-pill--critical/high/medium/low` in `complainify.css`.
Critical red is reserved for critical — nothing decorative uses red.

## Rules for future edits

1. Queue-first: worst-first ordering, rank numerals, WHY-line under the
   subject, pills everywhere a priority appears.
2. No kickers/eyebrows above headings; no gradient text; no invented
   stats — wire live data or show an honest empty/unavailable state.
3. Every dynamic JS insertion must be escaped (`escapeHtml` pattern).
4. Light and dark ship together: any new Register style gets both variants.
5. Dead links are removed, never left pointing at `#`.
