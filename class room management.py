import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Dynamic Student Performance & Analytics Dashboard",
    page_icon="🎓",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. REAL-TIME DATA INITIALIZATION (SESSION STATE)
# -----------------------------------------------------------------------------
if "students_db" not in st.session_state:
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

# User authentication database
USER_CREDENTIALS = {
    "Admin": {"admin": "admin123"},
    "Teacher": {"aris": "teacher123", "raman": "teacher123"},
    "Student": {"nira": "student123", "sahana": "student123", "jeevi": "student123", "swetha": "student123"}
}

# Session State for Authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None

# Helper calculation
def get_processed_data():
    df = st.session_state.students_db.copy()
    df["Composite_Score"] = (df["GPA"] * 20) + (df["Attendance"] * 0.3) + (df["Project_Score"] * 0.5)
    df["Rank"] = df["Composite_Score"].rank(ascending=False, method="min").astype(int)
    return df.sort_values(by="Rank")

df_students = get_processed_data()
df_teachers = st.session_state.teachers_db

# -----------------------------------------------------------------------------
# 3. LOGIN SYSTEM
# -----------------------------------------------------------------------------
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center;'>🔐 Classroom Portal Login</h1>", unsafe_allow_html=True)
    
    # Motive Banner on Login Page
    st.info("""
    🎯 **PROJECT MOTIVE & OBJECTIVE:**  
    This Data Analytics platform bridges the gap between academic evaluation and real-time data visual insights. 
    It enables teachers to record live academic progress, provides students with transparent rank and credit metrics, 
    and offers administrators continuous data-driven oversight.
    """)

    login_col1, login_col2, login_col3 = st.columns([1, 2, 1])
    
    with login_col2:
        with st.form("login_form"):
            selected_role = st.selectbox("Select Your Portal Role", ["Admin", "Teacher", "Student"])
            input_user = st.text_input("Username").strip().lower()
            input_pass = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Log In")
            
            if submit_login:
                role_creds = USER_CREDENTIALS.get(selected_role, {})
                if input_user in role_creds and role_creds[input_user] == input_pass:
                    st.session_state.authenticated = True
                    st.session_state.username = input_user
                    st.session_state.role = selected_role
                    st.success(f"Welcome back, {input_user.capitalize()}!")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password. Please try again.")

        with st.expander("🔑 View Demo Login Credentials"):
            st.markdown("""
            * **Admin:** Username: `admin` | Password: `admin123`
            * **Teacher:** Username: `aris` or `raman` | Password: `teacher123`
            * **Student:** Username: `nira`, `sahana`, `jeevi`, or `swetha` | Password: `student123`
            """)
    st.stop()  # Stop execution until user logs in

# Logout Button in Sidebar
st.sidebar.markdown(f"**Logged in as:** `{st.session_state.username.capitalize()}` ({st.session_state.role})")
if st.sidebar.button("🚪 Log Out"):
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None
    st.rerun()

# -----------------------------------------------------------------------------
# 4. SYSTEM HEADER & MOTIVE BANNER
# -----------------------------------------------------------------------------
st.title("🎓 Classroom Analytics & Performance System")

# Motive Header Banner
st.markdown(
    """
    <div style="background-color: #0F172A; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 6px solid #8B5CF6;">
        <h4 style="color: #F8FAFC; margin: 0 0 5px 0;">🎯 System Motive & Core Vision</h4>
        <p style="color: #94A3B8; margin: 0; font-size: 14px;">
            Empowering educational institutions with real-time academic tracking, automated merit ranking, 
            and proactive credit visualization to drive student growth and data analytics precision.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Real-time top metrics calculation
top_ranker = df_students.iloc[0]
top_credit_student = df_students.sort_values(by="Credits", ascending=False).iloc[0]

# Real-time Flow Highlights Banner
st.markdown(
    f"""
    <div style="background-color: #1E293B; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; border-left: 5px solid #3B82F6;">
        <span style="color: #F8FAFC; font-weight: bold; font-size: 15px;">🔥 LIVE METRICS FLOW:</span> 
        <span style="color: #60A5FA; margin-left: 15px;">🏆 <b>Top Ranker:</b> {top_ranker['Name']} (Rank #{top_ranker['Rank']} | GPA: {top_ranker['GPA']})</span>
        <span style="color: #34D399; margin-left: 20px;">💳 <b>Highest Credits:</b> {top_credit_student['Name']} ({top_credit_student['Credits']} Credits)</span>
        <span style="color: #FBBF24; margin-left: 20px;">📊 <b>Class Avg GPA:</b> {df_students['GPA'].mean():.2f}</span>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------------------------
# 5. PORTAL VIEWS BASED ON AUTHENTICATED ROLE
# -----------------------------------------------------------------------------
user_role = st.session_state.role

# --- ADMIN PORTAL ---
if user_role == "Admin":
    st.header("🛠️ Admin Portal")
    
    tab1, tab2, tab3 = st.tabs(["📊 Global Analytics", "👨‍🏫 Teacher Access Management", "➕ Add New Record"])
    
    with tab1:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Students", len(df_students))
        c2.metric("Total Teachers", len(df_teachers))
        c3.metric("Top Credit Holder", f"{top_credit_student['Name']} ({top_credit_student['Credits']})")
        c4.metric("Top Ranker", f"{top_ranker['Name']} (Rank #1)")
        
        st.subheader("Global Student Roster")
        st.dataframe(df_students[["Rank", "User ID", "Name", "Class", "GPA", "Credits", "Attendance", "Project_Score"]], use_container_width=True)

    with tab2:
        st.subheader("Manage Teacher Access")
        st.dataframe(df_teachers, use_container_width=True)
        
        with st.expander("Update Teacher Class Assignment"):
            t_select = st.selectbox("Select Teacher", df_teachers["Name"].tolist(), key="admin_t_select")
            new_class = st.text_input("Assign New Class", "CSE-A")
            if st.button("Save Access Rule"):
                st.session_state.teachers_db.loc[st.session_state.teachers_db["Name"] == t_select, "Assigned Class"] = new_class
                st.success(f"Updated access for {t_select} to {new_class}")
                st.rerun()

    with tab3:
        st.subheader("Add Student Record")
        with st.form("add_student_form"):
            new_id = f"STU00{len(df_students)+1}"
            new_name = st.text_input("Student Name")
            new_class = st.selectbox("Class Section", ["CSE-A", "CSE-B"])
            new_gpa = st.number_input("GPA", 0.0, 4.0, 3.5)
            new_credits = st.number_input("Credits", 0, 40, 20)
            new_att = st.number_input("Attendance (%)", 0, 100, 90)
            new_proj = st.number_input("Project Score", 0, 100, 85)
            
            if st.form_submit_button("Register Student") and new_name:
                new_row = {
                    "User ID": new_id, "Name": new_name, "Class": new_class,
                    "GPA": new_gpa, "Credits": new_credits, "Attendance": new_att, "Project_Score": new_proj
                }
                st.session_state.students_db = pd.concat([st.session_state.students_db, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"Added {new_name} dynamically to database!")
                st.rerun()

# --- TEACHER PORTAL ---
elif user_role == "Teacher":
    st.header("👨‍🏫 Teacher Portal")
    
    # Associate logged in teacher
    teacher_name = "Dr. Aris" if st.session_state.username == "aris" else "Prof. Raman"
    assigned_class = df_teachers.loc[df_teachers["Name"] == teacher_name, "Assigned Class"].values[0]
    
    st.info(f"Welcome **{teacher_name}** | Assigned Section: **{assigned_class}**")
    
    class_students = df_students[df_students["Class"] == assigned_class]
    
    st.subheader("Record Student Marks & Attendance")
    
    selected_stu_id = st.selectbox(
        "Select Student",
        options=class_students["User ID"].tolist(),
        format_func=lambda x: f"{x} - {class_students.loc[class_students['User ID'] == x, 'Name'].values[0]}",
        key="teacher_select_student_unique_key"
    )
    
    current_student_data = class_students[class_students["User ID"] == selected_stu_id].iloc[0]
    
    with st.form("update_performance_form"):
        col1, col2 = st.columns(2)
        with col1:
            updated_gpa = st.number_input("GPA", 0.0, 4.0, float(current_student_data["GPA"]), step=0.01)
            updated_credits = st.number_input("Curriculum Credits", 0, 50, int(current_student_data["Credits"]))
        with col2:
            updated_att = st.number_input("Attendance (%)", 0, 100, int(current_student_data["Attendance"]))
            updated_proj = st.number_input("Project Score", 0, 100, int(current_student_data["Project_Score"]))
            
        if st.form_submit_button("Update Student Record"):
            st.session_state.students_db.loc[st.session_state.students_db["User ID"] == selected_stu_id, ["GPA", "Credits", "Attendance", "Project_Score"]] = [
                updated_gpa, updated_credits, updated_att, updated_proj
            ]
            st.success(f"Updated live records for {current_student_data['Name']}!")
            st.rerun()

# --- STUDENT PORTAL ---
elif user_role == "Student":
    st.header("🎓 Student Progress Dashboard")
    
    # Match logged-in student name
    stu_name_map = {"nira": "Nira", "sahana": "Sahana", "jeevi": "Jeevi", "swetha": "Swetha"}
    current_name = stu_name_map.get(st.session_state.username, "Nira")
    
    student_data = df_students[df_students["Name"] == current_name].iloc[0]
    
    st.markdown(f"### Hello, **{student_data['Name']}**!")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall Rank", f"#{student_data['Rank']}")
    c2.metric("GPA", f"{student_data['GPA']} / 4.0")
    c3.metric("Credits Earned", f"{student_data['Credits']}")
    c4.metric("Attendance", f"{student_data['Attendance']}%")

# -----------------------------------------------------------------------------
# 6. DATA VISUALIZATION SUITE
# -----------------------------------------------------------------------------
st.markdown("---")
st.header("📈 Visual Analytics Dashboard")

v1, v2 = st.columns(2)

with v1:
    st.subheader("GPA vs. Curriculum Credits")
    st.scatter_chart(df_students, x="Credits", y="GPA", color="Class", size="Project_Score")

with v2:
    st.subheader("Leaderboard Rankings")
    leaderboard_df = df_students.sort_values("Rank").set_index("Name")[["Composite_Score"]]
    st.bar_chart(leaderboard_df)
