import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="EduSphere Multi-Role Portal", layout="wide")

# =========================================================================
# 1. SQLITE DATABASE INITIALIZATION (Prevents duplicates on refresh)
# =========================================================================
def init_db():
    conn = sqlite3.connect("edusphere.db")
    cursor = conn.cursor()
    
    # Create Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT NOT NULL,
            class TEXT
        )
    """)
    
    # Create Academic Records Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS academic_records (
            student_id TEXT PRIMARY KEY,
            class TEXT NOT NULL,
            total_days INTEGER DEFAULT 40,
            days_present INTEGER DEFAULT 40,
            attendance_pct REAL DEFAULT 100.0,
            quiz_1 INTEGER DEFAULT 0,
            quiz_2 INTEGER DEFAULT 0,
            feedback TEXT,
            FOREIGN KEY (student_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    
    # Inject Initial Seed Data safely (Only if tables are empty to avoid duplicates)
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        initial_users = [
            ("admin", "admin123", "Admin", "System Director", "Global"),
            ("T101", "password123", "Teacher", "Prof. Aris", "Class-A"),
            ("T102", "password123", "Teacher", "Dr. Meera", "Class-B"),
            ("S101", "student123", "Student", "Aarav Sharma", "Class-A"),
            ("S102", "student123", "Student", "Isha Patel", "Class-A")
        ]
        cursor.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?)", initial_users)
        
        initial_records = [
            ("S101", "Class-A", 40, 37, 92.5, 85, 90, "Excellent participation."),
            ("S102", "Class-A", 40, 26, 65.0, 55, 60, "Needs to improve regular attendance.")
        ]
        cursor.executemany("INSERT INTO academic_records VALUES (?, ?, ?, ?, ?, ?, ?, ?)", initial_records)
        
    conn.commit()
    conn.close()

init_db()

# Helper function to get a quick database connection
def get_db_connection():
    return sqlite3.connect("edusphere.db")

# Track login session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_role = None

# =========================================================================
# 2. AUTHENTICATION / LOGIN SYSTEM
# =========================================================================
if not st.session_state.logged_in:
    st.title("🛡️ EduSphere Management Portal")
    st.subheader("Real-Time SQL-Backed Admin, Faculty, & Student Login Hub")
    
    with st.form("login_form"):
        uid = st.text_input("Enter Unique ID (Admin / T-series / S-series):").strip()
        pwd = st.text_input("Password:", type="password")
        submit = st.form_submit_button("Authenticate Securely")
        
        if submit:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT password, role FROM users WHERE user_id = ?", (uid,))
            user = cursor.fetchone()
            conn.close()
            
            if user and user[0] == pwd:
                st.session_state.logged_in = True
                st.session_state.user_id = uid
                st.session_state.user_role = user[1]
                st.rerun()
            else:
                st.error("Invalid credentials. Please verify your ID or Password.")
    st.stop()

# Fetch current logged-in user profile details from SQL
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("SELECT name, class FROM users WHERE user_id = ?", (st.session_state.user_id,))
user_profile = cursor.fetchone()
conn.close()

st.sidebar.title(f"👤 Welcome, {user_profile[0]}")
st.sidebar.write(f"**Role Access Level:** {st.session_state.user_role}")
if st.sidebar.button("Secure Logout"):
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_role = None
    st.rerun()

# =========================================================================
# 3. ADMINISTRATIVE WORKFLOW (SQL BASED)
# =========================================================================
if st.session_state.user_role == "Admin":
    st.title("⚙️ Global Administrative Control Dashboard")
    st.write("Generate user profiles, modify dynamic records, and manage access parameters via SQL database execution.")
    
    st.subheader("📋 Core Infrastructure User Matrix (Live SQL Data)")
    conn = get_db_connection()
    df_users = pd.read_sql_query("SELECT user_id AS 'User ID', name AS 'Name', role AS 'Role Access', class AS 'Assigned Room' FROM users", conn)
    conn.close()
    st.dataframe(df_users, use_container_width=True)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("➕ Provision New System Access")
        new_role = st.selectbox("Assign System Role Profile:", ["Teacher", "Student"])
        
        id_prefix = "T" if new_role == "Teacher" else "S"
        new_num = st.text_input(f"Enter Account Unique Reference Number ({id_prefix}xxxx):", placeholder="e.g., 103", key="create_num")
        full_id = f"{id_prefix}{new_num}" if new_num else ""
        
        new_name = st.text_input("Enter Account User Full Name:", key="create_name")
        new_pass = st.text_input("Set Initial Account Default Password:", type="password", key="create_pass")
        assigned_class = st.selectbox("Assign Primary Class Section Mapping:", ["Class-A", "Class-B", "Class-C"], key="create_class")
        
        if st.button("Generate & Register Credentials"):
            if not new_num or not new_name or not new_pass:
                st.error("All account credential fields must be properly populated.")
            else:
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (full_id, new_pass, new_role, new_name, assigned_class))
                    if new_role == "Student":
                        cursor.execute("INSERT INTO academic_records VALUES (?, ?, 40, 40, 100.0, 0, 0, 'Account opened.')", (full_id, assigned_class))
                    conn.commit()
                    st.success(f"Successfully configured active SQL production profile for {full_id}")
                    conn.close()
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error(f"User identity handle {full_id} already exists within SQL database keys.")
                    conn.close()

    with col2:
        st.subheader("🛠️ Data Modification & Record Removal Panel")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id != 'admin'")
        updatable_users = [row[0] for row in cursor.fetchall()]
        
        if not updatable_users:
            st.info("No active teacher or student profiles found in database.")
            conn.close()
        else:
            target_uid = st.selectbox("Select Target User ID to Manage:", updatable_users)
            cursor.execute("SELECT role, class, name, password FROM users WHERE user_id = ?", (target_uid,))
            current_profile = cursor.fetchone()
            conn.close()
            
            st.markdown(f"**Current Role:** {current_profile[0]} | **Assigned Room:** {current_profile[1]}")
            
            mod_name = st.text_input("Modify Account Full Name:", value=current_profile[2])
            mod_pass = st.text_input("Modify Account Password Access:", value=current_profile[3], type="password")
            mod_class = st.selectbox("Modify Room Assignment Mapping:", ["Class-A", "Class-B", "Class-C"], index=["Class-A", "Class-B", "Class-C"].index(current_profile[1] if current_profile[1] in ["Class-A", "Class-B", "Class-C"] else "Class-A"))
            
            m_col1, m_col2 = st.columns(2)
            if m_col1.button("💾 Apply Modifications", use_container_width=True):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET name = ?, password = ?, class = ? WHERE user_id = ?", (mod_name, mod_pass, mod_class, target_uid))
                if current_profile[0] == "Student":
                    cursor.execute("UPDATE academic_records SET class = ? WHERE student_id = ?", (mod_class, target_uid))
                conn.commit()
                conn.close()
                st.success(f"Successfully saved SQL modifications for {target_uid}.")
                st.rerun()
                    
            if m_col2.button("🗑️ Permanent Record Purge", type="primary", use_container_width=True):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE user_id = ?", (target_uid,))
                cursor.execute("DELETE FROM academic_records WHERE student_id = ?", (target_uid,))
                conn.commit()
                conn.close()
                st.warning(f"Profile and SQL footprints purged for handle {target_uid}.")
                st.rerun()

# =========================================================================
# 4. FACULTY WORKFLOW (BUTTON ATTENDANCE & TEXTBOX GRADES SAVE TO SQL)
# =========================================================================
elif st.session_state.user_role == "Teacher":
    teacher_class = user_profile[1]
    st.title(f"👩‍🏫 Course Performance Management Engine: {teacher_class}")
    
    conn = get_db_connection()
    filtered_df = pd.read_sql_query("SELECT * FROM academic_records WHERE class = ?", conn, params=(teacher_class,))
    conn.close()
    
    if filtered_df.empty:
        st.info(f"No students have been assigned to {teacher_class} by administration yet.")
    else:
        st.subheader("📊 Active Student Ledger View (Live Database Output)")
        st.dataframe(filtered_df, use_container_width=True)
        
        st.markdown("---")
        col_att, col_grades = st.columns([1, 1])
        
        target_student = st.selectbox("Select Target Student Record to Update:", filtered_df["student_id"].tolist())
        
        # Pull single record from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT days_present, total_days, attendance_pct, quiz_1, quiz_2, feedback FROM academic_records WHERE student_id = ?", (target_student,))
        current_data = cursor.fetchone()
        conn.close()
        
        with col_att:
            st.subheader("⏱️ Instant Attendance Quick-Mark")
            st.write(f"Current Stats: **{current_data[0]} / {current_data[1]} Days** ({current_data[2]}%)")
            
            btn_col1, btn_col2 = st.columns(2)
            if btn_col1.button("✅ Mark Present Today", use_container_width=True):
                new_present = int(current_data[0]) + 1
                new_total = int(current_data[1]) + 1
                new_pct = round((new_present / new_total) * 100, 1)
                
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE academic_records SET days_present = ?, total_days = ?, attendance_pct = ? WHERE student_id = ?", (new_present, new_total, new_pct, target_student))
                conn.commit()
                conn.close()
                st.success(f"Added 1 day presence marker in SQL for {target_student}!")
                st.rerun()
                
            if btn_col2.button("❌ Mark Absent Today", use_container_width=True):
                new_total = int(current_data[1]) + 1
                new_pct = round((int(current_data[0]) / new_total) * 100, 1)
                
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE academic_records SET total_days = ?, attendance_pct = ? WHERE student_id = ?", (new_total, new_pct, target_student))
                conn.commit()
                conn.close()
                st.warning(f"Recorded absence tracking marker in SQL for {target_student}.")
                st.rerun()

        with col_grades:
            st.subheader("📝 Input Grades & Performance Analysis")
            
            with st.form("grades_form"):
                txt_q1 = st.text_input("Quiz 1 Evaluation Score (0-100):", value=str(current_data[3]))
                txt_q2 = st.text_input("Quiz 2 Evaluation Score (0-100):", value=str(current_data[4]))
                updated_feed = st.text_area("Provide Student Progress Feedback:", value=current_data[5] if current_data[5] else "")
                
                submit_grades = st.form_submit_button("💾 Save Grades & Remarks to SQL")
                
                if submit_grades:
                    try:
                        val_q1 = int(txt_q1)
                        val_q2 = int(txt_q2)
                        
                        if 0 <= val_q1 <= 100 and 0 <= val_q2 <= 100:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("UPDATE academic_records SET quiz_1 = ?, quiz_2 = ?, feedback = ? WHERE student_id = ?", (val_q1, val_q2, updated_feed, target_student))
                            conn.commit()
                            conn.close()
                            st.success(f"Academic values updated directly inside SQLite database.")
                            st.rerun()
                        else:
                            st.error("Input values out of bounds. Keep numbers between 0 and 100.")
                    except ValueError:
                        st.error("Invalid input. Please type numbers only.")

# =========================================================================
# 5. STUDENT WORKFLOW (SQL READING ONLY)
# =========================================================================
elif st.session_state.user_role == "Student":
    student_id = st.session_state.user_id
    st.title(f"🎓 Personal Academic Progress Portal")
    
    conn = get_db_connection()
    student_record = pd.read_sql_query("SELECT * FROM academic_records WHERE student_id = ?", conn, params=(student_id,))
    conn.close()
    
    if student_record.empty:
        st.warning("Your academic parameters haven't been provisioned by the department coordinator yet.")
    else:
        record_data = student_record.iloc[0]
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric(label="Your Logged Attendance Rate", value=f"{record_data['attendance_pct']}%")
        
        avg_score = (int(record_data["quiz_1"]) + int(record_data["quiz_2"])) / 2
        kpi2.metric(label="Aggregated Academic Test Average", value=f"{avg_score} / 100")
        
        risk_status = "Good Standing" if record_data["attendance_pct"] >= 75 else "Attendance Risk Protocol"
        kpi3.metric(label="Operational Accountability Status", value=risk_status)
        
        st.markdown("---")
        
        v_col1, v_col2 = st.columns([1, 1])
        with v_col1:
            st.subheader("📊 Dynamic Metric Analysis View")
            chart_data = pd.DataFrame({
                "Evaluation Milestones": ["Quiz 1 Assessment", "Quiz 2 Assessment", "Attendance Rate"],
                "Achieved Ratios (%)": [int(record_data["quiz_1"]), int(record_data["quiz_2"]), float(record_data["attendance_pct"])]
            }).set_index("Evaluation Milestones")
            
            st.bar_chart(chart_data)
            
        with v_col2:
            st.subheader("💬 Professor Review & Feedback Log")
            st.info(f"\"{record_data['feedback']}\"")
