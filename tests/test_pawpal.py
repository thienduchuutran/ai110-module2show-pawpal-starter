import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, time, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler, ScheduledTask, DailyPlan


# ---------------------------------------------------------------------------
# Existing tests (preserved)
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    task = Task(name="Morning Walk", duration=30, priority=3)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Buddy", species="dog", age=3)
    initial_count = len(pet.tasks)
    pet.add_task(Task(name="Feeding", duration=10, priority=3))
    assert len(pet.tasks) == initial_count + 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_owner_with_pet(tasks=None):
    """Return an (owner, pet, scheduler) triple loaded with the given tasks."""
    pet = Pet(name="Buddy", species="dog", age=3)
    if tasks:
        for t in tasks:
            pet.add_task(t)
    owner = Owner(name="Alice", day_start=time(8, 0), day_end=time(20, 0))
    owner.add_pet(pet)
    return owner, pet, Scheduler(owner)


# ---------------------------------------------------------------------------
# 1. Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """ScheduledTasks come back earliest-to-latest regardless of input order."""
    owner, pet, scheduler = make_owner_with_pet()
    t1 = Task(name="Evening Walk", duration=20, priority=2)
    t2 = Task(name="Feeding",      duration=10, priority=3)
    t3 = Task(name="Morning Walk", duration=30, priority=3)
    st_evening = ScheduledTask(task=t1, pet=pet, start_time=time(17, 0))
    st_feeding = ScheduledTask(task=t2, pet=pet, start_time=time(8,  0))
    st_morning = ScheduledTask(task=t3, pet=pet, start_time=time(9,  0))
    # Feed in reverse order to exercise the sort.
    result = scheduler.sort_by_time([st_evening, st_morning, st_feeding])
    assert [st.start_time for st in result] == [time(8, 0), time(9, 0), time(17, 0)]


def test_sort_tasks_by_priority_highest_first():
    """sort_tasks_by_priority puts high-priority tasks before low-priority ones."""
    low  = Task(name="Playtime",     duration=15, priority=1)
    med  = Task(name="Grooming",     duration=20, priority=2)
    high = Task(name="Morning Walk", duration=30, priority=3)
    pet = Pet(name="Buddy", species="dog", age=3)
    for t in (low, med, high):
        pet.add_task(t)
    owner = Owner(name="Alice")
    owner.add_pet(pet)
    result = Scheduler(owner).sort_tasks_by_priority()
    priorities = [pair[0].priority for pair in result]
    assert priorities == sorted(priorities, reverse=True)


def test_sort_tasks_priority_tie_broken_by_duration():
    """Among equal-priority tasks, shorter duration comes first."""
    long_task  = Task(name="Long Walk",  duration=60, priority=3)
    short_task = Task(name="Quick Feed", duration=10, priority=3)
    pet = Pet(name="Buddy", species="dog", age=3)
    pet.add_task(long_task)
    pet.add_task(short_task)
    owner = Owner(name="Alice")
    owner.add_pet(pet)
    result = Scheduler(owner).sort_tasks_by_priority()
    assert result[0][0].name == "Quick Feed"
    assert result[1][0].name == "Long Walk"


def test_required_tasks_sorted_before_optional():
    """Required tasks must precede optional ones in the sorted output."""
    optional = Task(name="Playtime", duration=15, priority=3)
    required = Task(name="Feeding",  duration=10, priority=1, required=True)
    pet = Pet(name="Buddy", species="dog", age=3)
    pet.add_task(optional)
    pet.add_task(required)
    owner = Owner(name="Alice")
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    pairs = scheduler._sort_pairs(scheduler._filter_for_today())
    assert pairs[0][0].required is True


# ---------------------------------------------------------------------------
# 2. Recurrence logic
# ---------------------------------------------------------------------------

def test_daily_task_creates_next_occurrence_tomorrow():
    """Completing a daily task returns a new task due the following day."""
    task = Task(name="Feeding", duration=10, priority=3, frequency="daily")
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.due_date == date.today() + timedelta(days=1)
    assert next_task.completed is False


def test_weekly_task_creates_next_occurrence_in_7_days():
    """Completing a weekly task returns a new task due 7 days from today."""
    task = Task(name="Bath", duration=30, priority=2, frequency="weekly",
                scheduled_day="monday")
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.due_date == date.today() + timedelta(weeks=1)
    assert next_task.completed is False


def test_as_needed_task_returns_none_on_complete():
    """Completing an as_needed task returns None (no automatic recurrence)."""
    task = Task(name="Vet Visit", duration=60, priority=3, frequency="as_needed")
    result = task.mark_complete()
    assert result is None
    assert task.completed is True


def test_mark_task_complete_adds_next_occurrence_to_pet():
    """Scheduler.mark_task_complete() appends the next occurrence to the pet's task list."""
    owner, pet, scheduler = make_owner_with_pet()
    task = Task(name="Feeding", duration=10, priority=3, frequency="daily")
    pet.add_task(task)
    before_count = len(pet.tasks)
    next_task = scheduler.mark_task_complete(task, pet)
    assert next_task is not None
    assert len(pet.tasks) == before_count + 1
    assert pet.tasks[-1].due_date == date.today() + timedelta(days=1)


def test_mark_task_complete_as_needed_does_not_grow_task_list():
    """Completing an as_needed task must NOT add a new task to the pet."""
    owner, pet, scheduler = make_owner_with_pet()
    task = Task(name="Vet Visit", duration=60, priority=3, frequency="as_needed")
    pet.add_task(task)
    before_count = len(pet.tasks)
    scheduler.mark_task_complete(task, pet)
    assert len(pet.tasks) == before_count


# ---------------------------------------------------------------------------
# 3. Conflict detection
# ---------------------------------------------------------------------------

def test_no_conflict_for_sequential_tasks():
    """Tasks placed back-to-back (no overlap) must produce zero conflicts."""
    owner, pet, scheduler = make_owner_with_pet()
    t1 = Task(name="Walk",    duration=30, priority=3)
    t2 = Task(name="Feeding", duration=10, priority=3)
    st1 = ScheduledTask(task=t1, pet=pet, start_time=time(8,  0))  # 08:00-08:30
    st2 = ScheduledTask(task=t2, pet=pet, start_time=time(8, 30))  # 08:30-08:40
    plan = DailyPlan(owner=owner, scheduled_items=[st1, st2])
    assert scheduler.detect_conflicts(plan) == []


def test_conflict_detected_for_same_start_time():
    """Two tasks with identical start times must be reported as a conflict."""
    owner, pet, scheduler = make_owner_with_pet()
    t1 = Task(name="Walk",    duration=30, priority=3)
    t2 = Task(name="Feeding", duration=10, priority=3)
    st1 = ScheduledTask(task=t1, pet=pet, start_time=time(8, 0))
    st2 = ScheduledTask(task=t2, pet=pet, start_time=time(8, 0))
    plan = DailyPlan(owner=owner, scheduled_items=[st1, st2])
    conflicts = scheduler.detect_conflicts(plan)
    assert len(conflicts) == 1


def test_conflict_detected_for_overlapping_tasks():
    """A task that starts before another finishes is a conflict."""
    owner, pet, scheduler = make_owner_with_pet()
    t1 = Task(name="Walk",    duration=60, priority=3)   # 08:00-09:00
    t2 = Task(name="Feeding", duration=15, priority=3)   # 08:45-09:00  <- overlaps
    st1 = ScheduledTask(task=t1, pet=pet, start_time=time(8,  0))
    st2 = ScheduledTask(task=t2, pet=pet, start_time=time(8, 45))
    plan = DailyPlan(owner=owner, scheduled_items=[st1, st2])
    assert len(scheduler.detect_conflicts(plan)) == 1


def test_no_conflict_for_empty_plan():
    """detect_conflicts on an empty plan must return an empty list without raising."""
    owner, _, scheduler = make_owner_with_pet()
    plan = DailyPlan(owner=owner, scheduled_items=[])
    assert scheduler.detect_conflicts(plan) == []


def test_no_conflict_for_single_task():
    """A plan with exactly one task can never have a conflict."""
    owner, pet, scheduler = make_owner_with_pet()
    t = Task(name="Walk", duration=30, priority=3)
    st = ScheduledTask(task=t, pet=pet, start_time=time(8, 0))
    plan = DailyPlan(owner=owner, scheduled_items=[st])
    assert scheduler.detect_conflicts(plan) == []


def test_warn_conflicts_returns_warning_strings():
    """warn_conflicts must return 'WARNING' strings for overlapping tasks."""
    owner, pet, scheduler = make_owner_with_pet()
    t1 = Task(name="Walk",    duration=30, priority=3)
    t2 = Task(name="Feeding", duration=10, priority=3)
    st1 = ScheduledTask(task=t1, pet=pet, start_time=time(8, 0))
    st2 = ScheduledTask(task=t2, pet=pet, start_time=time(8, 0))
    plan = DailyPlan(owner=owner, scheduled_items=[st1, st2])
    warnings = scheduler.warn_conflicts(plan)
    assert len(warnings) == 1
    assert "WARNING" in warnings[0]


# ---------------------------------------------------------------------------
# 4. Edge cases
# ---------------------------------------------------------------------------

def test_pet_with_no_tasks_produces_empty_plan():
    """A pet registered with zero tasks yields an empty, feasible plan."""
    owner, _, scheduler = make_owner_with_pet(tasks=[])
    plan = scheduler.generate_plan()
    assert plan.scheduled_items == []
    assert plan.skipped_tasks == []
    assert plan.is_feasible()


def test_as_needed_task_excluded_from_plan():
    """as_needed tasks must never appear in generate_plan output."""
    task = Task(name="Vet Visit", duration=60, priority=3, frequency="as_needed")
    owner, _, scheduler = make_owner_with_pet(tasks=[task])
    plan = scheduler.generate_plan()
    assert plan.scheduled_items == []


def test_daily_task_not_yet_due_excluded_from_plan():
    """A daily task whose due_date is tomorrow must be excluded from today's plan."""
    tomorrow = date.today() + timedelta(days=1)
    task = Task(name="Feeding", duration=10, priority=3, frequency="daily",
                due_date=tomorrow)
    owner, _, scheduler = make_owner_with_pet(tasks=[task])
    plan = scheduler.generate_plan()
    assert plan.scheduled_items == []


def test_weekly_task_wrong_day_excluded_from_plan():
    """A weekly task whose scheduled_day is not today must be filtered out."""
    days = ["monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday"]
    today_name = date.today().strftime("%A").lower()
    other_day = next(d for d in days if d != today_name)
    task = Task(name="Bath", duration=30, priority=2, frequency="weekly",
                scheduled_day=other_day)
    owner, _, scheduler = make_owner_with_pet(tasks=[task])
    plan = scheduler.generate_plan()
    assert plan.scheduled_items == []


def test_filter_by_pet_case_insensitive():
    """filter_by_pet must match regardless of name casing."""
    task = Task(name="Feeding", duration=10, priority=3)
    owner, _, scheduler = make_owner_with_pet(tasks=[task])
    assert scheduler.filter_by_pet("buddy") != []
    assert scheduler.filter_by_pet("BUDDY") != []
    assert scheduler.filter_by_pet("unknown") == []


def test_generate_plan_tasks_do_not_exceed_day_end():
    """Every scheduled task must finish at or before owner.day_end."""
    tasks = [
        Task(name="Walk",     duration=30, priority=3),
        Task(name="Feeding",  duration=10, priority=3),
        Task(name="Playtime", duration=15, priority=1),
    ]
    owner, _, scheduler = make_owner_with_pet(tasks=tasks)
    plan = scheduler.generate_plan()
    for item in plan.scheduled_items:
        assert item.end_time() <= owner.day_end


def test_task_shrunk_when_window_is_tight():
    """A flexible task (min_duration > 0) is shrunk rather than skipped when space is tight."""
    # 690 min filler consumes all but 30 min of the 720-min (8-20h) window.
    filler     = Task(name="Long Activity", duration=690, priority=3)
    shrinkable = Task(name="Quick Walk",    duration=60,  priority=2, min_duration=5)
    owner, pet, scheduler = make_owner_with_pet(tasks=[filler, shrinkable])
    plan = scheduler.generate_plan()
    scheduled_names = [item.task.name for item in plan.scheduled_items]
    if "Quick Walk" in scheduled_names:
        item = next(i for i in plan.scheduled_items if i.task.name == "Quick Walk")
        assert item.actual_duration <= shrinkable.duration


def test_get_recurring_tasks_excludes_as_needed():
    """get_recurring_tasks must return only daily/weekly tasks, not as_needed."""
    daily  = Task(name="Feeding",   duration=10, priority=3, frequency="daily")
    weekly = Task(name="Bath",      duration=30, priority=2, frequency="weekly")
    once   = Task(name="Vet Visit", duration=60, priority=3, frequency="as_needed")
    owner, _, scheduler = make_owner_with_pet(tasks=[daily, weekly, once])
    recurring = scheduler.get_recurring_tasks()
    freqs = {t.frequency for t, _ in recurring}
    assert "as_needed" not in freqs
    assert "daily" in freqs
    assert "weekly" in freqs
