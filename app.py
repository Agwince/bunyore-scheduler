import streamlit as st
import pandas as pd
import random
import io
from collections import defaultdict

# ============================================
# 1. PAGE CONFIGURATION
# ============================================
st.set_page_config(page_title="Bunyore Smart Scheduler", layout="wide")

st.title("🎓 Bunyore Girls High School - Smart Scheduler")
st.markdown("""
**System Status:** Online | **Mode:** Hybrid (8-4-4 & CBC)
*Upload your teacher data or use the sample data below to generate a conflict-free timetable.*
""")

# ============================================
# 2. SIDEBAR - INPUT DATA & GRAPHS
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

# --- NEW FEATURE: WORKLOAD GRAPH ---
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Workload Fairness Check")

# Calculate workload (Count how many streams each teacher has)
# We create a copy so we don't mess up the main data
workload_data = edited_df.copy()
workload_data['Lessons'] = workload_data['Classes'].apply(lambda x: len(str(x).split(',')) if x else 0)

# Display the Bar Chart
st.sidebar.bar_chart(workload_data.set_index('Teacher')['Lessons'])

# Overload Alert (If a teacher has > 5 classes, show warning)
overloaded = workload_data[workload_data['Lessons'] > 5]
if not overloaded.empty:
    st.sidebar.error(f"⚠️ Overload Alert: {', '.join(overloaded['Teacher'].tolist())} have too many classes!")
else:
    st.sidebar.success("✅ Workload is balanced.")

# --- END NEW FEATURE ---

st.sidebar.header("2. Settings")
streams_input = st.sidebar.text_input("Class Streams (Comma Separated)", "1R, 1G, 1B, 2R, 2G, 2B, 3R, 3G, 4B")
streams = [s.strip() for s in streams_input.split(',')]

slots_per_day = st.sidebar.slider("Lessons per Day", 5, 9, 9)
days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
times = [f"Lesson {i+1}" for i in range(slots_per_day)]

# ============================================
# 3. THE GENERATOR ENGINE
# ============================================
def generate_timetable(df, streams, days, times):
    # Initialize empty schedule
    schedule = {day: {t: {s: "FREE" for s in streams} for t in times} for day in days}
    teacher_busy = defaultdict(lambda: defaultdict(set)) 
    
    # Add workload column for sorting (Hardest teachers first)
    df['Workload'] = df['Classes'].apply(lambda x: len(str(x).split(',')) if x else 0)
    df = df.sort_values('Workload', ascending=False)

    for index, row in df.iterrows():
        teacher = row['Teacher']
        subject = row['Subject']
        if not row['Classes']: continue
        target_classes = [c.strip() for c in str(row['Classes']).split(',')]

        for cls in target_classes:
            if cls not in streams: continue 

            # Attempt to find a slot
            assigned = False
            all_slots = [(d, t) for d in days for t in times]
            random.shuffle(all_slots)

            for day, time in all_slots:
                # Check 1: Is the class free?
                if schedule[day][time][cls] == "FREE":
                    # Check 2: Is the teacher free?
                    if teacher not in teacher_busy[day][time]:
                        # Assign
                        schedule[day][time][cls] = f"{subject}\n({teacher})"
                        teacher_busy[day][time].add(teacher)
                        assigned = True
                        break
            
    return schedule

# ============================================
# 4. MAIN INTERFACE
# ============================================

if st.button("🚀 Generate Timetable", type="primary"):
    with st.spinner("Calculating non-colliding paths..."):
        timetable_data = generate_timetable(edited_df, streams, days, times)
        st.success("Timetable Generated Successfully!")

        tab1, tab2 = st.tabs(["📅 Master Timetable", "🏫 Class Views"])

        with tab1:
            st.write("### Master Schedule (Monday Preview)")
            mon_data = pd.DataFrame(timetable_data['Mon']).T
            st.dataframe(mon_data, use_container_width=True)

        with tab2:
            st.write("### Select a Class to View")
            selected_class = st.selectbox("Choose Class", streams)
            
            class_schedule = []
            for d in days:
                row = {"Day": d}
                for t in times:
                    row[t] = timetable_data[d][t][selected_class]
                class_schedule.append(row)
            
            st.table(pd.DataFrame(class_schedule))

        # ============================================
        # 5. EXCEL DOWNLOADER
        # ============================================
        st.write("---")
        st.header("📥 Downloads")
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Sheet 1: Master Monday
            pd.DataFrame(timetable_data['Mon']).T.to_excel(writer, sheet_name='Monday Master')
            
            # Sheet 2: All Data Flat
            flat_data = []
            for d in days:
                for t in times:
                    for s in streams:
                        entry = timetable_data[d][t][s]
                        if entry != "FREE":
                            flat_data.append({"Day": d, "Time": t, "Class": s, "Lesson": entry})
            pd.DataFrame(flat_data).to_excel(writer, sheet_name='Raw Data')
            
        st.download_button(
            label="Download Timetable as Excel",
            data=output.getvalue(),
            file_name="Bunyore_Smart_Schedule.xlsx",
            mime="application/vnd.ms-excel"
        )
