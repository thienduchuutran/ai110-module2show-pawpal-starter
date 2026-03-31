import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Owner & Pet setup
# ---------------------------------------------------------------------------
owner_name = st.text_input("Owner name", value="Jordan")
pet_name   = st.text_input("Pet name",   value="Mochi")
species    = st.selectbox("Species", ["dog", "cat", "other"])

# Guard: only create the Owner once per browser session.
# Every Streamlit rerun executes this whole file from top to bottom,
# but the `if` check makes sure we skip creation when the key already exists.
if "owner" not in st.session_state:
    pet = Pet(name=pet_name, species=species, age=0)
    pet.load_default_tasks()
    st.session_state.owner = Owner(name=owner_name)
    st.session_state.owner.add_pet(pet)

# Let the user replace the Owner/Pet when they explicitly click Reset.
if st.button("Reset owner & pet"):
    pet = Pet(name=pet_name, species=species, age=0)
    pet.load_default_tasks()
    st.session_state.owner = Owner(name=owner_name)
    st.session_state.owner.add_pet(pet)
    st.success(f"Owner '{owner_name}' with pet '{pet_name}' created.")

st.divider()

# ---------------------------------------------------------------------------
# Task management
# ---------------------------------------------------------------------------
st.subheader("Tasks")
st.caption("Tasks are stored on the Pet object inside session_state.owner.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

PRIORITY_MAP = {"low": 1, "medium": 2, "high": 3}

if st.button("Add task"):
    new_task = Task(
        name=task_title,
        duration=int(duration),
        priority=PRIORITY_MAP[priority],
    )
    # Add directly to the first pet stored in the Owner object.
    st.session_state.owner.pets[0].add_task(new_task)
    st.success(f"Task '{task_title}' added.")

# Display all tasks from the live Owner object.
all_tasks = st.session_state.owner.get_all_tasks()
if all_tasks:
    st.write("Current tasks:")
    st.table([t.to_dict() for t in all_tasks])
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Schedule generation
# ---------------------------------------------------------------------------
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    owner = st.session_state.owner
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()
    st.text(plan.display())
    with st.expander("Reasoning"):
        st.text(plan.reasoning)
