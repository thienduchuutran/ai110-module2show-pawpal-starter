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
Owner now holds pets: list[Pet] (multiple pets) with get_all_tasks() / get_all_pending_tasks(). 

I changed it because at first the README said a user enter basic owner + pet info, so i only let a pet per owner, but now i think an owner can manage multiple pets and should have access to all their tasks
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

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

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
