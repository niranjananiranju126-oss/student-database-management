import streamlit as st
import pandas as pd
import sqlite3
import datetime

st.set_page_config(page_title="EduSphere Multi-Role Portal", layout="wide")

# =========================================================================
# 1. SQLITE DATABASE INITIALIZATION & SCHEMA UPDATES
# =========================================================================
def init_db():
    conn = sqlite3.connect("edusphere.db")
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # --- SAFE MIGRATION STEP ---
    try:
        cursor.execute("ALTER TABLE academic_records ADD COLUMN exam_marks INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  

    try:
        cursor.execute("ALTER TABLE academic_records ADD COLUMN extra_curricular_rating INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  
    # ----------------------------

    # 1. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT NOT NULL,
            class TEXT
        )
    """)
    
    # 2. Academic Records Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS academic_records (
            student_id TEXT PRIMARY KEY,
            class TEXT NOT NULL,
            quiz_1 INTEGER DEFAULT 0,
            quiz_2 INTEGER DEFAULT 0,
            exam_marks INTEGER DEFAULT 0,
            extra_curricular_rating INTEGER DEFAULT 0,
            feedback TEXT,
            FOREIGN KEY (student_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    
    # 3. Separate Date-by-Date Attendance Logs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_logs (
            student_id TEXT,
            date TEXT,
            status TEXT,
            PRIMARY KEY (student_id, date),
            FOREIGN KEY (student_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    
    # Inject Initial Seed Data safely
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        initial_users = [
            ("admin", "admin123", "Admin", "System Director", "Global"),
            ("T101", "password123", "Teacher", "Prof. Aris", "Class-A"),
            ("T102", "password123", "Teacher", "Dr. Meera", "Class-B"),
            ("S101", "student123", "Student", "Aarav Sharma", "Class-A"),
            ("S102", "student123", "Student", "Isha Patel", "Class-A"),
            ("S103", "student123", "Student", "Rohan Das", "Class-A")
        ]
        cursor.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?)", initial_users)
        
        initial_records = [
            ("S101", "Class-A", 85, 90, 95, 9, "Excellent overall academic track."),
            ("S102", "Class-A", 55, 60, 72, 4, "Needs focus on core concepts."),
            ("S103", "Class-A", 90, 92, 98, 10, "Exceptional performer in sports and music.")
        ]
        cursor.executemany("INSERT INTO academic_records VALUES (?, ?, ?, ?, ?, ?, ?)", initial_records)
        
        today_str = str(datetime.date.today())
        yesterday_str = str(datetime.date.today() - datetime.timedelta(days=1))
        initial_attendance = [
            ("S101", yesterday_str, "Present"), ("S101", today_str, "Present"),
            ("S102", yesterday_str, "Absent"),  ("S102", today_str, "Present"),
            ("S103", yesterday_str, "Present"), ("S103", today_str, "Present")
        ]
        cursor.executemany("INSERT INTO attendance_logs VALUES (?, ?, ?)", initial_attendance)
        
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect("edusphere.db")

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
# 3. LIVE RUNNING NEWS BANNER (TOPPER & EXTRA-CURRICULAR RUNNING TEXT)
# =========================================================================
conn = get_db_connection()
marquee_query = """
    SELECT u.name, ar.exam_marks, ar.extra_curricular_rating, u.class
    FROM academic_records ar
    JOIN users u ON ar.student_id = u.user_id
"""
marquee_data = pd.read_sql_query(marquee_query, conn)
conn.close()

if not marquee_data.empty:
    highest_mark = marquee_data["exam_marks"].max()
    toppers = marquee_data[marquee_data["exam_marks"] == highest_mark]["name"].tolist()
    star_performers = marquee_data[marquee_data["extra_curricular_rating"] >= 8]["name"].tolist()
    
    topper_text = ", ".join(toppers) if toppers else "None"
    star_text = ", ".join(star_performers) if star_performers else "None"
    
    marquee_html = f"""
    <div style="background-color: #1E293B; padding: 10px; border-radius: 8px; margin-bottom: 20px;">
        <marquee behavior="scroll" direction="left" scrollamount="6" style="color: #F8FAFC; font-weight: bold; font-size: 16px;">
            🏆 Academic Topper Alert: <span style="color: #38BDF8;">{topper_text}</span> (Score: {highest_mark} pts) 
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🌟 Extra-Curricular Champions: <span style="color: #FBBF24;">{star_text}</span> (Rating 8+/10)
        </marquee>
    </div>
    """
    st.markdown(marquee_html, unsafe_allow_html=True)

# =========================================================================
# 4. ADMINISTRATIVE WORKFLOW (SQL BASED)
# =========================================================================
if st.session_state.user_role == "Admin":
    st.title("⚙️ Global Administrative Control Dashboard")
    
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
                        cursor.execute("INSERT INTO academic_records VALUES (?, ?, 0, 0, 0, 0, 'Account opened.')", (full_id, assigned_class))
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
                cursor.execute("DELETE FROM attendance_logs WHERE student_id = ?", (target_uid,))
                conn.commit()
                conn.close()
                st.warning(f"Profile and SQL footprints purged for handle {target_uid}.")
                st.rerun()

# =========================================================================
# 5. FACULTY WORKFLOW (DATE-SPECIFIC ATTENDANCE LOGS & TEXTBOX GRADES)
# =========================================================================
elif st.session_state.user_role == "Teacher":
    teacher_class = user_profile[1]
    st.title(f"👩‍🏫 Course Performance Management Engine: {teacher_class}")
    
    conn = get_db_connection()
    sql_query = """
        SELECT 
            ar.student_id,
            u.name,
            COUNT(CASE WHEN al.status = 'Present' THEN 1 END) as days_present,
            COUNT(al.status) as total_days,
            ar.quiz_1,
            ar.quiz_2,
            ar.exam_marks,
            ar.extra_curricular_rating,
            ar.feedback
        FROM academic_records ar
        JOIN users u ON ar.student_id = u.user_id
        LEFT JOIN attendance_logs al ON ar.student_id = al.student_id
        WHERE ar.class = ?
        GROUP BY ar.student_id
    """
    filtered_df = pd.read_sql_query(sql_query, conn, params=(teacher_class,))
    conn.close()
    
    if filtered_df.empty:
        st.info(f"No students have been assigned to {teacher_class} by administration yet.")
    else:
        filtered_df["Attendance %"] = filtered_df.apply(
            lambda r: round((r["days_present"] / r["total_days"] * 100), 1) if r["total_days"] > 0 else 100.0, axis=1
        )
        
        st.subheader("📊 Active Student Ledger View (Live Database Output)")
        st.dataframe(
            filtered_df[["student_id", "name", "days_present", "total_days", "Attendance %", "quiz_1", "quiz_2", "exam_marks", "extra_curricular_rating", "feedback"]], 
            use_container_width=True
        )
        
        st.markdown("---")
        col_att, col_grades = st.columns([1, 1])
        
        target_student = st.selectbox("Select Target Student Record to Update:", filtered_df["student_id"].tolist())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT quiz_1, quiz_2, exam_marks, extra_curricular_rating, feedback FROM academic_records WHERE student_id = ?", (target_student,))
        current_data = cursor.fetchone()
        conn.close()
        
        with col_att:
            st.subheader("📅 Separate Calendar Day Attendance Management")
            selected_date = st.date_input("Select Working Calendar Date to Log:", datetime.date.today())
            date_str = str(selected_date)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM attendance_logs WHERE student_id = ? AND date = ?", (target_student, date_str))
            existing_status = cursor.fetchone()
            conn.close()
            
            if existing_status:
                st.info(f"Current recorded status on **{date_str}**: **{existing_status[0]}**")
            else:
                st.warning(f"No log footprint found for {target_student} on {date_str}.")
                
            btn_col1, btn_col2 = st.columns(2)
            if btn_col1.button("✅ Mark Present for Date", use_container_width=True):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO attendance_logs VALUES (?, ?, ?)", (target_student, date_str, "Present"))
                conn.commit()
                conn.close()
                st.success(f"Logged 'Present' for {target_student} on {date_str}!")
                st.rerun()
                
            if btn_col2.button("❌ Mark Absent for Date", use_container_width=True):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO attendance_logs VALUES (?, ?, ?)", (target_student, date_str, "Absent"))
                conn.commit()
                conn.close()
                st.warning(f"Logged 'Absent' for {target_student} on {date_str}.")
                st.rerun()

        with col_grades:
            st.subheader("📝 Input Grades & Performance Analysis")
            
            with st.form("grades_form"):
                txt_q1 = st.text_input("Quiz 1 Evaluation Score (0-100):", value=str(current_data[0]))
                txt_q2 = st.text_input("Quiz 2 Evaluation Score (0-100):", value=str(current_data[1]))
                txt_exam = st.text_input("Final Exam Marks (0-100):", value=str(current_data[2]))
                txt_ec = st.text_input("Extra-Curricular Rating (0-10):", value=str(current_data[3]))
                updated_feed = st.text_area("Provide Student Progress Feedback:", value=current_data[4] if current_data[4] else "")
                
                submit_grades = st.form_submit_button("💾 Save Performance Matrix to SQL")
                
                if submit_grades:
                    try:
                        val_q1 = int(txt_q1)
                        val_q2 = int(txt_q2)
                        val_exam = int(txt_exam)
                        val_ec = int(txt_ec)
                        
                        if 0 <= val_q1 <= 100 and 0 <= val_q2 <= 100 and 0 <= val_exam <= 100 and 0 <= val_ec <= 10:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE academic_records 
                                SET quiz_1 = ?, quiz_2 = ?, exam_marks = ?, extra_curricular_rating = ?, feedback =? 
                                WHERE student_id = ?
                            """, (val_q1, val_q2, val_exam, val_ec, updated_feed, target_student))
                            conn.commit()
                            conn.close()
                            st.success(f"All academic metrics updated and broadcasted globally.")
                            st.rerun()
                        else:
                            st.error("Input values out of boundaries. Quizzes/Exams: 0-100. Extra-Curricular: 0-10.")
                    except ValueError:
                        st.error("Invalid entry. Please make sure all entries are numbers only.")

# =========================================================================
# 6. STUDENT WORKFLOW (UPDATED DYNAMIC FEEDBACK STRUCTURE)
# =========================================================================
elif st.session_state.user_role == "Student":
    student_id = st.session_state.user_id
    st.title(f"🎓 Personal Academic Progress Portal")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(CASE WHEN status = 'Present' THEN 1 END), COUNT(*) FROM attendance_logs WHERE student_id = ?", (student_id,))
    att_stats = cursor.fetchone()
    
    student_record = pd.read_sql_query("SELECT * FROM academic_records WHERE student_id = ?", conn, params=(student_id,))
    conn.close()
    
    if student_record.empty:
        st.warning("Your academic parameters haven't been provisioned by the department coordinator yet.")
    else:
        record_data = student_record.iloc[0]
        
        present_days = att_stats[0] if att_stats[0] else 0
        total_days = att_stats[1] if att_stats[1] else 0
        att_pct = round((present_days / total_days * 100), 1) if total_days > 0 else 100.0
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric(label="Your Calendar Attendance Rate", value=f"{att_pct}% ({present_days}/{total_days} Days)")
        kpi2.metric(label="Final Exam Score Mark", value=f"{record_data['exam_marks']} / 100")
        kpi3.metric(label="Extra-Curricular Rating Score", value=f"{record_data['extra_curricular_rating']} / 10")
        
        st.markdown("---")
        
        v_col1, v_col2 = st.columns([1, 1])
        with v_col1:
            st.subheader("📊 Dynamic Metric Analysis View")
            chart_data = pd.DataFrame({
                "Evaluation Milestones": ["Quiz 1 Assessment", "Quiz 2 Assessment", "Final Exam Score", "Extra-Curricular Rating x10"],
                "Achieved Ratios (%)": [int(record_data["quiz_1"]), int(record_data["quiz_2"]), int(record_data["exam_marks"]), int(record_data["extra_curricular_rating"]) * 10]
            }).set_index("Evaluation Milestones")
            
            st.bar_chart(chart_data)
            
        with v_col2:
            st.subheader("💬 Professor Review & Feedback Log")
            
            # Formatted presentation mirroring how data flows from the entry points to the repository
            st.markdown("### 📋 Official Performance Summary")
            
            # Dynamic grading logic based on metrics flowing from the data schema
            exam_score = int(record_data['exam_marks'])
            if exam_score >= 90:
                performance_tier = "🥇 Tier 1: Outstanding Distinction"
            elif exam_score >= 75:
                performance_tier = "🥈 Tier 2: First Class Academic Standing"
            elif exam_score >= 50:
                performance_tier = "🥉 Tier 3: Pass Profile (Needs Reinforcement)"
            else:
                performance_tier = "⚠️ Tier 4: Review Required"
                
            st.markdown(f"**Academic Evaluation Status:** `{performance_tier}`")
            st.markdown(f"**Co-Curricular Engagement Rating:** `{record_data['extra_curricular_rating']}/10`")
            
            st.markdown("#### 📝 Instructor Comments:")
            if record_data['feedback'] and record_data['feedback'].strip():
                st.info(f"\"{record_data['feedback']}\"")
            else:
                st.info('"No comments recorded for this evaluation cycle yet."')
