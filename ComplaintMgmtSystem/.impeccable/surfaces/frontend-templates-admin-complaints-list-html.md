---
version: 1
slug: "frontend-templates-admin-complaints-list-html"
primary_target: "frontend/templates/admin/complaints_list.html"
related_targets: ["frontend/templates/admin/complaint_detail.html"]
---

# Surface brief: admin queue + detail (Operate, code-led)

Scope: `admin/complaints_list.html` (the ranked queue), `admin/complaint_detail.html`
(WHY + quick actions), `admin/dashboard.html` (remove duplicate Recent table),
backend `admin_complaints` sort + `admin_confirm_label` sets validated.
Job: work the queue top-down — worst first, open, act, next.
Constraints: keep filters, pagination, exports, comments, assignment,
status, resend-mail. No new routes. Register pills for priority.

## Direction contract

THESIS: The queue is ranked, not listed — worst first by default, rank
numerals, WHY-line under every subject, one shared pill system. The
dashboard stops duplicating the table and points at the queue.

OWN-WORLD: Register pills (tint + icon + uppercase label) inside the
existing admin console chrome. Rank numerals in tabular figures. No new
visual language here — the console stays operational, pills carry the
Register voice.

STORY: An admin opens the queue, sees rank 01 with its reason, opens
the case, reads WHY (score + reason + sentiment), assigns or resolves,
verifies once for training. No second table to cross-check.

FIRST VIEWPORT: Ranked rows with numerals, pills, WHY-lines; filters
intact above. Detail: WHY block prominent, quick actions unchanged,
single verify that also marks validated.

FORM: User-pinned Direction A (roll skipped). Ranked ledger table.

FINISH: unreviewed and undocumented is unfinished; this build ends with
the finish review, the verdict, DESIGN.md, and every shipping raster
carrying its provenance
