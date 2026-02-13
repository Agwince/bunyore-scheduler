import streamlit as st
import pandas as pd
import random
import base64
from collections import defaultdict

# ============================================
# 1. CONFIGURATION & BELL SCHEDULE
# ============================================
st.set_page_config(page_title="Bunyore Smart Scheduler", layout="wide", page_icon="🎓")

# --- BELL TIMES ---
BELL_SCHEDULE = {
    "Lesson 1": "8:00 - 8:40",
    "Lesson 2": "8:40 - 9:20",
    "Lesson 3": "9:30 - 10:10",  
    "Lesson 4": "10:10 - 10:50",
    "Lesson 5": "11:20 - 12:00", 
    "Lesson 6": "12:00 - 12:40",
    "Lesson 7": "1:40 - 2:20",   
    "Lesson 8": "2:20 - 3:00",
    "Lesson 9": "3:00 - 3:40"
}

st.title("🎓 Bunyore Girls High School")
st.markdown("**Smart Scheduling System** | Hybrid CBC & 8-4-4")
st.markdown("---")

# ============================================
# 2. SIDEBAR - INPUT DATA & GRAPH
# ============================================
st.sidebar.header("1. Setup School Data")

# Default Sample Data
default_data = pd.DataFrame([
    {"Teacher": "Tr. Kamau", "Subject": "Maths", "Classes": "1R, 1G, 2B"},
    {"Teacher": "Tr. Wanjiku", "Subject": "English", "Classes": "3R, 3G, 4B"},
    {"Teacher": "Tr. Otieno", "Subject": "Chemistry", "Classes": "2R, 2G, 1B"},
    {"Teacher": "Tr. Alice", "Subject": "History", "Classes": "1R, 2R, 3R"},
    {"Teacher": "Tr. Omondi", "Subject": "Physics", "Classes": "3G, 4B"},
    {"Teacher": "Tr. Sarah", "Subject": "Kiswahili", "Classes": "1G, 2B, 3G"},
    {"Teacher": "Tr. Kevin", "Subject": "CRE", "Classes": "1R, 1G, 1B"},
    {"Teacher": "Tr. Jane", "Subject": "Biology", "Classes": "4B, 3R"},
], columns=["Teacher", "Subject", "Classes"])

# Data Editor
st.sidebar.subheader("Edit Teacher Load")
edited_df = st.data_editor(default_data, num_rows="dynamic")

# --- WORKLOAD GRAPH (Restored!) ---
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Workload Fairness")
workload_data = edited_df.copy()
# Count lessons by splitting commas
workload_data['Lessons'] = workload_data['Classes'].apply(lambda x: len(str(x).split(',')) if x else 0)

# Draw the Chart
st.sidebar.bar_chart(workload_data.set_index('Teacher')['Lessons'])

# Overload Alert
overloaded = workload_data[workload_data['Lessons'] > 25]
if not overloaded.empty:
    st.sidebar.error(f"⚠️ Overload: {', '.join(overloaded['Teacher'].tolist())}")
else:
    st.sidebar.success("✅ Workload Balanced")
# ----------------------------------

# Settings
st.sidebar.header("2. Settings")
streams_input = st.sidebar.text_input("Class Streams", "1R, 1G, 1B, 2R, 2G, 2B, 3R, 3G, 4B")
streams = [s.strip() for s in streams_input.split(',')]
slots_per_day = st.sidebar.slider("Lessons per Day", 5, 9, 9)
days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
times = [f"Lesson {i+1}" for i in range(slots_per_day)]

# ============================================
# 3. THE GENERATOR ENGINE
# ============================================
def generate_timetable(df, streams, days, times):
    schedule = {day: {t: {s: "FREE" for s in streams} for t in times} for day in days}
    teacher_busy = defaultdict(lambda: defaultdict(set))
    
    # Sort by workload (Hardest teachers first) to optimize
    df['Workload'] = df['Classes'].apply(lambda x: len(str(x).split(',')) if x else 0)
    df = df.sort_values('Workload', ascending=False)

    for index, row in df.iterrows():
        teacher = row['Teacher']
        subject = row['Subject']
        if not row['Classes']: continue
        target_classes = [c.strip() for c in str(row['Classes']).split(',')]

        for cls in target_classes:
            if cls not in streams: continue 
            assigned = False
            all_slots = [(d, t) for d in days for t in times]
            random.shuffle(all_slots)

            for day, time in all_slots:
                if schedule[day][time][cls] == "FREE":
                    if teacher not in teacher_busy[day][time]:
                        schedule[day][time][cls] = f"{subject} ({teacher})"
                        teacher_busy[day][time].add(teacher)
                        assigned = True
                        break
    return schedule

# ============================================
# 4. HTML REPORT GENERATOR
# ============================================
def create_styled_html(schedule, mode, target_name, days, times, streams):
    css = """
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; color: #333; }
        .header { text-align: center; border-bottom: 3px solid #b30000; padding-bottom: 10px; margin-bottom: 20px; }
        .header h1 { margin: 0; color: #b30000; font-size: 24px; text-transform: uppercase; }
        .header h2 { margin: 5px 0; color: #555; font-size: 18px; }
        table { border-collapse: collapse; width: 100%; margin-top: 10px; font-size: 12px; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
        th { background-color: #f2f2f2; color: #333; font-weight: bold; }
        .break-row { background-color: #fff3cd; font-weight: bold; color: #856404; text-transform: uppercase; letter-spacing: 2px;}
        .subject { font-weight: bold; color: #004d99; display: block; margin-bottom: 2px;}
        .detail { font-size: 0.9em; color: #666; font-style: italic; }
        .free { color: #ccc; }
        .footer { margin-top: 20px; text-align: center; font-size: 10px; color: #888; border-top: 1px solid #eee; padding-top: 10px;}
    </style>
    """
    
    html = f"<html><head>{css}</head><body>"
    html += f"<div class='header'><h1>Bunyore Girls High School</h1>"
    
    def insert_breaks_if_needed(current_lesson_index, colspan):
        if current_lesson_index == 4:
            return f"<tr class='break-row'><td colspan='{colspan}'>☕ TEA BREAK (10:50 - 11:20)</td></tr>"
        elif current_lesson_index == 6:
            return f"<tr class='break-row'><td colspan='{colspan}'>🍛 LUNCH BREAK (12:40 - 1:40)</td></tr>"
        return ""

    if mode == "Class":
        html += f"<h2>CLASS TIMETABLE: <span style='color:blue'>{target_name}</span></h2></div>"
        html += "<table><tr><th width='15%'>Time</th>"
        for day in days: html += f"<th>{day}</th>"
        html += "</tr>"
        for i, time in enumerate(times):
            html += insert_breaks_if_needed(i, len(days) + 1)
            real_time = BELL_SCHEDULE.get(time, time)
            html += f"<tr><td><b>{real_time}</b><br><span style='font-size:0.8em;color:#999'>{time}</span></td>"
            for day in days:
                cell = schedule[day][time][target_name]
                if cell == "FREE": html += "<td class='free'>-</td>"
                else:
                    subj = cell.split('(')[0]
                    teach = cell.split('(')[1].replace(')', '')
                    html += f"<td><span class='subject'>{subj}</span><span class='detail'>{teach}</span></td>"
            html += "</tr>"
        html += "</table>"

    elif mode == "Teacher":
        html += f"<h2>PERSONAL TIMETABLE: <span style='color:green'>{target_name}</span></h2></div>"
        html += "<table><tr><th width='15%'>Time</th>"
        for day in days: html += f"<th>{day}</th>"
        html += "</tr>"
        for i, time in enumerate(times):
            html += insert_breaks_if_needed(i, len(days) + 1)
            real_time = BELL_SCHEDULE.get(time, time)
            html += f"<tr><td><b>{real_time}</b><br><span style='font-size:0.8em;color:#999'>{time}</span></td>"
            for day in days:
                found_class = "-"
                found_subj = "-"
                for s in streams:
                    cell = schedule[day][time][s]
                    if target_name in cell:
                        found_class = s
                        found_subj = cell.split('(')[0]
                        break
                if found_class == "-": html += "<td class='free'>FREE</td>"
                else: html += f"<td><span class='subject'>{found_class}</span><span class='detail'>{found_subj}</span></td>"
            html += "</tr>"
        html += "</table>"

    elif mode == "Master":
        html += f"<h2>OFFICIAL MASTER TIMETABLE</h2></div>"
        for day in days:
            html += f"<h3>{day}</h3><table><tr><th>Time</th>"
            for s in streams: html += f"<th>{s}</th>"
            html += "</tr>"
            for i, time in enumerate(times):
                html += insert_breaks_if_needed(i, len(streams) + 1)
                real_time = BELL_SCHEDULE.get(time, time)
                html += f"<tr><td><b>{real_time}</b></td>"
                for s in streams:
                    cell = schedule[day][time][s]
                    if cell == "FREE": html += "<td class='free'>-</td>"
                    else:
                        subj = cell.split('(')[0]
                        teach = cell.split('(')[1].replace(')', '')
                        html += f"<td><span class='subject'>{subj}</span><span class='detail'>{teach}</span></td>"
                html += "</tr>"
            html += "</table><br>"

    html += "<div class='footer'>Generated by Bunyore Smart Scheduler | System Developer: Agwince Kagali</div></body></html>"
    return html

# ============================================
# 5. MAIN INTERFACE
# ============================================
if st.button("🚀 Generate Timetable", type="primary"):
    with st.spinner("Calculating..."):
        st.session_state['schedule'] = generate_timetable(edited_df, streams, days, times)
        st.success("Timetable Generated Successfully!")

if 'schedule' in st.session_state:
    schedule = st.session_state['schedule']
    
    st.write("---")
    st.header("📥 Download Center")
    
    download_type = st.radio("Who is this timetable for?", 
                             ["🏫 Class (Student)", "👨‍🏫 Teacher (Personal)", "👑 Headteacher (Master)"], 
                             horizontal=True)

    if "Class" in download_type:
        target = st.selectbox("Select Class:", streams)
        if st.button(f"Generate PDF for {target}"):
            html = create_styled_html(schedule, "Class", target, days, times, streams)
            st.download_button(f"⬇️ Download {target} Timetable", html, f"{target}_Timetable.html", "text/html")

    elif "Teacher" in download_type:
        teacher_list = edited_df['Teacher'].unique().tolist()
        target = st.selectbox("Select Teacher:", teacher_list)
        if st.button(f"Generate PDF for {target}"):
            html = create_styled_html(schedule, "Teacher", target, days, times, streams)
            st.download_button(f"⬇️ Download {target}'s Timetable", html, f"{target}_Timetable.html", "text/html")

    elif "Headteacher" in download_type:
        st.info("This will generate the full Master Schedule for all classes.")
        if st.button("Generate Master File"):
            html = create_styled_html(schedule, "Master", "HEADTEACHER", days, times, streams)
            st.download_button("⬇️ Download Master Timetable", html, "Master_Timetable.html", "text/html")

    st.warning("👉 **Tip:** After downloading, open the file -> Tap Menu -> Share -> Print -> **Save as PDF**.")
