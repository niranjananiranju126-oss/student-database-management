import streamlit as st
import sqlite3
import bcrypt
import pandas as pd

# ---------------------------------------------------------
# 1. DATABASE CONNECTION & INITIALIZATION (SQLite Cloud-Ready)
# ---------------------------------------------------------
@st.cache_resource
def init_connection():
    """Establishes connection to a local SQLite file database and caches it."""
    # This automatically creates 'classroom.db' inside your GitHub repository folder on execution
    return sqlite3.connect("classroom.db", check_same_thread=False)

try:
    myconnect = init_connection()
    myproj = myconnect.cursor()
    # Enable foreign key constraint support explicitly in SQLite
    myproj.execute("PRAGMA foreign_keys = ON;")
except Exception as e:
    st.error(f"Failed to connect to Database: {e}")
    st.stop()

# Build schema using SQLite specific datatypes
myproj.execute('''CREATE TABLE IF NOT EXISTS student(
    ID TEXT PRIMARY KEY NOT NULL,
    UserName TEXT UNIQUE NOT NULL,
    Password BLOB NOT NULL,
    Role TEXT NOT NULL
)''')

myproj.execute('''CREATE TABLE IF NOT EXISTS grades (
    grade_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    stud_id TEXT NOT NULL,            
    subject TEXT NOT NULL,
    marks INTEGER NOT NULL,
    FOREIGN KEY (stud_id) REFERENCES student(ID) ON DELETE CASCADE
)''')

myproj.execute('''CREATE TABLE IF NOT EXISTS attendence(
    attendence_id INTEGER PRIMARY KEY AUTO_INCREMENT,
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

# Seed baseline data if completely empty
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
    st.title("🏫 Classroom Management System")
    st.subheader("Login to your Account")
    
    with st.form("login_form"):
        username = st.text_input("Username").strip()
        password = st.text_input("Password", type="password").strip()
        submit = st.form_submit_button("Login")
        
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
                        st.error("Invalid password.")
                else:
                    st.error("Username not found.")


def admin_dashboard():
    st.title("🛠️ Admin Dashboard")
    st.write(f"Logged in as: **{st.session_state.username}**")
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["Add User Profile", "Manage Users (View/Delete)", "Database Reset Zone"])
    
    with tab1:
        st.subheader("Create a New User Account")
        with st.form("create_user_form", clear_on_submit=True):
            new_role = st.selectbox("Select Role", ["Teacher", "Student"]).lower()
            new_id = st.text_input("Unique ID (e.g., T02, S02)").strip()
            new_user = st.text_input("Custom Username").strip()
            new_pass = st.text_input("Password", type="password").strip()
            
            submit = st.form_submit_button("Register User")
            
            if submit:
                if not new_id or not new_user or not new_pass:
                    st.error("All fields are required.")
                else:
                    myproj.execute("SELECT * FROM student WHERE ID = ? OR UserName = ?", (new_id, new_user))
                    if myproj.fetchone():
                        st.error("Error: That User ID or Username is already registered.")
                    else:
                        hashed_pass = bcrypt.hashpw(new_pass.encode('utf-8'), bcrypt.gensalt())
                        try:
                            myproj.execute(
                                "INSERT INTO student (ID, UserName, Password, Role) VALUES (?, ?, ?, ?)",
                                (new_id, new_user, hashed_pass, new_role)
                            )
                            myconnect.commit()
                            st.success(f"Successfully registered '{new_user}' as a {new_role.capitalize()}!")
                        except Exception as err:
                            st.error(f"Database Error: {err}")
                            
    with tab2:
        st.subheader("Manage Teacher and Student Accounts")
        
        myproj.execute("SELECT ID, UserName, Role FROM student WHERE Role != 'admin'")
        users = myproj.fetchall()
        
        if users:
            df_users = pd.DataFrame(users, columns=["ID", "Username", "System Role"])
            st.dataframe(df_users, use_container_width=True, hide_index=True)
            
            st.write("### Delete User Profile")
            user_ids = [user[0] for user in users]
            selected_delete_id = st.selectbox("Select User ID to Delete", user_ids)
            
            myproj.execute("SELECT UserName, Role FROM student WHERE ID = ?", (selected_delete_id,))
            tgt_user = myproj.fetchone()
            
            if st.button(f"🗑️ Delete User {selected_delete_id} ({tgt_user[0]})", type="primary"):
                try:
                    myproj.execute("DELETE FROM grades WHERE stud_id = ?", (selected_delete_id,))
                    myproj.execute("DELETE FROM attendence WHERE stud_id = ?", (selected_delete_id,))
                    myproj.execute("DELETE FROM student WHERE ID = ?", (selected_delete_id,))
                    myconnect.commit()
                    st.success(f"User {selected_delete_id} deleted successfully!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Could not drop user: {ex}")
        else:
            st.info("No registered teachers or students found in system.")

    with tab3:
        st.subheader("🚨 Danger Zone")
        st.error("Warning: The action below will purge all transactional tables and drop all student and teacher accounts. Only the administrator profile will be preserved.")
        
        confirm_drop = st.checkbox("I understand that this action is irreversible and I want to purge student and teacher profiles.")
        
        if st.button("Purge Database Records", type="primary", disabled=not confirm_drop):
            try:
                myproj.execute("DELETE FROM grades;")
                myproj.execute("DELETE FROM attendence;")
                myproj.execute("DELETE FROM student WHERE Role != 'admin';")
                myconnect.commit()
                st.success("Database successfully cleared!")
                st.rerun()
            except Exception as ex:
                st.error(f"Failed to drop database records cleanly: {ex}")


def teacher_dashboard():
    st.title("🍎 Teacher Dashboard")
    st.write(f"Welcome, **{st.session_state.username}**")
    
    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["Register Student Details", "Insert Marks", "Record Attendance", "View Classroom Records"])
    
    with tab1:
        st.subheader("Add New Student Details")
        with st.form("teacher_add_student_form", clear_on_submit=True):
            s_id = st.text_input("Student ID (e.g., S02)").strip()
            s_name = st.text_input("Student Username").strip()
            s_pass = st.text_input("Login Password", type="password").strip()
            submit_student = st.form_submit_button("Register Student")
            
            if submit_student:
                if not s_id or not s_name or not s_pass:
                    st.error("All parameters are mandatory.")
                else:
                    myproj.execute("SELECT * FROM student WHERE ID = ? OR UserName = ?", (s_id, s_name))
                    if myproj.fetchone():
                        st.error("Error: That ID or Username is already occupied.")
                    else:
                        hashed_pass = bcrypt.hashpw(s_pass.encode('utf-8'), bcrypt.gensalt())
                        try:
                            myproj.execute(
                                "INSERT INTO student (ID, UserName, Password, Role) VALUES (?, ?, ?, ?)",
                                (s_id, s_name, hashed_pass, "student")
                            )
                            myconnect.commit()
                            st.success(f"Student profile '{s_name}' successfully added!")
                        except Exception as err:
                            st.error(f"Database Error: {err}")

    with tab2:
        st.subheader("Insert Student Marks")
        with st.form("marks_form", clear_on_submit=True):
            stud_id = st.text_input("Student ID").strip()
            subject = st.text_input("Subject").strip()
            marks = st.number_input("Marks", min_value=0, max_value=100, step=1)
            submit_marks = st.form_submit_button("Submit Marks")
            
            if submit_marks:
                myproj.execute("SELECT Role FROM student WHERE ID = ?", (stud_id,))
                stud_check = myproj.fetchone()
                
                if stud_check and stud_check[0] == "student":
                    myproj.execute("INSERT INTO grades (stud_id, subject, marks) VALUES (?, ?, ?)", (stud_id, subject, marks))
                    myconnect.commit()
                    st.success("Marks inserted successfully!")
                else:
                    st.error("Error: Valid Student ID not found.")
                    
    with tab3:
        st.subheader("Record Student Attendance")
        with st.form("attendance_form", clear_on_submit=True):
            stud_id = st.text_input("Student ID", key="att_stud_id").strip()
            date = st.date_input("Select Date").strftime("%d-%m-%Y")
            status = st.radio("Status", ["Present", "Absent"])
            submit_att = st.form_submit_button("Record Attendance")
            
            if submit_att:
                myproj.execute("SELECT Role FROM student WHERE ID = ?", (stud_id,))
                stud_check = myproj.fetchone()
                
                if stud_check and stud_check[0] == "student":
                    myproj.execute("INSERT INTO attendence (stud_id, date, status) VALUES (?, ?, ?)", (stud_id, date, status))
                    myconnect.commit()
                    st.success(f"Attendance recorded for {date}!")
                else:
                    st.error("Error: Valid Student ID not found.")

    with tab4:
        st.subheader("📋 Student Directory & Classroom Records")
        
        st.write("### Student Roster")
        myproj.execute("SELECT ID, UserName FROM student WHERE Role = 'student'")
        students = myproj.fetchall()
        if students:
            st.dataframe(pd.DataFrame(students, columns=["Student ID", "Student Name"]), use_container_width=True, hide_index=True)
        else:
            st.info("No students registered in the system database.")
            
        st.write("### Recorded Marks Log")
        myproj.execute("SELECT s.UserName, g.stud_id, g.subject, g.marks FROM grades g JOIN student s ON g.stud_id = s.ID")
        grades_log = myproj.fetchall()
        if grades_log:
            st.dataframe(pd.DataFrame(grades_log, columns=["Student Name", "Student ID", "Subject", "Marks Assigned"]), use_container_width=True, hide_index=True)
        else:
            st.info("No marks entries recorded yet.")
            
        st.write("### Recorded Attendance Log")
        myproj.execute("SELECT s.UserName, a.stud_id, a.date, a.status FROM attendence a JOIN student s ON a.stud_id = s.ID")
        att_log = myproj.fetchall()
        if att_log:
            st.dataframe(pd.DataFrame(att_log, columns=["Student Name", "Student ID", "Date Roll", "Status Roll"]), use_container_width=True, hide_index=True)
        else:
            st.info("No attendance sheets submitted yet.")


def student_dashboard():
    st.title("🎓 Student Dashboard")
    st.write(f"Welcome back, **{st.session_state.username}** (ID: {st.session_state.user_id})")
    
    st.markdown("---")
    tab1, tab2 = st.tabs(["My Report Card", "My Attendance Summary"])
    
    with tab1:
        st.subheader("Academic Performance")
        myproj.execute("SELECT subject AS 'Subject', marks AS 'Marks' FROM grades WHERE stud_id = ?", (st.session_state.user_id,))
        records = myproj.fetchall()
        if records:
            df = pd.DataFrame(records, columns=["Subject", "Marks"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No marks recorded yet.")
            
    with tab2:
        st.subheader("Attendance Summary")
        myproj.execute(
            "SELECT COUNT(*), SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) FROM attendence WHERE stud_id = ?", 
            (st.session_state.user_id,)
        )
        res = myproj.fetchone()
        if res and res[0] > 0:
            total_days, present_days = res[0], res[1]
            percentage = (present_days / total_days) * 100
            
            col1, col2 = st.columns(2)
            col1.metric("Attendance Percentage", f"{percentage:.2f}%")
            col2.metric("Days Present / Total", f"{present_days} / {total_days}")
        else:
            st.info("No attendance metrics recorded yet.")


# ---------------------------------------------------------
# 4. APP ROUTING ROUTINE
# ---------------------------------------------------------
if not st.session_state.authenticated:
    login_page()
else:
    st.sidebar.title("Navigation")
    st.sidebar.button("Logout", on_click=logout)
    
    if st.session_state.role == "admin":
        admin_dashboard()
    elif st.session_state.role == "teacher":
        teacher_dashboard()
    elif st.session_state.role == "student":
        student_dashboard()
