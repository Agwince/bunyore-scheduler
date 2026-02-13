import streamlit as st
import pandas as pd
import random
import base64
from collections import defaultdict

# ============================================
# 1. PAGE CONFIGURATION
# ============================================
st.set_page_config(page_title="Bunyore Smart Scheduler", layout="wide", page_icon="🎓")

st.title("🎓 Bunyore Girls High School")
st.markdown("**Smart Scheduling System** | Hybrid CBC & 8-4-4")
st.markdown("---")

# ============================================
# 2. SIDEBAR - INPUT DATA
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
    # Create the Master Schedule Structure
    schedule = {day: {t: {s: "FREE" for s in streams} for t in times} for day in days}
    teacher_busy = defaultdict(lambda: defaultdict(set))
    
    # Randomize processing order
    df = df.sample(frac=1).reset_index(drop=True)

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
                        # Store as: "Maths (Tr. Kamau)"
                        schedule[day][time][cls] = f"{subject} ({teacher})"
                        teacher_busy[day][time].add(teacher)
                        assigned = True
                        break
    return schedule

# ============================================
# 4. HTML REPORT GENERATOR (The "Pretty" Part)
# ============================================
def create_styled_html(schedule, mode, target_name, days, times, streams):
    # CSS Styling
    css = """
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; color: #333; }
        .header { text-align: center; border-bottom: 3px solid #b30000; padding-bottom: 10px; margin-bottom: 20px; }
        .header h1 { margin: 0; color: #b30000; font-size: 24px; text-transform: uppercase; }
        .header h2 { margin: 5px 0; color: #555; font-size: 18px; }
        table { border-collapse: collapse; width: 100%; margin-top: 10px; font-size: 12px; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
        th { background-color: #f2f2f2; color: #333; font-weight: bold; }
        tr:nth-child(even) { background-color: #fcfcfc; }
        .subject { font-weight: bold; color: #004d99; display: block; margin-bottom: 2px;}
        .detail { font-size: 0.9em; color: #666; font-style: italic; }
        .free { color: #ccc; }
        .footer { margin-top: 20px; text-align: center; font-size: 10px; color: #888; border-top: 1px solid #eee; padding-top: 10px;}
    </style>
    """
    
    html = f"<html><head>{css}</head><body>"
    html += f"<div class='header'><h1>Bunyore Girls High School</h1>"
    
    if mode == "Master":
        html += f"<h2>OFFICIAL MASTER TIMETABLE</h2></div>"
        # Loop through ALL days for Master
        for day in days:
            html += f"<h3>{day}</h3><table><tr><th>Time</th>"
            for s in streams: html += f"<th>{s}</th>"
            html += "</tr>"
            for time in times:
                html += f"<tr><td><b>{time}</b></td>"
                for s in streams:
                    cell = schedule[day][time][s]
                    if cell == "FREE": html += "<td class='free'>-</td>"
                    else:
                        subj = cell.split('(')[0]
                        teach = cell.split('(')[1].replace(')', '')
                        html += f"<td><span class='subject'>{subj}</span><span class='detail'>{teach}</span></td>"
                html += "</tr>"
            html += "</table><br>"

    elif mode == "Class":
        html += f"<h2>CLASS TIMETABLE: <span style='color:blue'>{target_name}</span></h2></div>"
        html += "<table><tr><th>Day</th>"
        for time in times: html += f"<th>{time}</th>"
        html += "</tr>"
        for day in days:
            html += f"<tr><td><b>{day}</b></td>"
            for time in times:
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
        html += "<table><tr><th>Day</th>"
        for time in times: html += f"<th>{time}</th>"
        html += "</tr>"
        for day in days:
            html += f"<tr><td><b>{day}</b></td>"
            for time in times:
                # Find where this teacher is
                found_class = "-"
                found_subj = "-"
                for s in streams:
                    cell = schedule[day][time][s]
                    if target_name in cell: # Check if teacher name is in the cell string
                        found_class = s
                        found_subj = cell.split('(')[0]
                        break
                
                if found_class == "-": html += "<td class='free'>FREE</td>"
                else: html += f"<td><span class='subject'>{found_class}</span><span class='detail'>{found_subj}</span></td>"
            html += "</tr>"
        html += "</table>"

    html += "<div class='footer'>Generated by Bunyore Smart Scheduler | System Developer: Agwince Kagali</div></body></html>"
    return html

# ============================================
# 5. MAIN INTERFACE
# ============================================
if st.button("🚀 Generate Timetable", type="primary"):
    with st.spinner("Calculating..."):
        # We store the schedule in 'session_state' so it doesn't disappear when we click download
        st.session_state['schedule'] = generate_timetable(edited_df, streams, days, times)
        st.success("Timetable Generated Successfully!")

# Check if schedule exists
if 'schedule' in st.session_state:
    schedule = st.session_state['schedule']
    
    st.write("---")
    st.header("📥 Download Center")
    
    # The 3-Way Choice
    download_type = st.radio("Who is this timetable for?", 
                             ["🏫 Class (Student)", "👨‍🏫 Teacher (Personal)", "👑 Headteacher (Master)"], 
                             horizontal=True)

    if "Class" in download_type:
        target = st.selectbox("Select Class:", streams)
        if st.button(f"Generate PDF for {target}"):
            html = create_styled_html(schedule, "Class", target, days, times, streams)
            st.download_button(f"⬇️ Download {target} Timetable", html, f"{target}_Timetable.html", "text/html")

    elif "Teacher" in download_type:
        # Get list of teachers from the dataframe
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
