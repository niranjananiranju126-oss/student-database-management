import streamlit as st
import sqlite3
import bcrypt
import pandas as pd
import numpy as np
from datetime import datetime

# Page Configuration for high-density analytical dashboard layouts
st.set_page_config(page_title="Analytics Classroom Hub", layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------
# 1. DATABASE CONNECTION & INITIALIZATION
# ---------------------------------------------------------
@st.cache_resource
def init_connection():
    return sqlite3.connect("classroom.db", check_same_thread=False)

try:
    myconnect = init_connection()
    myproj = myconnect.cursor()
    myproj.execute("PRAGMA foreign_keys = ON;")
except Exception as e:
    st.error(f"Failed to connect to Database: {e}")
    st.stop()

# Build schema
myproj.execute('''CREATE TABLE IF NOT EXISTS student(
    ID TEXT PRIMARY KEY NOT NULL,
    UserName TEXT UNIQUE NOT NULL,
    Password BLOB NOT NULL,
    Role TEXT NOT NULL
)''')

myproj.execute('''CREATE TABLE IF NOT EXISTS grades (
    grade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stud_id TEXT NOT NULL,            
    subject TEXT NOT NULL,
    marks INTEGER NOT NULL,
    FOREIGN KEY (stud_id) REFERENCES student(ID) ON DELETE CASCADE
)''')

myproj.execute('''CREATE TABLE IF NOT EXISTS attendence(
    attendence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stud_id TEXT,
    date TEXT,
    status TEXT NOT NULL,
    FOREIGN KEY (stud_id) REFERENCES student(ID) ON DELETE CASCADE
)''')
myconnect.commit()

# Seed Admin account if missing
myproj.execute("SELECT COUNT(*) FROM student WHERE Role = 'admin'")
if myproj.fetchone()[0] == 0:
    hasha = bcrypt.hashpw(b"admin123", bcrypt.gensalt())
    myproj.execute("INSERT INTO student(ID, UserName, Password, Role) VALUES (?, ?, ?, ?)", ("A01", "admin", hasha, "admin"))
    myconnect.commit()

# Seed baseline data if empty
myproj.execute("SELECT COUNT(*) FROM student")
if myproj.fetchone()[0] <= 1:
    hasht = bcrypt.hashpw(b"teacher123", bcrypt.gensalt())
    myproj.execute("INSERT INTO student(ID, UserName, Password, Role) VALUES (?, ?, ?, ?)", ("T01", "niranjana", hasht, "teacher"))
    hashs = bcrypt.hashpw(b"student\\123", bcrypt.gensalt())
    myproj.execute("INSERT INTO student(ID, UserName, Password, Role) VALUES (?, ?, ?, ?)", ("S01", "nira", hashs, "student"))
    myconnect.commit()


# ---------------------------------------------------------
# 2. SESSION STATE MANAGEMENT
# ---------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.role = None

def logout():
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.role = None
    st.rerun()


# ---------------------------------------------------------
# 3. INTERFACE VIEWS (DASHBOARDS)
# ---------------------------------------------------------

def login_page():
    st.title("🏫 Classroom Analytics Workspace")
    st.markdown("Enter credentials to open your environment.")
    
    c1, _ = st.columns([1.5, 2])
    with c1:
        with st.form("login_form", clear_on_submit=False):
            st.subheader("Sign In")
            username = st.text_input("Username").strip()
            password = st.text_input("Password", type="password").strip()
            submit = st.form_submit_button("Launch Environment", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    myproj.execute("SELECT ID, Password, Role FROM student WHERE UserName = ?", (username,))
                    user_record = myproj.fetchone()
                    
                    if user_record:
                        user_id, hashed_password, role = user_record
                        if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
                            st.session_state.authenticated = True
                            st.session_state.user_id = user_id
                            st.session_state.username = username
                            st.session_state.role = role
                            st.success("Login Successful!")
                            st.rerun()
                        else:
                            st.error("Invalid password entry.")
                    else:
                        st.error("Username profile not located.")


def admin_dashboard():
    st.title("🛠️ System Control Panel")
    st.caption(f"Authenticated Identity: **{st.session_state.username}** (System Admin)")
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["➕ Provision User", "⚙️ Account Directory", "🚨 Advanced Reset"])
    
    with tab1:
        st.subheader("Create a New Account Profile")
        with st.form("create_user_form", clear_on_submit=True):
            c_left, c_right = st.columns(2)
            new_role = c_left.selectbox("Assigned System Access Role", ["Teacher", "Student"]).lower()
            new_id = c_right.text_input("Unique Institutional ID (e.g., T02, S02)").strip()
            new_user = c_left.text_input("Unique System Username").strip()
            new_pass = c_right.text_input("Initial Temporary Password", type="password").strip()
            submit = st.form_submit_button("Commit & Provision Account")
            
            if submit:
                if not new_id or not new_user or not new_pass:
                    st.error("All credential attributes must be assigned.")
                else:
                    myproj.execute("SELECT * FROM student WHERE ID = ? OR UserName = ?", (new_id, new_user))
                    if myproj.fetchone():
                        st.error("A profile already contains that target ID or Username.")
                    else:
                        hashed_pass = bcrypt.hashpw(new_pass.encode('utf-8'), bcrypt.gensalt())
                        try:
                            myproj.execute(
                                "INSERT INTO student (ID, UserName, Password, Role) VALUES (?, ?, ?, ?)",
                                (new_id, new_user, hashed_pass, new_role)
                            )
                            myconnect.commit()
                            st.success(f"Successfully provisioned account for '{new_user}'!")
                        except Exception as err:
                            st.error(f"Database Write Failure: {err}")
                            
    with tab2:
        st.subheader("Account Management Directory")
        myproj.execute("SELECT ID, UserName, Role FROM student WHERE Role != 'admin'")
        users = myproj.fetchall()
        
        if users:
            df_users = pd.DataFrame(users, columns=["Account ID", "Username ID", "Assigned Role"])
            st.dataframe(df_users, use_container_width=True, hide_index=True)
            
            st.markdown("#### Delete Account Record")
            user_ids = [user[0] for user in users]
            selected_delete_id = st.selectbox("Select Target ID to Remove", user_ids)
            
            myproj.execute("SELECT UserName, Role FROM student WHERE ID = ?", (selected_delete_id,))
            tgt_user = myproj.fetchone()
            
            if st.button(f"🗑️ Terminate Profile {selected_delete_id} ({tgt_user[0]})", type="primary"):
                try:
                    myproj.execute("DELETE FROM grades WHERE stud_id = ?", (selected_delete_id,))
                    myproj.execute("DELETE FROM attendence WHERE stud_id = ?", (selected_delete_id,))
                    myproj.execute("DELETE FROM student WHERE ID = ?", (selected_delete_id,))
                    myconnect.commit()
                    st.success(f"Profile {selected_delete_id} scrubbed from records.")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Action blocked: {ex}")
        else:
            st.info("No active teacher or student credentials recorded in the system database.")

    with tab3:
        st.subheader("System Cold Reset")
        st.warning("Executing this sequence purges all academic records, attendance spreadsheets, and custom accounts.")
        confirm_drop = st.checkbox("I verify this cold reset is required.")
        
        if st.button("Purge Academic Records completely", type="primary", disabled=not confirm_drop):
            try:
                myproj.execute("DELETE FROM grades;")
                myproj.execute("DELETE FROM attendence;")
                myproj.execute("DELETE FROM student WHERE Role != 'admin';")
                myconnect.commit()
                st.success("System databases successfully refreshed.")
                st.rerun()
            except Exception as ex:
                st.error(f"Reset engine failure: {ex}")


def teacher_dashboard():
    st.title("🍎 Faculty Analytics Command Center")
    st.markdown(f"User: **{st.session_state.username}** | Role: **Faculty Analyst**")
    
    # Pre-fetch list of active students
    myproj.execute("SELECT ID, UserName FROM student WHERE Role = 'student'")
    students_list = myproj.fetchall()
    
    # ---------------------------------------------------------
    # GLOBAL METRIC CACHING FOR EXPLORATORY ANALSYS
    # ---------------------------------------------------------
    myproj.execute("SELECT s.UserName, g.stud_id, g.subject, g.marks FROM grades g JOIN student s ON g.stud_id = s.ID")
    raw_grades_data = myproj.fetchall()
    df_grades = pd.DataFrame(raw_grades_data, columns=["Name", "Student_ID", "Subject", "Score"]) if raw_grades_data else pd.DataFrame()
    
    myproj.execute("SELECT s.UserName, a.stud_id, a.date, a.status FROM attendence a JOIN student s ON a.stud_id = s.ID")
    raw_attendance_data = myproj.fetchall()
    df_attendance = pd.DataFrame(raw_attendance_data, columns=["Name", "Student_ID", "Date", "Status"]) if raw_attendance_data else pd.DataFrame()

    # Dynamic Top Insight Metric Overview row using Pandas engine calculations
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sample Population (N)", f"{len(students_list)} Students")
    
    if not df_grades.empty:
        m2.metric("Cohort Class Average", f"{df_grades['Score'].mean():.1f}%")
        m3.metric("Grade Std Deviation (σ)", f"{df_grades['Score'].std():.2f}")
    else:
        m2.metric("Cohort Class Average", "No Data")
        m3.metric("Grade Std Deviation (σ)", "No Data")
        
    if not df_attendance.empty:
        total_records = len(df_attendance)
        present_records = len(df_attendance[df_attendance["Status"] == "Present"])
        m4.metric("Global Attendance Rate", f"{(present_records/total_records)*100:.1f}%")
    else:
        m4.metric("Global Attendance Rate", "No Data")
        
    st.markdown("---")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Data Analytics Engine", "📅 Check Attendance", "📝 Log Marks", "📋 Roster Records", "🆕 Add Student Profile"])
    
    with tab1:
        st.subheader("📊 Exploratory Data Analysis & Export Sandbox")
        st.markdown("Use this environment to inspect distributions, slice feature tables, or export CSV packages for out-of-app scripts.")
        
        c_an1, c_an2 = st.columns(2)
        
        with c_an1:
            st.markdown("#### Course Descriptive Analytics")
            if df_grades.empty:
                st.info("Log scores to activate descriptive summary matrix tables.")
            else:
                st.dataframe(df_grades.describe(), use_container_width=True)
                
                # Dynamic Subject Distribution Aggregates
                subject_aggs = df_grades.groupby("Subject")["Score"].agg(["count", "mean", "min", "max"]).reset_index()
                st.markdown("#### Subject Strata Breakdown Summary")
                st.dataframe(subject_aggs, use_container_width=True, hide_index=True)
                
        with c_an2:
            st.markdown("#### Data Pipeline Export Targets")
            st.caption("Extract application state parameters down directly to working analytical directories.")
            
            if not df_grades.empty:
                csv_grades = df_grades.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export Clean Grades Dataset (CSV)",
                    data=csv_grades,
                    file_name="classroom_grades_dataset.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.button("📥 Grades Dataset Empty", disabled=True, use_container_width=True)
                
            if not df_attendance.empty:
                csv_att = df_attendance.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export Clean Attendance Dataset (CSV)",
                    data=csv_att,
                    file_name="classroom_attendance_dataset.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.button("📥 Attendance Dataset Empty", disabled=True, use_container_width=True)
                
            # Streamlit built-in line/bar analytical distribution plots
            if not df_grades.empty:
                st.markdown("#### Performance Metric Chart Profile")
                chart_target = df_grades.groupby("Subject")["Score"].mean()
                st.bar_chart(chart_target)

    with tab2:
        st.subheader("Instant Attendance Entry Grid")
        session_date = st.date_input("Target Session Date", value=datetime.today()).strftime("%d-%m-%Y")
        
        if not students_list:
            st.info("No registered student profiles available.")
        else:
            h1, h2, h3 = st.columns([2, 1, 1])
            h1.markdown("**Student Full Name**")
            h2.markdown("**Status Option A**")
            h3.markdown("**Status Option B**")
            st.markdown("---")
            
            for stud_id, username in students_list:
                row_col1, row_col2, row_col3 = st.columns([2, 1, 1])
                row_col1.write(f"👤 **{username}** (ID: `{stud_id}`)")
                
                if row_col2.button("✅ Mark Present", key=f"pres_{stud_id}", use_container_width=True):
                    myproj.execute("INSERT INTO attendence (stud_id, date, status) VALUES (?, ?, ?)", (stud_id, session_date, "Present"))
                    myconnect.commit()
                    st.toast(f"{username} logged Present!", icon="✅")
                    st.mini_rerun() if hasattr(st, "mini_rerun") else st.rerun()
                    
                if row_col3.button("❌ Mark Absent", key=f"abs_{stud_id}", use_container_width=True):
                    myproj.execute("INSERT INTO attendence (stud_id, date, status) VALUES (?, ?, ?)", (stud_id, session_date, "Absent"))
                    myconnect.commit()
                    st.toast(f"{username} logged Absent!", icon="❌")
                    st.mini_rerun() if hasattr(st, "mini_rerun") else st.rerun()
                    
    with tab3:
        st.subheader("Log Academic Evaluations")
        if not students_list:
            st.info("Please register a student profile to allocate evaluation marks.")
        else:
            student_options = {f"{name} (ID: {sid})": sid for sid, name in students_list}
            
            with st.form("marks_form", clear_on_submit=True):
                c_in1, c_in2 = st.columns(2)
                selected_student_label = c_in1.selectbox("Target Student Account", options=list(student_options.keys()))
                target_stud_id = student_options[selected_student_label]
                
                subject = c_in2.selectbox("Academic Subject Course", ["Mathematics", "Science", "English", "History", "Computer Science"])
                marks = st.number_input("Earned Performance Score (0-100)", min_value=0, max_value=100, step=1, value=80)
                submit_marks = st.form_submit_button("Commit Evaluation Mark")
                
                if submit_marks:
                    try:
                        myproj.execute("INSERT INTO grades (stud_id, subject, marks) VALUES (?, ?, ?)", (target_stud_id, subject, marks))
                        myconnect.commit()
                        st.success(f"Successfully recorded a grade of **{marks}** in **{subject}**!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Database insertion error: {err}")
                        
    with tab4:
        st.subheader("Raw Storage Source Records (SQL View)")
        sub_tab1, sub_tab2 = st.tabs(["Performance Log Book Table", "Attendance History Sheet Table"])
        
        with sub_tab1:
            if not df_grades.empty:
                st.dataframe(df_grades, use_container_width=True, hide_index=True)
            else:
                st.info("No recorded grades logged in the evaluation matrix yet.")
                
        with sub_tab2:
            if not df_attendance.empty:
                st.dataframe(df_attendance, use_container_width=True, hide_index=True)
            else:
                st.info("No attendance tracking data captured for any session yet.")

    with tab5:
        st.subheader("Register a Student Account Profile")
        with st.form("teacher_add_student_form", clear_on_submit=True):
            cx1, cx2 = st.columns(2)
            s_id = cx1.text_input("Assign Unique Student ID (e.g., S02)").strip()
            s_name = cx2.text_input("Create Login Username").strip()
            s_pass = st.text_input("Create Access Password", type="password").strip()
            submit_student = st.form_submit_button("Register New Student Record")
            
            if submit_student:
                if not s_id or not s_name or not s_pass:
                    st.error("All parameters are required to generate a student card.")
                else:
                    myproj.execute("SELECT * FROM student WHERE ID = ? OR UserName = ?", (s_id, s_name))
                    if myproj.fetchone():
                        st.error("This specific Student ID or Username is already allocated.")
                    else:
                        hashed_pass = bcrypt.hashpw(s_pass.encode('utf-8'), bcrypt.gensalt())
                        try:
                            myproj.execute(
                                "INSERT INTO student (ID, UserName, Password, Role) VALUES (?, ?, ?, ?)",
                                (s_id, s_name, hashed_pass, "student")
                            )
                            myconnect.commit()
                            st.success(f"Account for student '{s_name}' initialized.")
                            st.rerun()
                        except Exception as err:
                            st.error(f"Critical entry failure: {err}")


def student_dashboard():
    st.title("🎓 Personal Analytics Workspace")
    st.markdown(f"Student: **{st.session_state.username}** | Terminal ID: `{st.session_state.user_id}`")
    
    # Pre-fetch personal data rows
    myproj.execute("SELECT subject, marks FROM grades WHERE stud_id = ?", (st.session_state.user_id,))
    raw_personal_grades = myproj.fetchall()
    df_p_grades = pd.DataFrame(raw_personal_grades, columns=["Subject", "Score"]) if raw_personal_grades else pd.DataFrame()
    
    myproj.execute("SELECT date, status FROM attendence WHERE stud_id = ?", (st.session_state.user_id,))
    raw_personal_att = myproj.fetchall()
    df_p_att = pd.DataFrame(raw_personal_att, columns=["Date", "Status"]) if raw_personal_att else pd.DataFrame()

    # Dynamic Student Metric Summary Block
    kpi1, kpi2, kpi3 = st.columns(3)
    
    if not df_p_grades.empty:
        kpi1.metric("Personal GPA / Mean", f"{df_p_grades['Score'].mean():.1f}%")
        kpi2.metric("Evaluations Logged", f"{len(df_p_grades)} Tests")
    else:
        kpi1.metric("Personal GPA / Mean", "No Grades")
        kpi2.metric("Evaluations Logged", "0 Tests")
        
    if not df_p_att.empty:
        tot = len(df_p_att)
        pres = len(df_p_att[df_p_att["Status"] == "Present"])
        kpi3.metric("Your Attendance Frequency", f"{(pres/tot)*100:.1f}%")
    else:
        kpi3.metric("Your Attendance Frequency", "No Data")
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["📊 Personal Report Card", "📅 Attendance Matrix Summary", "🔬 Local Analytics View"])
    
    with tab1:
        st.subheader("Your Academic Term Evaluations")
        if not df_p_grades.empty:
            st.dataframe(df_p_grades, use_container_width=True, hide_index=True)
        else:
            st.info("No course evaluations have been logged to your profile matrix yet.")
            
    with tab2:
        st.subheader("Your Attendance History Dashboard")
        if not df_p_att.empty:
            st.dataframe(df_p_att, use_container_width=True, hide_index=True)
        else:
            st.info("No attendance log information matching your profile credentials located yet.")
            
    with tab3:
        st.subheader("🔬 Local Feature Table Inspection")
        st.markdown("Review descriptive statistics and metrics calculated from your personal account row vectors.")
        
        if df_p_grades.empty:
            st.info("Analytical data summaries will populate once grades are logged into the system.")
        else:
            c_st1, c_st2 = st.columns(2)
            with c_st1:
                st.markdown("**Your Internal Metrics Summary**")
                st.dataframe(df_p_grades.describe(), use_container_width=True)
            with c_st2:
                st.markdown("**Your Subject Performance Distribution**")
                st.bar_chart(df_p_grades.set_index("Subject"))


# ---------------------------------------------------------
# 4. APP ROUTING ROUTINE
# ---------------------------------------------------------
if not st.session_state.authenticated:
    login_page()
else:
    # Sidebar Role Indicator styling configuration blocks
    if st.session_state.role == "teacher":
        st.sidebar.markdown(
            "<div style='background-color:#fff3cd; padding:12px; border-radius:6px; border-left: 5px solid #ffc107; color:#856404; font-weight:bold; margin-bottom:15px;'>Operating Workspace:<br>🍎 Faculty Controller Mode</div>", 
            unsafe_allow_html=True
        )
    elif st.session_state.role == "student":
        st.sidebar.markdown(
            "<div style='background-color:#d1ecf1; padding:12px; border-radius:6px; border-left: 5px solid #17a2b8; color:#0c5460; font-weight:bold; margin-bottom:15px;'>Operating Workspace:<br>🎓 Student Terminal Mode</div>", 
            unsafe_allow_html=True
        )
    elif st.session_state.role == "admin":
        st.sidebar.markdown(
            "<div style='background-color:#f8d7da; padding:12px; border-radius:6px; border-left: 5px solid #dc3545; color:#721c24; font-weight:bold; margin-bottom:15px;'>Operating Workspace:<br>🛠️ Administrator Panel</div>", 
            unsafe_allow_html=True
        )
        
    st.sidebar.write(f"Logged Identity: **{st.session_state.username}**")
    st.sidebar.button("Secure Account Sign Out", on_click=logout, use_container_width=True, type="secondary")
    
    if st.session_state.role == "admin":
        admin_dashboard()
    elif st.session_state.role == "teacher":
        teacher_dashboard()
    elif st.session_state.role == "student":
        student_dashboard()
