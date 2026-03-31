from __future__ import annotations
from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    name: str
    duration: int               # minutes (maximum; or fixed when min_duration == 0)
    priority: int               # 1 = low, 2 = medium, 3 = high
    category: str = ""          # walk / feeding / meds / grooming / enrichment
    frequency: str = "daily"    # daily / weekly / as_needed
    scheduled_day: str = ""     # for weekly tasks: "monday".."sunday"; empty = skip
    preferred_time: str = "any" # morning / afternoon / evening / any
    min_duration: int = 0       # 0 = fixed duration; >0 = can shrink to this minimum
    required: bool = False      # guaranteed placement before optional tasks
    effort: int = 1             # 1 (light) to 3 (heavy); counts toward owner energy budget
    notes: str = ""
    completed: bool = False
    due_date: date | None = None  # None = no date constraint (always applicable)

    def is_valid(self) -> bool:
        """Return True if duration is positive and priority is 1–3."""
        return self.duration > 0 and self.priority in (1, 2, 3)

    def mark_complete(self) -> "Task | None":
        """Mark this task as completed.

        For recurring tasks, returns a new Task instance for the next occurrence:
          - daily  → due_date = today + 1 day
          - weekly → due_date = today + 7 days
        Returns None for as_needed tasks (no automatic next occurrence).
        """
        self.completed = True
        if self.frequency == "daily":
            return replace(self, completed=False, due_date=date.today() + timedelta(days=1))
        if self.frequency == "weekly":
            return replace(self, completed=False, due_date=date.today() + timedelta(weeks=1))
        return None

    def reset(self) -> None:
        """Reset the task to incomplete so it can be rescheduled."""
        self.completed = False

    def to_dict(self) -> dict:
        """Serialize the task to a plain dictionary."""
        return {
            "name": self.name,
            "duration": self.duration,
            "priority": self.priority,
            "category": self.category,
            "frequency": self.frequency,
            "scheduled_day": self.scheduled_day,
            "preferred_time": self.preferred_time,
            "min_duration": self.min_duration,
            "required": self.required,
            "effort": self.effort,
            "notes": self.notes,
            "completed": self.completed,
            "due_date": self.due_date.isoformat() if self.due_date else None,
        }


# ---------------------------------------------------------------------------
# Pet  (owns a list of Tasks)
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str
    age: int
    breed: str = ""
    special_needs: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    # Default starter tasks keyed by species
    _DEFAULTS: dict[str, list[tuple]] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        """Populate the species-to-default-tasks lookup after dataclass init."""
        self._DEFAULTS = {
            "dog": [
                ("Morning Walk",  30, 3, "walk"),
                ("Feeding",       10, 3, "feeding"),
                ("Evening Walk",  20, 2, "walk"),
                ("Playtime",      15, 1, "enrichment"),
            ],
            "cat": [
                ("Feeding",       10, 3, "feeding"),
                ("Litter Box",     5, 2, "grooming"),
                ("Playtime",      15, 1, "enrichment"),
            ],
        }

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's list."""
        self.tasks.append(task)

    def remove_task(self, name: str) -> None:
        """Remove a task by name (removes first match)."""
        self.tasks = [t for t in self.tasks if t.name != name]

    def get_pending_tasks(self) -> list[Task]:
        """Return only tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]

    def get_default_tasks(self) -> list[Task]:
        """Return a fresh list of common tasks for this pet's species."""
        return [
            Task(name, duration, priority, category)
            for name, duration, priority, category
            in self._DEFAULTS.get(self.species.lower(), [])
        ]

    def load_default_tasks(self) -> None:
        """Populate this pet's task list with species defaults (only if empty)."""
        if not self.tasks:
            self.tasks = self.get_default_tasks()


# ---------------------------------------------------------------------------
# Owner  (manages multiple Pets)
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    name: str
    day_start: time = time(8, 0)
    day_end: time = time(20, 0)
    break_duration: int = 5      # minutes of buffer inserted between consecutive tasks
    energy_budget: int = 0       # max total effort points across all tasks; 0 = no cap
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> None:
        """Remove a pet by name (removes first match)."""
        self.pets = [p for p in self.pets if p.name != name]

    def get_available_time(self) -> int:
        """Derive total available minutes from day_start and day_end."""
        start_dt = datetime.combine(date.today(), self.day_start)
        end_dt = datetime.combine(date.today(), self.day_end)
        return int((end_dt - start_dt).total_seconds() // 60)

    def get_all_tasks(self) -> list[Task]:
        """Collect every task across all pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_all_pending_tasks(self) -> list[Task]:
        """Collect only incomplete tasks across all pets."""
        return [task for pet in self.pets for task in pet.get_pending_tasks()]

    def update_preferences(self, **kwargs) -> None:
        """Merge keyword arguments into the preferences dict."""
        self.preferences.update(kwargs)


# ---------------------------------------------------------------------------
# ScheduledTask  (a Task placed at a specific time)
# ---------------------------------------------------------------------------

@dataclass
class ScheduledTask:
    task: Task
    pet: Pet
    start_time: time
    actual_duration: int = 0  # set by Scheduler; may be < task.duration when shrunk to fit

    def __post_init__(self) -> None:
        if self.actual_duration == 0:
            self.actual_duration = self.task.duration

    def end_time(self) -> time:
        """Compute end time from actual_duration (which may differ from task.duration)."""
        start_dt = datetime.combine(date.today(), self.start_time)
        return (start_dt + timedelta(minutes=self.actual_duration)).time()

    def conflicts_with(self, other: ScheduledTask) -> bool:
        """Return True if this slot overlaps with another ScheduledTask."""
        return self.start_time < other.end_time() and other.start_time < self.end_time()


# ---------------------------------------------------------------------------
# DailyPlan  (the output produced by Scheduler)
# ---------------------------------------------------------------------------

@dataclass
class DailyPlan:
    owner: Owner
    scheduled_items: list[ScheduledTask] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    reasoning: str = ""

    @property
    def total_duration(self) -> int:
        """Sum of actual scheduled durations (respects shrinkage)."""
        return sum(item.actual_duration for item in self.scheduled_items)

    def is_feasible(self) -> bool:
        """Return True if every scheduled item fits inside the owner's day window."""
        if not self.scheduled_items:
            return True
        first_start = min(item.start_time for item in self.scheduled_items)
        last_end = max(item.end_time() for item in self.scheduled_items)
        return first_start >= self.owner.day_start and last_end <= self.owner.day_end

    def display(self) -> str:
        """Return a human-readable schedule string."""
        if not self.scheduled_items:
            return "No tasks scheduled."
        lines = ["Daily Plan", "=" * 42]
        for item in sorted(self.scheduled_items, key=lambda x: x.start_time):
            shrunk = (
                f" [shrunk to {item.actual_duration}min]"
                if item.actual_duration < item.task.duration
                else ""
            )
            lines.append(
                f"  {item.start_time.strftime('%H:%M')} - {item.end_time().strftime('%H:%M')}"
                f"  [{item.pet.name}] {item.task.name}"
                f"  (P{item.task.priority}){shrunk}"
            )
        lines.append(f"\nTime used : {self.total_duration} min")
        if self.skipped_tasks:
            lines.append("Skipped   : " + ", ".join(t.name for t in self.skipped_tasks))
        if self.reasoning:
            lines.append(f"\n{self.reasoning}")
        return "\n".join(lines)

    def get_summary(self) -> str:
        """One-line summary of the plan."""
        return (
            f"{len(self.scheduled_items)} task(s) scheduled, "
            f"{self.total_duration} min used, "
            f"{len(self.skipped_tasks)} skipped"
        )


# ---------------------------------------------------------------------------
# Scheduler  (the brain — reads from Owner, produces DailyPlan)
# ---------------------------------------------------------------------------

class Scheduler:
    # Clock windows that define each time-of-day slot.
    # Clipped to the owner's day_start/day_end at runtime.
    _SLOT_WINDOWS: dict[str, tuple[time, time]] = {
        "morning":   (time(5, 0),  time(12, 0)),
        "afternoon": (time(12, 0), time(17, 0)),
        "evening":   (time(17, 0), time(22, 0)),
    }

    # Lower number = scheduled earlier in the day.
    _SLOT_ORDER: dict[str, int] = {
        "morning": 0, "afternoon": 1, "evening": 2, "any": 3,
    }

    # Sensible slot defaults inferred from task category when preferred_time == "any".
    _CATEGORY_SLOT_DEFAULTS: dict[str, str] = {
        "feeding":    "morning",
        "walk":       "morning",
        "meds":       "morning",
        "grooming":   "afternoon",
        "enrichment": "afternoon",
    }

    def __init__(self, owner: Owner) -> None:
        """Bind the scheduler to the given owner and their pets."""
        self.owner = owner

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def _is_scheduled_today(self, task: Task) -> bool:
        """Return True if the task should run today based on its frequency."""
        if task.frequency == "daily":
            # due_date=None means always applicable (legacy tasks); otherwise must be due by today
            return task.due_date is None or task.due_date <= date.today()
        if task.frequency == "as_needed":
            return False
        if task.frequency == "weekly":
            if not task.scheduled_day:
                return False
            return date.today().strftime("%A").lower() == task.scheduled_day.lower()
        return True

    def _filter_for_today(self) -> list[tuple[Task, Pet]]:
        """Return all valid, pending, today-applicable (task, pet) pairs."""
        return [
            (task, pet)
            for pet in self.owner.pets
            for task in pet.get_pending_tasks()
            if task.is_valid() and self._is_scheduled_today(task)
        ]

    def filter_by_status(self, completed: bool = False) -> list[tuple[Task, Pet]]:
        """Return (task, pet) pairs where task.completed matches *completed*.

        Pass ``completed=True`` to see finished tasks, ``False`` (default) for pending.
        """
        return [
            (task, pet)
            for pet in self.owner.pets
            for task in pet.tasks
            if task.completed == completed
        ]

    def filter_by_pet(self, pet_name: str) -> list[Task]:
        """Return all tasks belonging to the pet whose name matches *pet_name* (case-insensitive)."""
        for pet in self.owner.pets:
            if pet.name.lower() == pet_name.lower():
                return list(pet.tasks)
        return []

    def get_recurring_tasks(self) -> list[tuple[Task, Pet]]:
        """Return (task, pet) pairs for tasks scheduled on a recurring basis (daily or weekly)."""
        return [
            (task, pet)
            for pet in self.owner.pets
            for task in pet.tasks
            if task.frequency in ("daily", "weekly")
        ]

    def mark_task_complete(self, task: Task, pet: Pet) -> "Task | None":
        """Mark *task* complete and, for recurring tasks, add the next occurrence to *pet*.

        Returns the newly created Task for the next occurrence, or None for as_needed tasks.

        Example
        -------
        next_task = scheduler.mark_task_complete(feeding_task, my_dog)
        # my_dog.tasks now contains a fresh Feeding task due tomorrow
        """
        next_task = task.mark_complete()
        if next_task is not None:
            pet.add_task(next_task)
        return next_task

    # ------------------------------------------------------------------
    # Time-slot helpers
    # ------------------------------------------------------------------

    def _resolve_preferred_time(self, task: Task) -> str:
        """Return the task's preferred slot, falling back to category-based defaults."""
        if task.preferred_time != "any":
            return task.preferred_time
        return self._CATEGORY_SLOT_DEFAULTS.get(task.category, "any")

    def _preferred_start(self, task: Task, current_dt: datetime, owner_start: datetime) -> datetime:
        """Return the effective start time, advancing into the preferred slot if needed."""
        resolved = self._resolve_preferred_time(task)
        if resolved not in self._SLOT_WINDOWS:
            return current_dt
        slot_start, _ = self._SLOT_WINDOWS[resolved]
        # Never start before the owner's day begins.
        effective_slot_start = max(datetime.combine(date.today(), slot_start), owner_start)
        return max(current_dt, effective_slot_start)

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def _sort_pairs(self, pairs: list[tuple[Task, Pet]]) -> list[tuple[Task, Pet]]:
        """
        Sort into tiers: (required first, slot order, priority desc).
        Within each tier, interleave tasks by pet via round-robin so no single
        pet monopolises consecutive slots.
        """
        def tier_key(pair: tuple[Task, Pet]) -> tuple[bool, int, int]:
            task, _ = pair
            resolved = self._resolve_preferred_time(task)
            return (not task.required, self._SLOT_ORDER.get(resolved, 3), -task.priority)

        # Group by tier while preserving a per-pet queue inside each tier.
        tiers: dict[tuple, dict[str, list[tuple[Task, Pet]]]] = {}
        for pair in sorted(pairs, key=tier_key):
            key = tier_key(pair)
            tiers.setdefault(key, {})
            tiers[key].setdefault(pair[1].name, []).append(pair)

        result: list[tuple[Task, Pet]] = []
        for key in sorted(tiers.keys()):
            pet_queues = tiers[key]
            pet_names = list(pet_queues.keys())
            # Within each pet queue, prefer shorter tasks first.
            for name in pet_names:
                pet_queues[name].sort(key=lambda p: p[0].duration)
            # Round-robin across pets to interleave their tasks.
            while any(pet_queues[name] for name in pet_names):
                for name in pet_names:
                    if pet_queues[name]:
                        result.append(pet_queues[name].pop(0))

        return result

    def sort_tasks_by_priority(self) -> list[tuple[Task, Pet]]:
        """Return today's (task, pet) pairs sorted by priority desc, then duration asc."""
        return sorted(
            self._filter_for_today(),
            key=lambda pair: (-pair[0].priority, pair[0].duration),
        )

    def sort_by_time(self, scheduled_tasks: list[ScheduledTask]) -> list[ScheduledTask]:
        """Return scheduled tasks sorted by start_time ascending.

        Uses a lambda with strftime('%H:%M') as the sort key so that times stored
        as strings in "HH:MM" format compare lexicographically in the correct order.
        """
        return sorted(scheduled_tasks, key=lambda st: st.start_time.strftime("%H:%M"))

    # ------------------------------------------------------------------
    # Core scheduling
    # ------------------------------------------------------------------

    def fits_in_window(self, tasks: list[Task]) -> bool:
        """Return True if tasks fit using min_duration where available."""
        effective_total = sum(t.min_duration or t.duration for t in tasks)
        return effective_total <= self.owner.get_available_time()

    def generate_plan(self) -> DailyPlan:
        """
        Schedule tasks into the owner's day using:
          1. Frequency filtering  — skip tasks not due today
          2. Required-first order — guaranteed tasks placed before optional ones
          3. Per-pet interleaving — round-robin within each priority tier
          4. Time-slot pinning    — tasks advance into their preferred window
          5. Category defaults    — feeding/walk → morning, grooming → afternoon, etc.
          6. Duration flexibility — shrink to min_duration before skipping
          7. Buffer gaps          — owner.break_duration inserted after each task
          8. Energy budget        — skip tasks that exceed owner.energy_budget
        """
        plan = DailyPlan(owner=self.owner)
        reasons: list[str] = []

        pairs = self._filter_for_today()
        if not pairs:
            return plan

        today = date.today()
        owner_start = datetime.combine(today, self.owner.day_start)
        owner_end = datetime.combine(today, self.owner.day_end)
        current_dt = owner_start
        total_effort = 0

        for task, pet in self._sort_pairs(pairs):
            # 8. Energy budget check.
            if self.owner.energy_budget > 0 and total_effort + task.effort > self.owner.energy_budget:
                plan.skipped_tasks.append(task)
                tag = " [required]" if task.required else ""
                reasons.append(f"'{task.name}'{tag} skipped — energy budget exceeded")
                continue

            # 4 & 5. Advance into preferred time slot if we haven't reached it yet.
            start_dt = self._preferred_start(task, current_dt, owner_start)

            # 6. Try full duration; shrink to min_duration if the task allows it.
            duration = task.duration
            if start_dt + timedelta(minutes=duration) > owner_end and task.min_duration > 0:
                duration = task.min_duration

            if start_dt + timedelta(minutes=duration) > owner_end:
                plan.skipped_tasks.append(task)
                tag = " [required]" if task.required else ""
                reasons.append(f"'{task.name}'{tag} skipped — window too tight")
                continue

            plan.scheduled_items.append(
                ScheduledTask(task=task, pet=pet, start_time=start_dt.time(), actual_duration=duration)
            )
            total_effort += task.effort

            shrunk = f", shrunk from {task.duration}min" if duration < task.duration else ""
            reasons.append(
                f"'{task.name}' (P{task.priority}, {duration}min{shrunk})"
                f" -> {start_dt.strftime('%H:%M')} [{pet.name}]"
            )
            # 7. Advance pointer past the task and its trailing buffer.
            current_dt = start_dt + timedelta(minutes=duration + self.owner.break_duration)

        plan.reasoning = self._build_reasoning(reasons, total_effort)
        return plan

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self, plan: DailyPlan) -> list[tuple[ScheduledTask, ScheduledTask]]:
        """Return every pair of ScheduledTask objects whose time windows overlap.

        Iterates over all ordered combinations once (O(n²)) and delegates the
        overlap test to :meth:`ScheduledTask.conflicts_with`.
        """
        conflicts: list[tuple[ScheduledTask, ScheduledTask]] = []
        items = plan.scheduled_items
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if items[i].conflicts_with(items[j]):
                    conflicts.append((items[i], items[j]))
        return conflicts

    def warn_conflicts(self, plan: DailyPlan) -> list[str]:
        """Return a warning string for every overlapping task pair; never raises.

        Lightweight strategy: reuses detect_conflicts (O(n²) pass) and formats
        each overlap as a human-readable message.  Returns an empty list when
        the plan is conflict-free.
        """
        return [
            f"WARNING: [{a.pet.name}] '{a.task.name}' "
            f"({a.start_time.strftime('%H:%M')}-{a.end_time().strftime('%H:%M')}) "
            f"overlaps with [{b.pet.name}] '{b.task.name}' "
            f"({b.start_time.strftime('%H:%M')}-{b.end_time().strftime('%H:%M')})"
            for a, b in self.detect_conflicts(plan)
        ]

    def _build_reasoning(self, reasons: list[str], total_effort: int) -> str:
        """Format per-task scheduling decisions into a readable explanation."""
        budget_note = (
            f", effort {total_effort}/{self.owner.energy_budget}"
            if self.owner.energy_budget > 0
            else ""
        )
        intro = (
            f"Scheduled across a {self.owner.get_available_time()}-min window "
            f"({self.owner.day_start.strftime('%H:%M')}-{self.owner.day_end.strftime('%H:%M')})"
            f"{budget_note}, ordered by priority (highest first):\n"
        )
        return intro + "\n".join(f"  - {r}" for r in reasons)
