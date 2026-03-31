# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
My initial design had 5–6 classes:

Owner: stores the user's name, available time window, and preferences
Pet: stores the animal's name, species, age, and any special needs
Task: holds a single care activity with its duration, priority, and category
Scheduler: the core logic class; takes an Owner, Pet, and list of Tasks and produces a plan
DailyPlan: the output object; holds an ordered list of scheduled items, skipped tasks, and a reasoning string
ScheduledTask: a lightweight wrapper pairing a Task with a specific start time

classDiagram
    class Owner {
        +str name
        +int available_minutes
        +time day_start
        +time day_end
        +dict preferences
        +add_pet(pet)
        +get_available_time() int
        +update_preferences()
    }

    class Pet {
        +str name
        +str species
        +int age
        +str breed
        +list special_needs
        +get_default_tasks() list
    }

    class Task {
        +str name
        +int duration
        +int priority
        +str category
        +str notes
        +is_valid() bool
        +to_dict() dict
    }

    class Scheduler {
        +Owner owner
        +Pet pet
        +list tasks
        +generate_plan() DailyPlan
        +sort_tasks_by_priority() list
        +fits_in_window(tasks) bool
        +explain_reasoning() str
    }

    class DailyPlan {
        +list scheduled_items
        +int total_duration
        +list skipped_tasks
        +str reasoning
        +display() str
        +is_feasible() bool
        +get_summary() str
    }

    class ScheduledTask {
        +Task task
        +time start_time
        +conflicts_with(other) bool
        +end_time() time
    }

    Owner "1" --> "1" Pet
    Owner "1" --> "*" Task
    Scheduler --> Owner
    Scheduler --> Pet
    Scheduler --> Task
    Scheduler ..> DailyPlan : produces
    DailyPlan "1" --> "*" ScheduledTask
    ScheduledTask --> Task


- What classes did you include, and what responsibilities did you assign to each?
The main responsibility split was: data objects (Owner, Pet, Task) hold information, Scheduler holds logic, and DailyPlan holds the result

**b. Design changes**

- Did your design change during implementation? Yes
- If yes, describe at least one change and why you made it.

yes it changed in two ways. first i originally had owner connected to just one pet but then i realized that doesnt make sense because a person can have more than one animal. so i changed owner to hold a list of pets and added methods like get_all_tasks() so the scheduler can just ask the owner for everything instead of going through each pet manually.

second the ui also changed. the starter code was saving tasks as plain dicts in session_state but once i had the real classes i just stored the whole owner object in session_state instead. that way all the data stays in one place and when i click generate schedule i just pass session_state.owner straight to the scheduler, no rebuilding needed.
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

The scheduler considers several constraints layered on top of each other. The hard constraints are the owner's time window (day_start / day_end) and the task's duration, a task that doesn't fit in the remaining window is skipped entirely, or shrunk to its min_duration if one is set. On top of that there are soft constraints: task priority (1–3), a required flag that guarantees placement before optional tasks, preferred_time / category defaults that nudge tasks into morning / afternoon / evening slots, an energy_budget that caps how much total effort the owner takes on, and a break_duration buffer inserted between tasks so nothing is back-to-back with no breathing room.

- How did you decide which constraints mattered most?

I ranked them by consequence. The time window is non-negotiable, you can't schedule outside the day. The required flag and priority come next because a required task like giving medication has to happen regardless of what else is on the list. Everything else (preferred slot, energy budget, buffer) is about comfort and realism rather than correctness, so it shapes the schedule but never overrides the hard constraints.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

The scheduler is a greedy single-pass algorithm. It sorts tasks once by (required first, slot order, priority descending), then walks through them in that order and places each task as early as possible in its preferred window. It never goes back and reconsiders an earlier placement.

- Why is that tradeoff reasonable for this scenario?

For a daily pet care schedule with maybe 5-20 tasks, a near-optimal result is good enough. The owner doesn't need a mathematically perfect arrangement, they need a clear, workable plan quickly. A backtracking or constraint-satisfaction approach would handle edge cases better (for example, noticing that shifting a high-priority task 15 minutes later would let two lower-priority tasks fit instead of one), but it would add a lot of complexity for very little practical gain. The greedy approach is easy to reason about, easy to debug, and fast enough that it could run on every UI interaction without lag.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
for helping me with designing OOP objects, catching when i miss something, explain the dataflow and how components are wired and layers interact with each other
- What kinds of prompts or questions were most helpful?
"explain to me how abc works"

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
I learned more about systems design and some OOP implementation

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
I am the driver, I must know what direction I'm going to direct the AI, can't let the AI drive me 
