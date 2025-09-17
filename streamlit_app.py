import streamlit as st
import datetime
import json
import os
import matplotlib.pyplot as plt
import pandas as pd

# ---------------------------
# Helper functions
# ---------------------------

DATA_FILE = "todo_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    else:
        return {
            "start_date": str(datetime.date.today()),
            "tasks": {},      # { "YYYY-MM-DD": [ {task, priority, done}, ... ] }
            "streaks": {},    # { "YYYY-MM-DD": True/False }
            "goals": {
                "weekly": [],
                "monthly": [],
                "3_months": [],
                "6_months": []
            },
            "main_goal": {"goal": "", "progress": 0}
        }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def parse_streaks(streaks_dict):
    """Return list of (date_obj, done_bool) sorted ascending by date."""
    parsed = []
    for k, v in streaks_dict.items():
        try:
            d = datetime.datetime.strptime(k, "%Y-%m-%d").date()
            parsed.append((d, bool(v)))
        except Exception:
            continue
    parsed.sort(key=lambda x: x[0])
    return parsed

def compute_current_streak(parsed_streaks):
    """Count consecutive True values from the latest date backwards."""
    count = 0
    if not parsed_streaks:
        return 0
    for d, done in reversed(parsed_streaks):
        if done:
            count += 1
        else:
            break
    return count

# ---------------------------
# App start
# ---------------------------

st.set_page_config(page_title="To-Do & Streak Tracker", layout="wide")
st.title("📝 To-Do List & Streak Tracker with Goals")

data = load_data()

# ---------------------------
# Sidebar: Challenge Start Date + Current Streak
# ---------------------------
st.sidebar.subheader("⚡ Challenge Start Date")
try:
    start_date = datetime.datetime.strptime(data["start_date"], "%Y-%m-%d").date()
except Exception:
    start_date = datetime.date.today()
new_start = st.sidebar.date_input("Set/Change Start Date", value=start_date)

if new_start != start_date:
    data["start_date"] = new_start.isoformat()
    save_data(data)
    st.sidebar.success(f"Challenge start date updated to {new_start}")

days_passed = (datetime.date.today() - datetime.datetime.strptime(data["start_date"], "%Y-%m-%d").date()).days + 1
st.sidebar.markdown(f"**Challenge started:** {data['start_date']}")
st.sidebar.markdown(f"**Days Count:** {days_passed} days")

parsed = parse_streaks(data.get("streaks", {}))
current_streak = compute_current_streak(parsed)
st.sidebar.markdown(f"🔥 **Current Streak:** {current_streak} days")

# ---------------------------
# Main Goal Tracker
# ---------------------------
st.header("🌟 Main Goal Tracker")
main_goal = data.get("main_goal", {"goal": "", "progress": 0})

with st.form("main_goal_form", clear_on_submit=False):
    goal_text = st.text_input("Enter your Main Goal", value=main_goal.get("goal", ""))
    progress = st.slider("Progress (%)", 0, 100, main_goal.get("progress", 0))
    submitted = st.form_submit_button("Save Main Goal")
    if submitted:
        data["main_goal"] = {"goal": goal_text, "progress": progress}
        save_data(data)
        st.success("Main Goal updated!")

if data.get("main_goal", {}).get("goal"):
    st.markdown(f"**Main Goal:** {data['main_goal']['goal']}")
    st.progress(data["main_goal"]["progress"] / 100)

# ---------------------------
# Add Task
# ---------------------------
st.header("Add a Task")
with st.form("add_task_form", clear_on_submit=True):
    task_name = st.text_input("Task Name")
    priority = st.selectbox("Priority", ["High", "Medium", "Low"])
    add_submitted = st.form_submit_button("Add Task")
    if add_submitted:
        today = datetime.date.today().isoformat()
        if today not in data["tasks"]:
            data["tasks"][today] = []
        data["tasks"][today].append({"task": task_name, "priority": priority, "done": False})
        save_data(data)
        st.success("Task added!")

# ---------------------------
# Show Today’s Tasks
# ---------------------------
st.header("Today’s Tasks")
today = datetime.date.today().isoformat()
tasks_today = data["tasks"].get(today, [])

if tasks_today:
    for i, t in enumerate(tasks_today):
        col1, col2, col3 = st.columns([5, 1, 1])
        with col1:
            if t["priority"] == "High":
                st.markdown(f"**🔥 {t['task']}**  —  _{t['priority']}_")
            elif t["priority"] == "Medium":
                st.markdown(f"**🟡 {t['task']}**  —  _{t['priority']}_")
            else:
                st.markdown(f"**🟢 {t['task']}**  —  _{t['priority']}_")

        key_done = f"done_{today}_{i}"
        checked = st.checkbox("Done", value=t.get("done", False), key=key_done)
        data["tasks"][today][i]["done"] = bool(checked)

        with col3:
            if st.button("Delete", key=f"del_{today}_{i}"):
                data["tasks"][today].pop(i)
                save_data(data)
                st.rerun()
    save_data(data)
else:
    st.info("No tasks added for today yet.")

# ---------------------------
# Update today's streak value
# ---------------------------
completed_today = all(t.get("done", False) for t in data["tasks"].get(today, [])) if today in data["tasks"] else False
data["streaks"][today] = bool(completed_today)
save_data(data)

# ---------------------------
# Reset Today's Streak
# ---------------------------
if st.button("❌ Reset Today’s Streak to 0"):
    data["streaks"][today] = False
    save_data(data)
    st.warning("Today's streak has been reset to 0!")
    st.rerun()

# ---------------------------
# Streak Chart (Monthly)
# ---------------------------
st.header("📊 Monthly Streak Chart")
if data.get("streaks"):
    streak_df = pd.DataFrame(list(data["streaks"].items()), columns=["date", "done"])
    streak_df["date"] = pd.to_datetime(streak_df["date"], format="%Y-%m-%d", errors="coerce")
    streak_df = streak_df.dropna(subset=["date"])
    streak_df["month"] = streak_df["date"].dt.to_period("M")
    monthly_streak = streak_df.groupby("month")["done"].sum().reset_index()
    fig, ax = plt.subplots()
    ax.bar(monthly_streak["month"].astype(str), monthly_streak["done"])
    ax.set_title("Monthly Completed Days")
    ax.set_xlabel("Month")
    ax.set_ylabel("Days Completed")
    plt.xticks(rotation=45)
    st.pyplot(fig)

# ---------------------------
# Compute streaks again
# ---------------------------
parsed = parse_streaks(data.get("streaks", {}))
current_streak = compute_current_streak(parsed)
st.markdown(f"**Current streak:** {current_streak} days")

# ---------------------------
# Reset Current Streak
# ---------------------------
if st.button("🛑 Reset Current Streak to 0"):
    most_recent_true = None
    for d, done in reversed(parsed):
        if done:
            most_recent_true = d
            break

    if most_recent_true:
        key = most_recent_true.isoformat()
        data["streaks"][key] = False
        save_data(data)
        st.warning(f"Current streak was broken by setting {key} to False.")
        st.rerun()
    else:
        st.info("There is no active streak to reset (current streak already 0).")

# ---------------------------
# Goals Section
# ---------------------------
st.header("🎯 Goals")

goal_type = st.selectbox("Select Goal Segment", ["Weekly", "Monthly", "3 Months", "6 Months"])
goal_text = st.text_input("Enter your goal (for the selected segment)")
if st.button("Add Goal"):
    key = goal_type.lower().replace(" ", "_")
    if key not in data["goals"]:
        data["goals"][key] = []
    data["goals"][key].append({"goal": goal_text, "done": False})
    save_data(data)
    st.success(f"Goal added to {goal_type} segment!")

for seg, goals in data["goals"].items():
    st.subheader(f"{seg.capitalize()} Goals")
    if goals:
        done_count = sum(1 for g in goals if g.get("done"))
        total = len(goals)
        st.write(f"Progress: {done_count}/{total} ({(done_count/total)*100:.0f}%)")
        for i, g in enumerate(goals):
            col1, col2 = st.columns([6, 1])
            with col1:
                checked = st.checkbox(g["goal"], value=g.get("done", False), key=f"goal_{seg}_{i}")
                data["goals"][seg][i]["done"] = bool(checked)
            with col2:
                if st.button("Delete", key=f"del_goal_{seg}_{i}"):
                    data["goals"][seg].pop(i)
                    save_data(data)
                    st.rerun()
        save_data(data)
    else:
        st.info("No goals added yet.")
