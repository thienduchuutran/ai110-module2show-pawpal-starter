from datetime import time
from pawpal_system import Owner, Pet, Task, Scheduler

# --- Owner ---
owner = Owner(name="Duc", day_start=time(7, 0), day_end=time(21, 0))

# --- Pets ---
buddy = Pet(name="Buddy", species="dog", age=3, breed="Labrador")
mochi = Pet(name="Mochi", species="cat", age=2)

# --- Tasks for Buddy ---
buddy.add_task(Task(name="Morning Walk",  duration=30, priority=3, category="walk"))
buddy.add_task(Task(name="Feeding",       duration=10, priority=3, category="feeding"))
buddy.add_task(Task(name="Fetch",         duration=20, priority=1, category="enrichment"))

# --- Tasks for Mochi ---
mochi.add_task(Task(name="Feeding",       duration=10, priority=3, category="feeding"))
mochi.add_task(Task(name="Litter Box",    duration=5,  priority=2, category="grooming"))
mochi.add_task(Task(name="Laser Pointer", duration=15, priority=1, category="enrichment"))

# --- Register pets with owner ---
owner.add_pet(buddy)
owner.add_pet(mochi)

# --- Generate plan ---
scheduler = Scheduler(owner)
plan = scheduler.generate_plan()

# --- Print results ---
print("\n========== Today's Schedule ==========")
print(plan.display())
print("\nSummary:", plan.get_summary())
