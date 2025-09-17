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
            "tasks": {},
            "streaks": {},
            "goals": {
                "weekly": [],
                "monthly": [],
                "3_months": [],
                "6_months": []
            },
            "main_goal": {"goal": "", "progress": 0}  # NEW
        }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ---------------------------
# App Logic
# ---------------------------

st.title("📝 To-Do List & Streak Tracker with Goals")

data = load_data()

# ---------------------------
# Challenge Start Date Selector
# ---------------------------
st.sidebar.subheader("⚡ Challenge Start Date")
start_date = datetime.datetime.strptime(data["start_date"], "%Y-%m-%d").date()
new_start = st.sidebar.date_input("Set/Change Start Date", value=start_date)

if new_start != start_date:
    data["start_date"] = str(new_start)
    save_data(data)
    st.sidebar.success(f"Challenge start date updated to {new_start}")

days_passed = (datetime.date.today() - datetime.datetime.strptime(data["start_date"], "%Y-%m-%d").date()).days + 1
st.sidebar.markdown(f"**Challenge started:** {data['start_date']}")
st.sidebar.markdown(f"**Days Count:** {days_passed} days")

# ---------------------------
# Main Goal Tracker
# ---------------------------
st.header("🌟 Main Goal Tracker")
main_goal = data.get("main_goal", {"goal": "", "progress": 0})

goal_text = st.text_input("Enter your Main Goal", value=main_goal["goal"])
progress = st.slider("Progress (%)", 0, 100, main_goal["progress"])

if st.button("Save Main Goal"):
    data["main_goal"] = {"goal": goal_text, "progress": progress}
    save_data(data)
    st.success("Main Goal updated!")

if main_goal["goal"]:
    st.markdown(f"**Main Goal:** {data['main_goal']['goal']}")
    st.progress(data["main_goal"]["progress"] / 100)

# ---------------------------
# Add Task
# ---------------------------
st.header("Add a Task")
task_name = st.text_input("Task Name")
priority = st.selectbox("Priority", ["High", "Medium", "Low"])

if st.button("Add Task"):
    today = str(datetime.date.today())
    if today not in data["tasks"]:
        data["tasks"][today] = []
    data["tasks"][today].append({"task": task_name, "priority": priority, "done": False})
    save_data(data)
    st.success("Task added!")

# ---------------------------
# Show Today’s Tasks
# ---------------------------
st.header("Today’s Tasks")
today = str(datetime.date.today())
if today in data["tasks"] and data["tasks"][today]:
    for i, t in enumerate(data["tasks"][today]):
        col1, col2, col3 = st.columns([4, 2, 2])
        with col1:
            if t["priority"] == "High":
                st.markdown(f"🔥 **{t['task']}** ({t['priority']})")
            elif t["priority"] == "Medium":
                st.markdown(f"🟡 {t['task']} ({t['priority']})")
            else:
                st.markdown(f"🟢 {t['task']} ({t['priority']})")

        with col2:
            if st.checkbox("Done", value=t["done"], key=f"done_{i}"):
                data["tasks"][today][i]["done"] = True

        with col3:
            if st.button("Delete", key=f"del_{i}"):
                data["tasks"][today].pop(i)
                save_data(data)
                st.rerun()

    save_data(data)
else:
    st.info("No tasks added for today yet.")

# ---------------------------
# Update streak
# ---------------------------
completed_today = all(t["done"] for t in data["tasks"].get(today, [])) if today in data["tasks"] else False
data["streaks"][today] = completed_today
save_data(data)

# ---------------------------
# Streak Chart (Monthly)
# ---------------------------
st.header("📊 Monthly Streak Chart")

if data["streaks"]:
    streak_df = pd.DataFrame(list(data["streaks"].items()), columns=["date", "done"])
    streak_df["date"] = pd.to_datetime(streak_df["date"])
    streak_df["month"] = streak_df["date"].dt.to_period("M")
    monthly_streak = streak_df.groupby("month")["done"].sum().reset_index()

    fig, ax = plt.subplots()
    ax.bar(monthly_streak["month"].astype(str), monthly_streak["done"], color="skyblue")
    ax.set_title("Monthly Completed Days")
    ax.set_xlabel("Month")
    ax.set_ylabel("Days Completed")
    plt.xticks(rotation=45)
    st.pyplot(fig)

    # Calculate current streak
    dates = sorted(data["streaks"].keys())
    current_streak = 0
    for d in reversed(dates):
        if data["streaks"][d]:
            current_streak += 1
        else:
            break
    st.sidebar.markdown(f"🔥 **Current Streak:** {current_streak} days")

# ---------------------------
# Goals Section
# ---------------------------
st.header("🎯 Goals")

goal_type = st.selectbox("Select Goal Segment", ["Weekly", "Monthly", "3 Months", "6 Months"])
goal_text = st.text_input("Enter your goal")

if st.button("Add Goal"):
    key = goal_type.lower().replace(" ", "_")
    if key not in data["goals"]:
        data["goals"][key] = []
    data["goals"][key].append({"goal": goal_text, "done": False})
    save_data(data)
    st.success(f"Goal added to {goal_type} segment!")

# Show Goals
for seg, goals in data["goals"].items():
    st.subheader(f"{seg.capitalize()} Goals")
    if goals:
        done_count = sum(1 for g in goals if g["done"])
        total = len(goals)
        st.write(f"Progress: {done_count}/{total} ({(done_count/total)*100:.0f}%)")

        for i, g in enumerate(goals):
            col1, col2 = st.columns([6, 2])
            with col1:
                if st.checkbox(g["goal"], value=g["done"], key=f"goal_{seg}_{i}"):
                    data["goals"][seg][i]["done"] = True
            with col2:
                if st.button("Delete", key=f"del_goal_{seg}_{i}"):
                    data["goals"][seg].pop(i)
                    save_data(data)
                    st.rerun()
        save_data(data)
    else:
        st.info("No goals added yet.")
