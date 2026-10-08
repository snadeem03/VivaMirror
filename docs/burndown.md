# VivaMirror — Burndown (Sprint 1, accelerated student sprint)

- Sprint start (H0): 2026-10-09T00:14:05+05:30 (Asia/Kolkata, IST).
- Unit: estimated minutes remaining over **committed** scope.
- Source of truth: `docs/progress_events.jsonl` (`estimated` + `scope_changed`
  set the totals; `started`/`completed`/`burndown` events move the actual line).
- Rule: scope changes are new events only — initial estimates are never rewritten.

## Re-baseline note (correction M1, ~00:25 IST)

The M0 plan tracked 295 committed minutes against a ~5-hour ideal line.
Correction M1 re-baselined committed scope to **485 min** (US-12/13/14 → P0,
US-17 added, US-03/04 committed, US-09 trimmed, US-15/16 deferred). The old
5-hour ideal line is kept here as history; the active ideal line below runs
over **~8 hours** (485 ÷ 8 ≈ 61 min/hour).

## Hourly checkpoints (ideal vs. actual)

| Checkpoint | Clock (IST) | Ideal remaining | Actual remaining | Note |
|------------|-------------|-----------------|------------------|------|
| H0 start | 00:14 | 485 (re-based; was 295) | 485 | Sprint start; scope correction applied at ~00:25, nothing implemented |
| H1 | 01:14 | 424 | 300 | Behind ideal: 185 of 485 done (US-10, US-06, US-01, US-02, US-05); rebaselined scope is larger than the old 5 h plan by design |
| H2 | 02:14 | 364 | _(fill)_ | |
| H3 | 03:14 | 303 | _(fill)_ | |
| H4 | 04:14 | 242 | _(fill)_ | |
| H5 | 05:14 | 182 | _(fill)_ | Old 5 h mark: under old plan ideal would be 0; rebased plan expects ~182 left |
| H6 | 06:14 | 121 | _(fill)_ | |
| H7 | 07:14 | 61 | _(fill)_ | |
| H8 | 08:14 | 0 | _(fill)_ | Rebased target completion |

## How to record an hour

1. Append to `docs/progress_events.jsonl`:
   `{"timestamp":"<ISO+TZ>","story_id":"SPRINT-1","event":"burndown",
   "estimated_remaining_minutes":<actual>,"note":"H<n> checkpoint: <done>/<scope note>"}`
2. Fill the `Actual remaining` cell for that checkpoint.
3. If scope changed that hour, append `scope_changed` events per story AND note
   it in the checkpoint row — the ideal line does not move; the change is shown
   as a step in the actual line with an explicit note.
