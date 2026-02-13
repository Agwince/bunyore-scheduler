import streamlit as st
import pandas as pd
import random
import io
import base64
from collections import defaultdict

# ============================================
# 1. PAGE CONFIGURATION
# ============================================
st.set_page_config(page_title="Bunyore Smart Scheduler", layout="wide", page_icon="🎓")

st.title("🎓 Bunyore Girls High School - Smart Scheduler")
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

# Workload Graph
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Workload Fairness")
workload_data = edited_df.copy()
workload_data['Lessons'] = workload_data['Classes'].apply(lambda x: len(str(x).split(',')) if x else 0)
st.sidebar.bar_chart(workload_data.set_index('Teacher')['Lessons'])

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
    
    # Shuffle teachers to ensure randomness
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
                        schedule[day][time][cls] = f"{subject}<br><span style='font-size:0.8em; color:gray'>({teacher})</span>"
                        teacher_busy[day][time].add(teacher)
                        assigned = True
                        break
    return schedule

# Function to create the HTML Report
def create_html_report(timetable_data, day_view):
    # CSS Styling
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            h1 {{ color: #2c3e50; text-align: center; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
            th {{ background-color: #f2f2f2; color: #333; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .subject {{ font-weight: bold; color: #2980b9; }}
            .teacher {{ font-size: 0.85em; color: #7f8c8d; display: block; }}
            .footer {{ margin-top: 30px; text-align: center; font-size: 0.8em; color: #777; }}
        </style>
    </head>
    <body>
        <h1>🎓 Bunyore Girls High School</h1>
        <h3>Master Timetable - {day_view}</h3>
        <table>
            <tr>
                <th>Time Slot</th>
                {''.join(f'<th>{s}</th>' for s in streams)}
            </tr>
    """
    
    for time in times:
        html += f"<tr><td><b>{time}</b></td>"
        for stream in streams:
            cell = timetable_data[day_view][time][stream]
            if cell == "FREE":
                html += "<td style='background-color: #fff5f5;'>-</td>"
            else:
                # Clean up the string for display
                clean_cell = cell.replace('<br>', '</div><div class="teacher">').replace('span', 'span')
                html += f"<td><div class='subject'>{clean_cell}</div></td>"
        html += "</tr>"

    html += """
        </table>
        <div class="footer">Generated by Bunyore Smart Scheduler | System Developer: Agwince Kagali</div>
    </body>
    </html>
    """
    return html

# ============================================
# 4. MAIN INTERFACE
# ============================================
if st.button("🚀 Generate Timetable", type="primary"):
    with st.spinner("Calculating..."):
        timetable_data = generate_timetable(edited_df, streams, days, times)
        st.success("Timetable Generated!")

        # TABS
        tab1, tab2 = st.tabs(["📅 Monday View", "📥 Download Center"])

        with tab1:
            # Display raw dataframe for quick check
            day_df = pd.DataFrame(timetable_data['Mon']).T
            # Simple clean up for display
            st.write(day_df.style.set_properties(**{'text-align': 'center'}))

        with tab2:
            st.header("📥 Download Professional Reports")
            st.write("Select a day to generate a colored HTML report. You can print this to PDF.")
            
            selected_day = st.selectbox("Select Day to Print", days)
            
            # Generate HTML
            html_code = create_html_report(timetable_data, selected_day)
            
            # Download Button
            st.download_button(
                label=f"📄 Download {selected_day} Timetable (Colorful)",
                data=html_code,
                file_name=f"Bunyore_Timetable_{selected_day}.html",
                mime="text/html"
            )
            
            st.info("💡 **Tip:** After downloading, open the file and select **'Share' > 'Print' > 'Save as PDF'** on your phone to get the final PDF file.")
