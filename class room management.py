import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set page style and layout
st.set_page_config(page_title="EduConnect: Teacher-Student Portal", layout="wide")

st.title("🤝 EduConnect: Real-Time Teacher-Student Engagement & Feedback Hub")
st.markdown("Building stronger student-teacher rapport through performance analytics and continuous feedback loops.")

# 1. Initialize Mock Database Session State (To mimic a real-time system)
if 'student_db' not in st.session_state:
    st.session_state.student_db = pd.DataFrame([
        {"Roll No": "101", "Name": "Aarav Sharma", "Attendance %": 92, "GPA": 8.8, "Behavior": "Excellent", "Teacher Feedback": "Highly active in discussions. Keep it up!"},
        {"Roll No": "102", "Name": "Isha Patel", "Attendance %": 68, "GPA": 6.5, "Behavior": "Distracted", "Teacher Feedback": "Needs to focus more during practical sessions. Attendance is impacting grades."},
        {"Roll No": "103", "Name": "Rohan Das", "Attendance %": 85, "GPA": 7.9, "Behavior": "Good", "Teacher Feedback": "Consistent performer. Shows great teamwork skills."},
        {"Roll No": "104", "Name": "Ananya Reddy", "Attendance %": 74, "GPA": 6.2, "Behavior": "Passive", "Teacher Feedback": "Quiet in class. Encouraging her to ask more questions during lectures."},
    ])

# Sidebar navigation to switch between Teacher Access and Student View
role = st.sidebar.radio("🔑 Select Portal Access:", ["Teacher Portal", "Student Dashboard"])

# ==================== TEACHER PORTAL ====================
if role == "Teacher Portal":
    st.header("👩‍🏫 Teacher Feedback & Classroom Performance Intake")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 Input New Student Evaluation")
        
        # Dropdown to select student
        student_names = st.session_state.student_db["Name"].tolist()
        selected_student = st.selectbox("Select Student to Evaluate:", student_names)
        
        # Real-time inputs for class performance matrix
        new_attendance = st.slider("Update Attendance %:", 0, 100, int(st.session_state.student_db.loc[st.session_state.student_db["Name"] == selected_student, "Attendance %"].values[0]))
        new_gpa = st.slider("Update Academic GPA (out of 10):", 0.0, 10.0, float(st.session_state.student_db.loc[st.session_state.student_db["Name"] == selected_student, "GPA"].values[0]), step=0.1)
        
        behavior_options = ["Excellent", "Good", "Passive", "Distracted", "Needs Urgent Improvement"]
        current_behavior = st.session_state.student_db.loc[st.session_state.student_db["Name"] == selected_student, "Behavior"].values[0]
        new_behavior = st.selectbox("Classroom Behavior / Engagement Level:", behavior_options, index=behavior_options.index(current_behavior) if current_behavior in behavior_options else 0)
        
        new_feedback = st.text_area("Write Academic Feedback / Remarks:", st.session_state.student_db.loc[st.session_state.student_db["Name"] == selected_student, "Teacher Feedback"].values[0])
        
        if st.button("Submit Feedback & Sync Data"):
            # Update the DataFrame in session state dynamically
            idx = st.session_state.student_db[st.session_state.student_db["Name"] == selected_student].index[0]
            st.session_state.student_db.at[idx, "Attendance %"] = new_attendance
            st.session_state.student_db.at[idx, "GPA"] = new_gpa
            st.session_state.student_db.at[idx, "Behavior"] = new_behavior
            st.session_state.student_db.at[idx, "Teacher Feedback"] = new_feedback
            st.success(f"Successfully updated data and sent live feedback to {selected_student}!")

    with col2:
        st.subheader("📊 Current Classroom Overview")
        st.dataframe(st.session_state.student_db[["Roll No", "Name", "Attendance %", "GPA", "Behavior"]], use_container_width=True)
        
        # Interactive Class Insights
        st.markdown("**Quick Insights for Management:**")
        low_attendance_count = len(st.session_state.student_db[st.session_state.student_db["Attendance %"] < 75])
        st.warning(f"⚠️ There are **{low_attendance_count} student(s)** with attendance below the required 75% threshold.")

# ==================== STUDENT DASHBOARD ====================
else:
    st.header("🎓 Student Performance & Rapport Dashboard")
    
    student_names = st.session_state.student_db["Name"].tolist()
    student_select = st.selectbox("Log in as Student:", student_names)
    
    # Retrieve data for the specific logged-in student
    student_row = st.session_state.student_db[st.session_state.student_db["Name"] == student_select].iloc[0]
    
    # 360 Metric Highlights
    m1, m2, m3 = st.columns(3)
    m1.metric(label="Your Attendance Score", value=f"{student_row['Attendance %']}%", delta="Target: 75%+")
    m2.metric(label="Current Academic GPA", value=f"{student_row['GPA']} / 10")
    m3.metric(label="Classroom Behavior Status", value=student_row['Behavior'])
    
    st.markdown("---")
    
    # Visual Analytics Layout
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("📈 Analytics: Class Trend Comparison")
        
        # Create a visual plot showing where this student stands relative to the class
        fig, ax = plt.subplots(figsize=(6, 3))
        sns.scatterplot(
            data=st.session_state.student_db, 
            x="Attendance %", 
            y="GPA", 
            hue="Behavior", 
            s=150, 
            ax=ax
        )
        
        # Highlight the current logged-in student on the graph
        ax.scatter(
            student_row["Attendance %"], 
            student_row["GPA"], 
            color='red', 
            s=250, 
            edgecolors='black', 
            linewidth=2, 
            label="You"
        )
        ax.set_title("How Attendance Directly Impacts Grades")
        ax.set_xlim(50, 100)
        ax.set_ylim(0, 10)
        ax.grid(True, linestyle="--", alpha=0.5)
        st.pyplot(fig)
        
    with col_right:
        st.subheader("💬 Teacher's Personal Feedback")
        st.info(f'"{student_row["Teacher Feedback"]}"')
        
        # Actionable advice tool to build better rapport
        st.markdown("**💡 Steps to Build Better Rapport:**")
        if student_row["Attendance %"] < 75:
            st.write("❌ Schedule an office hours meet with your teacher to explain your recent attendance gap.")
        if student_row["Behavior"] in ["Distracted", "Passive"]:
            st.write("🙋‍♂️ Try interacting at least once next lecture by asking or answering a question.")
        else:
            st.write("✨ Excellent job! Offer peer-to-peer tutoring to classmates to boost leadership metrics.")
