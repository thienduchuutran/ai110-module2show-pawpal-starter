import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Owner setup — created once, lives in session_state for the whole session
# ---------------------------------------------------------------------------
owner_name = st.text_input("Owner name", value="Jordan")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name)

if st.button("Reset owner"):
    st.session_state.owner = Owner(name=owner_name)
    st.success(f"Owner '{owner_name}' reset. All pets and tasks cleared.")

st.divider()

# ---------------------------------------------------------------------------
# Add a pet — form submits → owner.add_pet() stores it in the Owner object
# ---------------------------------------------------------------------------
st.subheader("Add a Pet")

with st.form("add_pet_form"):
    pet_name = st.text_input("Pet name", value="Mochi")
    species  = st.selectbox("Species", ["dog", "cat", "other"])
    age      = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
    load_defaults = st.checkbox("Load default tasks for this species", value=True)
    submitted = st.form_submit_button("Add pet")

if submitted:
    new_pet = Pet(name=pet_name, species=species, age=age)
    if load_defaults:
        new_pet.load_default_tasks()       # Pet.load_default_tasks() populates species tasks
    st.session_state.owner.add_pet(new_pet)  # Owner.add_pet() registers the pet
    st.success(f"Pet '{pet_name}' added to {st.session_state.owner.name}'s profile.")

# Show current pets so the user sees the update immediately after submit
if st.session_state.owner.pets:
    st.write("Registered pets:")
    for pet in st.session_state.owner.pets:
        st.markdown(f"- **{pet.name}** ({pet.species}, age {pet.age})")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Add a task — user picks which pet, Task object is added via pet.add_task()
# ---------------------------------------------------------------------------
st.subheader("Add a Task")

if not st.session_state.owner.pets:
    st.warning("Add a pet first before scheduling tasks.")
else:
    PRIORITY_MAP = {"low": 1, "medium": 2, "high": 3}

    pet_names = [p.name for p in st.session_state.owner.pets]

    with st.form("add_task_form"):
        target_pet = st.selectbox("For which pet?", pet_names)
        col1, col2, col3 = st.columns(3)
        with col1:
            task_title = st.text_input("Task title", value="Evening walk")
        with col2:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=1)
        task_submitted = st.form_submit_button("Add task")

    if task_submitted:
        new_task = Task(
            name=task_title,
            duration=int(duration),
            priority=PRIORITY_MAP[priority],
        )
        # Find the chosen pet in the Owner's list, then call pet.add_task()
        pet_obj = next(p for p in st.session_state.owner.pets if p.name == target_pet)
        pet_obj.add_task(new_task)           # Pet.add_task() appends to pet.tasks
        st.success(f"Task '{task_title}' added to {target_pet}.")

    # Display all tasks grouped by pet — re-read from owner each run
    all_tasks = st.session_state.owner.get_all_tasks()
    if all_tasks:
        st.write("Current tasks:")
        st.table([t.to_dict() for t in all_tasks])
    else:
        st.info("No tasks yet.")

st.divider()

# ---------------------------------------------------------------------------
# Generate schedule — Scheduler reads from owner, produces a DailyPlan
# ---------------------------------------------------------------------------
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    owner = st.session_state.owner
    if not owner.get_all_pending_tasks():
        st.warning("No pending tasks to schedule.")
    else:
        scheduler = Scheduler(owner)
        plan = scheduler.generate_plan()       # Scheduler.generate_plan() returns DailyPlan
        st.text(plan.display())                # DailyPlan.display() formats the output
        with st.expander("Reasoning"):
            st.text(plan.reasoning)
