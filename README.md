# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

The scheduler goes beyond a simple task list with three algorithmic enhancements:

**Sorting**
Tasks are ordered by required-first, then time-slot (morning → afternoon → evening), then descending priority, then ascending duration. Within each tier, tasks are interleaved across pets using round-robin so no single pet monopolises the schedule. A separate `sort_by_time` utility returns any `DailyPlan`'s items in chronological order for display.

**Filtering**
- `filter_by_status(completed)` — returns all (task, pet) pairs matching a completion state, useful for showing pending work or a done list.
- `filter_by_pet(name)` — returns all tasks for a named pet (case-insensitive), regardless of status.
- `get_recurring_tasks()` — returns every daily and weekly task across all pets, making it easy to audit the recurring workload.

**Conflict detection**
`detect_conflicts(plan)` does an O(n²) pass over the scheduled items and returns every overlapping pair. `warn_conflicts(plan)` wraps that result in formatted `"WARNING: ..."` strings ready for printing or UI display. Because `generate_plan` advances the clock after each task, the standard plan is always conflict-free; these methods are most valuable when plans are built or edited manually.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
