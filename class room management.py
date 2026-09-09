import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Dynamic Student Performance & Analytics Dashboard",
    page_icon="🎓",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. REAL-TIME DYNAMIC DATA INITIALIZATION (SESSION STATE)
# -----------------------------------------------------------------------------
if "students_db" not in st.session_state:
    # Seed data with specified names
    initial_students = [
        {"User ID": "STU001", "Name": "Nira", "Class": "CSE-A", "GPA": 3.92, "Credits": 24, "Attendance": 96, "Project_Score": 95},
        {"User ID": "STU002", "Name": "Sahana", "Class": "CSE-A", "GPA": 3.88, "Credits": 22, "Attendance": 94, "Project_Score": 91},
        {"User ID": "STU003", "Name": "Jeevi", "Class": "CSE-B", "GPA": 3.75, "Credits": 20, "Attendance": 90, "Project_Score": 88},
        {"User ID": "STU004", "Name": "Aishu", "Class": "CSE-A", "GPA": 3.82, "Credits": 22, "Attendance": 92, "Project_Score": 89},
        {"User ID": "STU005", "Name": "Swetha", "Class": "CSE-B", "GPA": 3.95, "Credits": 26, "Attendance": 98, "Project_Score": 97},
        {"User ID": "STU006", "Name": "Badrinath", "Class": "CSE-A", "GPA": 3.65, "Credits": 18, "Attendance": 88, "Project_Score": 84},
        {"User ID": "STU007", "Name": "Bharath", "Class": "CSE-B", "GPA": 3.70, "Credits": 20, "Attendance": 89, "Project_Score": 86},
        {"User ID": "STU008", "Name": "Mani", "Class": "CSE-A", "GPA": 3.58, "Credits": 18, "Attendance": 85, "Project_Score": 80},
        {"User ID": "STU009", "Name": "Srihari", "Class": "CSE-B", "GPA": 3.90, "Credits": 24, "Attendance": 95, "Project_Score": 93},
    ]
    st.session_state.students_db = pd.DataFrame(initial_students)

if "teachers_db" not in st.session_state:
    initial_teachers = [
        {"Teacher ID": "TCH101", "Name": "Dr. Aris", "Subject": "Data Analytics", "Assigned Class": "CSE-A"},
        {"Teacher ID": "TCH102", "Name": "Prof. Raman", "Subject": "Database Systems", "Assigned Class": "CSE-B"},
    ]
    st.session_state.teachers_db = pd.DataFrame(initial_teachers)

# Helper function to recalculate rankings dynamically
def get_processed_data():
    df = st.session_state.students_db.copy()
    df["Composite_Score"] = (df["GPA"] * 20) + (df["Attendance"] * 0.3) + (df["Project_Score"] * 0.5)
    df["Rank"] = df["Composite_Score"].rank(ascending=False, method="min").astype(int)
    return df.sort_values(by="Rank")

df_students = get_processed_data()
df_teachers = st.session_state.teachers_db

# -----------------------------------------------------------------------------
# 3. REAL-TIME TICKER & METRICS BANNER (DEFAULT TOP FLOW)
# -----------------------------------------------------------------------------
st.title("🎓 Student Performance Analytics & Management System")

# Computing top rankers & credit leaders
top_ranker = df_students.iloc[0]
top_credit_student = df_students.sort_values(by="Credits", ascending=False).iloc[0]

# Ticker/Banner Container
st.markdown(
    f"""
    <div style="background-color: #1E293B; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; border-left: 5px solid #3B82F6;">
        <span style="color: #F8FAFC; font-weight: bold; font-size: 16px;">🔥 REAL-TIME HIGHLIGHTS:</span> 
        <span style="color: #60A5FA; margin-left: 15px;">🏆 <b>Top Ranked Student:</b> {top_ranker['Name']} (Rank #{top_ranker['Rank']} | GPA: {top_ranker['GPA']})</span>
        <span style="color: #34D399; margin-left: 25px;">💳 <b>Highest Curriculum Credits:</b> {top_credit_student['Name']} ({top_credit_student['Credits']} Credits)</span>
        <span style="color: #FBBF24; margin-left: 25px;">📊 <b>Class Average GPA:</b> {df_students['GPA'].mean():.2f}</span>
    </div>
    """,
    unsafe_clause=True,
    unsafe_allow_html=True
)

# -----------------------------------------------------------------------------
# 4. ROLE-BASED ACCESS CONTROL (RBAC) SIDEBAR
# -----------------------------------------------------------------------------
st.sidebar.header("🔑 Access Control & Roles")
user_role = st.sidebar.selectbox("Select Active Portal", ["Admin", "Teacher", "Student"])

st.sidebar.markdown("---")

# -----------------------------------------------------------------------------
# 5. DYNAMIC PORTAL IMPLEMENTATIONS
# -----------------------------------------------------------------------------

# --- ADMIN PORTAL ---
if user_role == "Admin":
    st.header("🛠️ Admin Dashboard: Management & Access Control")
    
    tab1, tab2, tab3 = st.tabs(["📊 Global Analytics", "👨‍🏫 Teacher Access Management", "➕ Add New Student/Teacher"])
    
    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Students Registered", len(df_students))
        col2.metric("Total Active Teachers", len(df_teachers))
        col3.metric("Highest Credit Holder", f"{top_credit_student['Name']} ({top_credit_student['Credits']})")
        col4.metric("Top Rank", f"{top_ranker['Name']} (Rank #1)")
        
        st.subheader("Global Student Roster")
        st.dataframe(df_students[["Rank", "User ID", "Name", "Class", "GPA", "Credits", "Attendance", "Project_Score"]], use_container_width=True)

    with tab2:
        st.subheader("Assign & Manage Teacher Access")
        st.dataframe(df_teachers, use_container_width=True)
        
        with st.expander("Update Teacher Assignment"):
            t_select = st.selectbox("Select Teacher", df_teachers["Name"].tolist(), key="admin_t_select")
            new_class = st.text_input("Assign New Class/Section", "CSE-A")
            if st.button("Update Access", key="btn_update_t"):
                st.session_state.teachers_db.loc[st.session_state.teachers_db["Name"] == t_select, "Assigned Class"] = new_class
                st.success(f"Updated access for {t_select} to {new_class}")
                st.rerun()

    with tab3:
        st.subheader("Add New Student Record")
        with st.form("add_student_form"):
            new_id = f"STU00{len(df_students)+1}"
            new_name = st.text_input("Student Name")
            new_class = st.selectbox("Class Section", ["CSE-A", "CSE-B"])
            new_gpa = st.number_input("GPA", 0.0, 4.0, 3.5)
            new_credits = st.number_input("Curriculum Credits", 0, 40, 20)
            new_att = st.number_input("Attendance (%)", 0, 100, 90)
            new_proj = st.number_input("Project Score", 0, 100, 85)
            
            submitted = st.form_submit_button("Add Student")
            if submitted and new_name:
                new_row = {
                    "User ID": new_id, "Name": new_name, "Class": new_class,
                    "GPA": new_gpa, "Credits": new_credits, "Attendance": new_att, "Project_Score": new_proj
                }
                st.session_state.students_db = pd.concat([st.session_state.students_db, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"Added {new_name} dynamically to database!")
                st.rerun()

# --- TEACHER PORTAL ---
elif user_role == "Teacher":
    st.header("👨‍🏫 Teacher Portal: Real-Time Performance Recording")
    
    selected_teacher = st.selectbox("Select Logged-in Teacher", df_teachers["Name"].tolist(), key="t_login")
    assigned_class = df_teachers.loc[df_teachers["Name"] == selected_teacher, "Assigned Class"].values[0]
    
    st.info(f"Welcome **{selected_teacher}**! Assigned Class: **{assigned_class}**")
    
    # Filter students for assigned class
    class_students = df_students[df_students["Class"] == assigned_class]
    
    st.subheader("Record / Update Student Performance")
    
    # Select student dynamically safely
    selected_stu_id = st.selectbox(
        "Select Student to Update",
        options=class_students["User ID"].tolist(),
        format_func=lambda x: f"{x} - {class_students.loc[class_students['User ID'] == x, 'Name'].values[0]}",
        key="teacher_select_student_unique_key"
    )
    
    # Pre-populate dynamic values
    current_student_data = class_students[class_students["User ID"] == selected_stu_id].iloc[0]
    
    with st.form("update_performance_form"):
        col1, col2 = st.columns(2)
        with col1:
            updated_gpa = st.number_input("Update GPA", 0.0, 4.0, float(current_student_data["GPA"]), step=0.01)
            updated_credits = st.number_input("Update Curriculum Credits", 0, 50, int(current_student_data["Credits"]))
        with col2:
            updated_att = st.number_input("Update Attendance (%)", 0, 100, int(current_student_data["Attendance"]))
            updated_proj = st.number_input("Update Project Score", 0, 100, int(current_student_data["Project_Score"]))
            
        update_btn = st.form_submit_button("Save Performance Record")
        if update_btn:
            # Update dynamic Session State database
            st.session_state.students_db.loc[st.session_state.students_db["User ID"] == selected_stu_id, ["GPA", "Credits", "Attendance", "Project_Score"]] = [
                updated_gpa, updated_credits, updated_att, updated_proj
            ]
            st.success(f"Successfully updated real-time records for {current_student_data['Name']}!")
            st.rerun()

# --- STUDENT PORTAL ---
elif user_role == "Student":
    st.header("🎓 Student Self-Service & Progress Portal")
    
    selected_student_name = st.selectbox("Select Student Profile", df_students["Name"].tolist(), key="stu_login")
    student_data = df_students[df_students["Name"] == selected_student_name].iloc[0]
    
    st.markdown(f"### Welcome back, **{student_data['Name']}**!")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall Rank", f"#{student_data['Rank']}")
    c2.metric("GPA", f"{student_data['GPA']} / 4.0")
    c3.metric("Credits Earned", f"{student_data['Credits']}")
    c4.metric("Attendance", f"{student_data['Attendance']}%")

    st.markdown("---")
    st.subheader("Personal Performance vs Class Average")
    
    avg_data = {
        "Metric": ["GPA (x25)", "Attendance (%)", "Project Score (%)", "Credits (x2)"],
        "Your Score": [student_data["GPA"] * 25, student_data["Attendance"], student_data["Project_Score"], student_data["Credits"] * 2],
        "Class Average": [df_students["GPA"].mean() * 25, df_students["Attendance"].mean(), df_students["Project_Score"].mean(), df_students["Credits"].mean() * 2]
    }
    df_compare = pd.DataFrame(avg_data)
    
    fig_comp = px.bar(df_compare, x="Metric", y=["Your Score", "Class Average"], barmode="group", title="Performance Comparison")
    st.plotly_chart(fig_comp, use_container_width=True)

# -----------------------------------------------------------------------------
# 6. DATA ANALYST VISUALIZATION SUITE (VISIBLE ACROSS PORTALS)
# -----------------------------------------------------------------------------
st.markdown("---")
st.header("📈 Data Analyst Visualizations & Insights")

viz_col1, viz_col2 = st.columns(2)

with viz_col1:
    st.subheader("1. Student Rank vs. Curriculum Credits")
    fig_scatter = px.scatter(
        df_students,
        x="Credits",
        y="GPA",
        size="Project_Score",
        color="Class",
        hover_name="Name",
        text="Name",
        title="Credits vs GPA (Bubble Size = Project Score)",
        color_discrete_sequence=px.colors.qualitative.Set1
    )
    fig_scatter.update_traces(textposition='top center')
    st.plotly_chart(fig_scatter, use_container_width=True)

with viz_col2:
    st.subheader("2. Top Performers Leaderboard")
    fig_rank = px.bar(
        df_students.sort_values("Rank"),
        x="Name",
        y="Composite_Score",
        color="Rank",
        text="Rank",
        title="Overall Rank by Composite Score",
        color_continuous_scale="Viridis"
    )
    st.plotly_chart(fig_rank, use_container_width=True)
