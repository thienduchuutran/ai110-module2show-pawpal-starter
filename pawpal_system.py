from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    name: str
    duration: int           # minutes
    priority: int           # 1 = low, 2 = medium, 3 = high
    category: str = ""      # walk / feeding / meds / grooming / enrichment
    frequency: str = "daily"  # daily / weekly / as_needed
    notes: str = ""
    completed: bool = False

    def is_valid(self) -> bool:
        """Return True if duration is positive and priority is 1–3."""
        return self.duration > 0 and self.priority in (1, 2, 3)

    def mark_complete(self) -> None:
        self.completed = True

    def reset(self) -> None:
        self.completed = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "duration": self.duration,
            "priority": self.priority,
            "category": self.category,
            "frequency": self.frequency,
            "notes": self.notes,
            "completed": self.completed,
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

    def end_time(self) -> time:
        """Compute end time using datetime arithmetic (time has no + operator)."""
        start_dt = datetime.combine(date.today(), self.start_time)
        return (start_dt + timedelta(minutes=self.task.duration)).time()

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
        """Sum of all scheduled task durations."""
        return sum(item.task.duration for item in self.scheduled_items)

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
            lines.append(
                f"  {item.start_time.strftime('%H:%M')} - {item.end_time().strftime('%H:%M')}"
                f"  [{item.pet.name}] {item.task.name}"
                f"  (P{item.task.priority})"
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
    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def _task_pet_pairs(self) -> list[tuple[Task, Pet]]:
        """Gather all pending (task, pet) pairs from every pet."""
        return [
            (task, pet)
            for pet in self.owner.pets
            for task in pet.get_pending_tasks()
            if task.is_valid()
        ]

    def sort_tasks_by_priority(self) -> list[tuple[Task, Pet]]:
        """Return (task, pet) pairs sorted by priority desc, then duration asc."""
        return sorted(
            self._task_pet_pairs(),
            key=lambda pair: (-pair[0].priority, pair[0].duration),
        )

    def fits_in_window(self, tasks: list[Task]) -> bool:
        """Return True if the combined duration fits inside the owner's available time."""
        return sum(t.duration for t in tasks) <= self.owner.get_available_time()

    def generate_plan(self) -> DailyPlan:
        """
        Greedy scheduler: place tasks highest-priority first into consecutive
        slots starting at owner.day_start; skip anything that won't fit.
        """
        plan = DailyPlan(owner=self.owner)
        current_dt = datetime.combine(date.today(), self.owner.day_start)
        end_dt = datetime.combine(date.today(), self.owner.day_end)
        reasons: list[str] = []

        for task, pet in self.sort_tasks_by_priority():
            task_end_dt = current_dt + timedelta(minutes=task.duration)
            if task_end_dt <= end_dt:
                plan.scheduled_items.append(
                    ScheduledTask(task=task, pet=pet, start_time=current_dt.time())
                )
                reasons.append(
                    f"'{task.name}' (P{task.priority}) -> {current_dt.strftime('%H:%M')} [{pet.name}]"
                )
                current_dt = task_end_dt
            else:
                plan.skipped_tasks.append(task)
                reasons.append(f"'{task.name}' skipped — window too tight")

        plan.reasoning = self._build_reasoning(reasons)
        return plan

    def _build_reasoning(self, reasons: list[str]) -> str:
        intro = (
            f"Scheduled across a {self.owner.get_available_time()}-min window "
            f"({self.owner.day_start.strftime('%H:%M')}-{self.owner.day_end.strftime('%H:%M')}), "
            "ordered by priority (highest first):\n"
        )
        return intro + "\n".join(f"  - {r}" for r in reasons)
