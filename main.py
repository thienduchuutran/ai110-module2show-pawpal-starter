from datetime import time
from pawpal_system import Owner, Pet, Task, Scheduler, DailyPlan, ScheduledTask

# --- Owner ---
owner = Owner(
    name="Duc",
    day_start=time(7, 0),
    day_end=time(21, 0),
    break_duration=10,  # 10-min buffer between tasks
    energy_budget=8,    # max total effort points for the day
)

# --- Pets ---
buddy = Pet(name="Buddy", species="dog", age=3, breed="Labrador")
mochi = Pet(name="Mochi", species="cat", age=2)

# --- Tasks for Buddy (added out of order: low priority first) ---
buddy.add_task(Task(
    name="Fetch", duration=20, priority=1, category="enrichment",
    effort=1, min_duration=10,
))
buddy.add_task(Task(
    name="Evening Walk", duration=25, priority=2, category="walk",
    preferred_time="evening", effort=2,
))
buddy.add_task(Task(
    name="Feeding", duration=10, priority=3, category="feeding",
    required=True, effort=1,
))
buddy.add_task(Task(
    name="Morning Walk", duration=30, priority=3, category="walk",
    required=True, effort=2,
))

# --- Tasks for Mochi (added out of order: low priority first) ---
mochi.add_task(Task(
    name="Laser Pointer", duration=15, priority=1, category="enrichment",
    effort=1,
))
mochi.add_task(Task(
    name="Litter Box", duration=5, priority=2, category="grooming",
    required=True, effort=1, frequency="weekly", scheduled_day="monday",
))
mochi.add_task(Task(
    name="Feeding", duration=10, priority=3, category="feeding",
    required=True, effort=1,
))

# --- Register pets with owner ---
owner.add_pet(buddy)
owner.add_pet(mochi)

# --- Scheduler ---
scheduler = Scheduler(owner)

# --- Generate plan ---
plan = scheduler.generate_plan()

# -----------------------------------------------------------------------
# sort_by_time
# -----------------------------------------------------------------------
print("\n========== Scheduled Tasks (sorted by start time) ==========")
for item in scheduler.sort_by_time(plan.scheduled_items):
    print(
        f"  {item.start_time.strftime('%H:%M')} - {item.end_time().strftime('%H:%M')}"
        f"  [{item.pet.name}] {item.task.name}  (P{item.task.priority})"
    )

# -----------------------------------------------------------------------
# filter_by_status
# -----------------------------------------------------------------------
print("\n========== Pending tasks (filter_by_status completed=False) ==========")
for task, pet in scheduler.filter_by_status(completed=False):
    print(f"  [{pet.name}] {task.name}  completed={task.completed}")

# Mark one task complete to show the completed filter
buddy.tasks[2].mark_complete()  # "Feeding" for Buddy
print("\n  (Marked Buddy's 'Feeding' as complete)")

print("\n  Completed tasks now:")
for task, pet in scheduler.filter_by_status(completed=True):
    print(f"  [{pet.name}] {task.name}  completed={task.completed}")

# -----------------------------------------------------------------------
# filter_by_pet
# -----------------------------------------------------------------------
print("\n========== Tasks for Buddy only (filter_by_pet) ==========")
for task in scheduler.filter_by_pet("Buddy"):
    status = "done" if task.completed else "pending"
    print(f"  {task.name}  priority={task.priority}  [{status}]")

print("\n========== Tasks for Mochi only (filter_by_pet) ==========")
for task in scheduler.filter_by_pet("Mochi"):
    status = "done" if task.completed else "pending"
    print(f"  {task.name}  priority={task.priority}  [{status}]")

# -----------------------------------------------------------------------
# get_recurring_tasks
# -----------------------------------------------------------------------
print("\n========== Recurring tasks (daily / weekly) ==========")
for task, pet in scheduler.get_recurring_tasks():
    print(f"  [{pet.name}] {task.name}  frequency={task.frequency}")

# -----------------------------------------------------------------------
# detect_conflicts
# -----------------------------------------------------------------------
conflicts = scheduler.detect_conflicts(plan)
print(f"\n========== Conflict detection: {len(conflicts)} conflict(s) ==========")
if conflicts:
    for a, b in conflicts:
        print(
            f"  CONFLICT: [{a.pet.name}] {a.task.name} "
            f"({a.start_time.strftime('%H:%M')}-{a.end_time().strftime('%H:%M')})"
            f"  vs  [{b.pet.name}] {b.task.name} "
            f"({b.start_time.strftime('%H:%M')}-{b.end_time().strftime('%H:%M')})"
        )
else:
    print("  No conflicts detected.")

# -----------------------------------------------------------------------
# warn_conflicts — lightweight warning demo with manually-overlapping tasks
#
# generate_plan() naturally avoids overlaps by advancing current_dt after
# each task, so we build a DailyPlan by hand to force two tasks that share
# the same time window and verify warn_conflicts catches them.
# -----------------------------------------------------------------------
conflict_plan = DailyPlan(owner=owner)
conflict_plan.scheduled_items = [
    ScheduledTask(
        task=Task(name="Morning Walk", duration=30, priority=3, category="walk"),
        pet=buddy,
        start_time=time(8, 0),          # 08:00 – 08:30
    ),
    ScheduledTask(
        task=Task(name="Feeding", duration=20, priority=3, category="feeding"),
        pet=mochi,
        start_time=time(8, 15),         # 08:15 – 08:35  ← overlaps above
    ),
    ScheduledTask(
        task=Task(name="Evening Walk", duration=25, priority=2, category="walk"),
        pet=buddy,
        start_time=time(18, 0),         # 18:00 – 18:25  ← no overlap
    ),
]

print("\n========== warn_conflicts (overlapping demo) ==========")
warnings = scheduler.warn_conflicts(conflict_plan)
if warnings:
    for w in warnings:
        print(" ", w)
else:
    print("  No conflicts detected.")

# -----------------------------------------------------------------------
# Full plan display
# -----------------------------------------------------------------------
print("\n========== Full Daily Plan ==========")
print(plan.display())
print("\nSummary:", plan.get_summary())
