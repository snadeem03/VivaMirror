"""Reproducible burndown chart for Sprint 1 (US-17).

Reads docs/progress_events.jsonl and derives remaining estimated minutes
from real events only: sprint_planned sets the first total, scope_changed
events adjust per-story estimates, sprint_replanned re-baselines the total,
and each completed event deducts that story's current estimate exactly once.
Hourly burndown checkpoints are plotted as markers.

No interpolation, no fictional observations, no future checkpoints. Run:

    .\\.venv\\Scripts\\python.exe scripts/make_burndown.py

Outputs docs/burndown.csv (step table) and docs/burndown.png (chart).
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVENTS = ROOT / "docs" / "progress_events.jsonl"
CSV_OUT = ROOT / "docs" / "burndown.csv"
PNG_OUT = ROOT / "docs" / "burndown.png"

SPRINT_START = datetime.fromisoformat("2026-10-09T00:14:05+05:30")

# Ideal baselines (elapsed hours, remaining minutes), labeled on the chart.
IDEAL_ORIGINAL = [(0.0, 295.0), (5.0, 0.0)]  # M0 plan, kept as history
IDEAL_REVISED = [(0.0, 485.0), (8.0, 0.0)]  # correction M1 re-baseline


def _elapsed_hours(timestamp: str) -> float:
    moment = datetime.fromisoformat(timestamp)
    return (moment - SPRINT_START).total_seconds() / 3600.0


def build_steps() -> tuple[list[tuple[float, float, str]], float]:
    """Return ([(elapsed_h, remaining, note)], final_remaining).

    Totals move only on sprint_planned / sprint_replanned / completed
    events. scope_changed events are annotations (their estimates feed the
    per-story map used at completion); this avoids double-counting, since
    the M0 estimates mixed committed and stretch scope while the replan
    value is authoritative. Each completed story deducts once.
    """
    estimates: dict[str, float] = {}
    completed: set[str] = set()
    total: float | None = None
    steps: list[tuple[float, float, str]] = []
    for line in EVENTS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        kind, story = event["event"], event["story_id"]
        hours = _elapsed_hours(event["timestamp"])
        if kind == "sprint_planned":
            total = float(event["estimated_remaining_minutes"])
            steps.append((0.0, total, "sprint start (M0 plan: 295)"))
        elif kind in ("estimated", "scope_changed") and story.startswith("US-"):
            estimates[story] = float(event["estimated_remaining_minutes"])
            if kind == "scope_changed":
                steps.append((hours, total if total is not None else 0.0,
                              f"scope: {story} -> "
                              f"{event['estimated_remaining_minutes']}"))
        elif kind == "sprint_replanned":
            total = float(event["estimated_remaining_minutes"])
            steps.append((hours, total, "correction M1 re-baseline: 485"))
        elif kind == "completed" and story.startswith("US-"):
            if story not in completed:
                if story not in estimates:
                    raise ValueError(f"completed {story} has no estimate")
                completed.add(story)
                total -= estimates[story]
                steps.append((hours, total, f"done: {story}"))
        elif kind == "burndown":
            steps.append((hours, float(event["estimated_remaining_minutes"]),
                          "hourly checkpoint"))
    assert total is not None, "no sprint totals found in events"
    return steps, total


def write_csv(steps: list[tuple[float, float, str]]) -> None:
    with CSV_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["elapsed_hours", "actual_remaining_min", "note"])
        for hours, remaining, note in steps:
            writer.writerow([f"{hours:.3f}", f"{remaining:g}", note])


def write_png(steps: list[tuple[float, float, str]]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    xs = [s[0] for s in steps]
    ys = [s[1] for s in steps]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.step(xs, ys, where="post", linewidth=2, label="actual remaining")
    ax.plot([s[0] for s in steps], [s[1] for s in steps], "o", markersize=4)
    ox, oy = zip(*IDEAL_ORIGINAL)
    rx, ry = zip(*IDEAL_REVISED)
    ax.plot(ox, oy, "--", linewidth=1, label="ideal (M0 plan: 295/5h)")
    ax.plot(rx, ry, "-.", linewidth=1, label="ideal (revised: 485/8h)")
    for hours, remaining, note in steps:
        # Scope promotions are listed in the CSV; labeling all of them would
        # bury the chart (they share one timestamp), so only structural
        # points get text.
        if note.startswith(("sprint", "correction", "done:", "hourly")):
            ax.annotate(
                note, (hours, remaining), fontsize=7,
                xytext=(4, 6), textcoords="offset points",
            )
    ax.set_xlabel("elapsed hours from sprint start (H0 00:14 IST)")
    ax.set_ylabel("remaining estimated minutes")
    ax.set_title("VivaMirror Sprint 1 burndown (event-based, no interpolation)")
    ax.legend(fontsize=8)
    ax.grid(True, linestyle=":", alpha=0.6)
    fig.tight_layout()
    fig.savefig(PNG_OUT, dpi=120)
    plt.close(fig)


def main() -> None:
    steps, final_total = build_steps()
    write_csv(steps)
    write_png(steps)
    print(f"steps: {len(steps)}, final remaining: {final_total:g} min")
    print(f"wrote {CSV_OUT.name} and {PNG_OUT.name}")


if __name__ == "__main__":
    main()
