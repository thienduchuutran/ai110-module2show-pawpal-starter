from __future__ import annotations
from dataclasses import dataclass, field
from datetime import time


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str
    age: int
    breed: str = ""
    special_needs: list[str] = field(default_factory=list)

    def get_default_tasks(self) -> list[Task]:
        """Return a starter list of common tasks for this pet type."""
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int
    day_start: time = time(8, 0)
    day_end: time = time(20, 0)
    preferences: dict = field(default_factory=dict)
    pet: Pet | None = None

    def add_pet(self, pet: Pet) -> None:
        """Attach a pet to this owner."""
        pass

    def get_available_time(self) -> int:
        """Return total available minutes for the day."""
        pass

    def update_preferences(self, **kwargs) -> None:
        """Update one or more scheduling preferences."""
        pass


@dataclass
class Task:
    name: str
    duration: int          # minutes
    priority: int          # 1 = low, 2 = medium, 3 = high
    category: str = ""     # walk / feeding / meds / grooming / enrichment
    notes: str = ""

    def is_valid(self) -> bool:
        """Return True if the task has a positive duration and valid priority."""
        pass

    def to_dict(self) -> dict:
        """Serialize the task to a plain dictionary."""
        pass


@dataclass
class ScheduledTask:
    task: Task
    start_time: time

    def end_time(self) -> time:
        """Compute the end time based on task duration."""
        pass

    def conflicts_with(self, other: ScheduledTask) -> bool:
        """Return True if this slot overlaps with another ScheduledTask."""
        pass


@dataclass
class DailyPlan:
    scheduled_items: list[ScheduledTask] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    total_duration: int = 0
    reasoning: str = ""

    def is_feasible(self) -> bool:
        """Return True if all scheduled items fit within the day window."""
        pass

    def display(self) -> str:
        """Return a human-readable version of the schedule."""
        pass

    def get_summary(self) -> str:
        """Return a short summary line (tasks scheduled, time used, skipped)."""
        pass


# ---------------------------------------------------------------------------
# Logic class
# ---------------------------------------------------------------------------

class Scheduler:
    def __init__(self, owner: Owner, pet: Pet, tasks: list[Task]):
        self.owner = owner
        self.pet = pet
        self.tasks = tasks

    def sort_tasks_by_priority(self) -> list[Task]:
        """Return tasks sorted highest priority first."""
        pass

    def fits_in_window(self, tasks: list[Task]) -> bool:
        """Return True if the combined duration fits in the owner's available time."""
        pass

    def generate_plan(self) -> DailyPlan:
        """Build and return a DailyPlan by scheduling tasks within the day window."""
        pass

    def explain_reasoning(self) -> str:
        """Return a plain-English explanation of how the plan was built."""
        pass
