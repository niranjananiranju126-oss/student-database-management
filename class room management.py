import streamlit as st
import pandas as pd
import sqlite3
import datetime
import os
from PIL import Image

# Optional imports for barcode/QR code parsing
try:
    from pyzbar.pyzbar import decode
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False

st.set_page_config(page_title="EduSphere Multi-Role Portal", layout="wide")

# Directory setup for media storage
UPLOAD_DIR = "media/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =========================================================================
# 1. SQLITE DATABASE INITIALIZATION & SCHEMA UPDATES
# =========================================================================
def init_db():
    conn = sqlite3.connect("edusphere.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Safe Migrations for schema updates
    migrations = [
        "ALTER TABLE academic_records ADD COLUMN exam_marks INTEGER DEFAULT 0",
        "ALTER TABLE academic_records ADD COLUMN extra_curricular_rating INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN photo_path TEXT DEFAULT ''",
        "ALTER TABLE users ADD COLUMN barcode_token TEXT DEFAULT ''"
    ]
    for query in migrations:
        try:
            cursor.execute(query)
        except sqlite3.OperationalError:
            pass

    # Core Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT NOT NULL,
            class TEXT,
            photo_path TEXT DEFAULT '',
            barcode_token TEXT DEFAULT ''
        )
    """)
    
    # Academic Records Table
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
    
    # Attendance Logs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_logs (
            student_id TEXT,
            date TEXT,
            status TEXT,
            PRIMARY KEY (student_id, date),
            FOREIGN KEY (student_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    
    # Initial Data Seed
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        initial_users = [
            ("admin", "admin123", "Admin", "System Director", "Global", "", "BARCODE-ADMIN"),
            ("T101", "password123", "Teacher", "Prof. Aris", "Class-A", "", "BARCODE-T101"),
            ("T102", "password123", "Teacher", "Dr. Meera", "Class-B", "", "BARCODE-T102"),
            ("S101", "student123", "Student", "Aarav Sharma", "Class-A", "", "BARCODE-S101"),
            ("S102", "student123", "Student", "Isha Patel", "Class-A", "", "BARCODE-S102"),
            ("S103", "student123", "Student", "Rohan Das", "Class-A", "", "BARCODE-S103")
        ]
        cursor.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)", initial_users)
        
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
# 2. DUAL AUTHENTICATION / LOGIN SYSTEM (MANUAL & BARCODE/QR)
# =========================================================================
if not st.session_state.logged_in:
    st.title("🛡️ EduSphere Management Portal")
    st.subheader("Real-Time SQL-Backed Admin, Faculty, & Student Login Hub")
    
    auth_mode = st.radio("Select Authentication Method:", ["🔑 Manual Login", "📷 Barcode / QR Code Scanner"], horizontal=True)
    
    if auth_mode == "🔑 Manual Login":
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

    elif auth_mode == "📷 Barcode / QR Code Scanner":
        st.info("Hold your ID card with the barcode/QR code facing the camera.")
        camera_image = st.camera_input("Scan Barcode ID Card")
        
        if camera_image:
            if not PYZBAR_AVAILABLE:
                st.warning("Barcode scanning library (`pyzbar`) is not installed. Defaulting to string payload matching.")
            
            img = Image.open(camera_image)
            scanned_data = None
            
            if PYZBAR_AVAILABLE:
                decoded_objects = decode(img)
                if decoded_objects:
                    scanned_data = decoded_objects[0].data.decode("utf-8").strip()
            
            if not scanned_data:
                # Manual barcode entry fallback if scanner device lacks direct optical library decoding
                scanned_data = st.text_input("Optical scan failed. Manual Barcode Token Entry:", placeholder="e.g., BARCODE-S101")

            if scanned_data:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT user_id, role FROM users WHERE barcode_token = ? OR user_id = ?", (scanned_data, scanned_data))
                user = cursor.fetchone()
                conn.close()
                
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.session_state.user_role = user[1]
                    st.success(f"Access granted for User ID: {user[0]}")
                    st.rerun()
                else:
                    st.error("Barcode or ID token not recognized in system registry.")
    st.stop()

# Load User Context
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("SELECT name, class, photo_path FROM users WHERE user_id = ?", (st.session_state.user_id,))
user_profile = cursor.fetchone()
conn.close()

# Sidebar User Identification Matrix
st.sidebar.title(f"👤 Welcome, {user_profile[0]}")
st.sidebar.write(f"**Role Access Level:** {st.session_state.user_role}")

if user_profile[2] and os.path.exists(user_profile[2]):
    st.sidebar.image(user_profile[2], caption=user_profile[0], width=180)
else:
    st.sidebar.info("No profile picture uploaded.")

if st.sidebar.button("Secure Logout"):
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_role = None
    st.rerun()

# =========================================================================
# 3. LIVE RUNNING NEWS BANNER
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
# 4. ADMINISTRATIVE WORKFLOW (SQL & PHOTO / BARCODE MANAGEMENT)
# =========================================================================
if st.session_state.user_role == "Admin":
    st.title("⚙️ Global Administrative Control Dashboard")
    
    st.subheader("📋 Core Infrastructure User Matrix")
    conn = get_db_connection()
    df_users = pd.read_sql_query("SELECT user_id AS 'User ID', name AS 'Name', role AS 'Role Access', class AS 'Assigned Room', barcode_token AS 'Barcode Token' FROM users", conn)
    conn.close()
    st.dataframe(df_users, use_container_width=True)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("➕ Provision New System Access")
        new_role = st.selectbox("Assign System Role Profile:", ["Teacher", "Student"])
        id_prefix = "T" if new_role == "Teacher" else "S"
        new_num = st.text_input(f"Enter Reference Number ({id_prefix}xxxx):", placeholder="e.g., 103", key="create_num")
        full_id = f"{id_prefix}{new_num}" if new_num else ""
        
        new_name = st.text_input("Account User Full Name:", key="create_name")
        new_pass = st.text_input("Account Password:", type="password", key="create_pass")
        assigned_class = st.selectbox("Class Mapping:", ["Class-A", "Class-B", "Class-C"], key="create_class")
        new_barcode = st.text_input("Assign Barcode / QR Token String:", value=f"BARCODE-{full_id}", key="create_barcode")
        uploaded_photo = st.file_uploader("Upload Profile Photo:", type=["jpg", "png", "jpeg"], key="create_photo")

        if st.button("Generate & Register Credentials"):
            if not new_num or not new_name or not new_pass:
                st.error("All credential fields must be populated.")
            else:
                photo_file_path = ""
                if uploaded_photo is not None:
                    photo_file_path = os.path.join(UPLOAD_DIR, f"{full_id}_{uploaded_photo.name}")
                    with open(photo_file_path, "wb") as f:
                        f.write(uploaded_photo.getbuffer())

                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                   (full_id, new_pass, new_role, new_name, assigned_class, photo_file_path, new_barcode))
                    if new_role == "Student":
                        cursor.execute("INSERT INTO academic_records VALUES (?, ?, 0, 0, 0, 0, 'Account opened.')", (full_id, assigned_class))
                    conn.commit()
                    st.success(f"Successfully configured active profile for {full_id}")
                    conn.close()
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error(f"User identity handle {full_id} already exists.")
                    conn.close()

    with col2:
        st.subheader("🛠️ Data Modification & Record Removal Panel")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id != 'admin'")
        updatable_users = [row[0] for row in cursor.fetchall()]
        
        if updatable_users:
            target_uid = st.selectbox("Select Target User ID to Manage:", updatable_users)
            cursor.execute("SELECT role, class, name, password, photo_path, barcode_token FROM users WHERE user_id = ?", (target_uid,))
            current_profile = cursor.fetchone()
            conn.close()
            
            st.markdown(f"**Current Role:** {current_profile[0]} | **Room:** {current_profile[1]}")
            
            mod_name = st.text_input("Modify Account Full Name:", value=current_profile[2])
            mod_pass = st.text_input("Modify Password:", value=current_profile[3], type="password")
            mod_class = st.selectbox("Modify Room Mapping:", ["Class-A", "Class-B", "Class-C"], 
                                     index=["Class-A", "Class-B", "Class-C"].index(current_profile[1] if current_profile[1] in ["Class-A", "Class-B", "Class-C"] else "Class-A"))
            mod_barcode = st.text_input("Modify Barcode Token String:", value=current_profile[5])
            mod_photo = st.file_uploader("Update Profile Photo:", type=["jpg", "png", "jpeg"], key="mod_photo")

            m_col1, m_col2 = st.columns(2)
            if m_col1.button("💾 Apply Modifications", use_container_width=True):
                photo_file_path = current_profile[4]
                if mod_photo is not None:
                    photo_file_path = os.path.join(UPLOAD_DIR, f"{target_uid}_{mod_photo.name}")
                    with open(photo_file_path, "wb") as f:
                        f.write(mod_photo.getbuffer())

                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET name = ?, password = ?, class = ?, photo_path = ?, barcode_token = ? WHERE user_id = ?", 
                               (mod_name, mod_pass, mod_class, photo_file_path, mod_barcode, target_uid))
                if current_profile[0] == "Student":
                    cursor.execute("UPDATE academic_records SET class = ? WHERE student_id = ?", (mod_class, target_uid))
                conn.commit()
                conn.close()
                st.success(f"Saved modifications for {target_uid}.")
                st.rerun()
                    
            if m_col2.button("🗑️ Permanent Record Purge", type="primary", use_container_width=True):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE user_id = ?", (target_uid,))
                cursor.execute("DELETE FROM academic_records WHERE student_id = ?", (target_uid,))
                cursor.execute("DELETE FROM attendance_logs WHERE student_id = ?", (target_uid,))
                conn.commit()
                conn.close()
                st.warning(f"Purged profile records for handle {target_uid}.")
                st.rerun()

# =========================================================================
# 5. FACULTY WORKFLOW (ATTENDANCE, GRADES & PHOTO REVIEW)
# =========================================================================
elif st.session_state.user_role == "Teacher":
    teacher_class = user_profile[1]
    st.title(f"👩‍🏫 Course Performance Engine: {teacher_class}")
    
    conn = get_db_connection()
    sql_query = """
        SELECT 
            ar.student_id,
            u.name,
            u.photo_path,
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
    
    if not filtered_df.empty:
        filtered_df["Attendance %"] = filtered_df.apply(
            lambda r: round((r["days_present"] / r["total_days"] * 100), 1) if r["total_days"] > 0 else 100.0, axis=1
        )
        st.subheader("📊 Active Student Ledger View")
        st.dataframe(
            filtered_df[["student_id", "name", "days_present", "total_days", "Attendance %", "quiz_1", "quiz_2", "exam_marks", "extra_curricular_rating", "feedback"]], 
            use_container_width=True
        )
        
        st.markdown("---")
        target_student = st.selectbox("Select Target Student Record to Update:", filtered_df["student_id"].tolist())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT u.photo_path, ar.quiz_1, ar.quiz_2, ar.exam_marks, ar.extra_curricular_rating, ar.feedback FROM academic_records ar JOIN users u ON ar.student_id = u.user_id WHERE ar.student_id = ?", (target_student,))
        current_data = cursor.fetchone()
        conn.close()

        col_pic, col_att, col_grades = st.columns([1, 1.5, 2])

        with col_pic:
            st.subheader("📷 Student Photo")
            if current_data[0] and os.path.exists(current_data[0]):
                st.image(current_data[0], use_container_width=True)
            else:
                st.info("No profile picture set for this student.")

            student_photo = st.file_uploader("Upload / Replace Photo:", type=["jpg", "png", "jpeg"], key="faculty_photo_upload")
            if st.button("Save Student Photo"):
                if student_photo is not None:
                    photo_file_path = os.path.join(UPLOAD_DIR, f"{target_student}_{student_photo.name}")
                    with open(photo_file_path, "wb") as f:
                        f.write(student_photo.getbuffer())
                    
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET photo_path = ? WHERE user_id = ?", (photo_file_path, target_student))
                    conn.commit()
                    conn.close()
                    st.success("Photo updated successfully!")
                    st.rerun()

        with col_att:
            st.subheader("📅 Attendance Logging")
            selected_date = st.date_input("Select Calendar Date:", datetime.date.today())
            date_str = str(selected_date)
            
            btn_col1, btn_col2 = st.columns(2)
            if btn_col1.button("✅ Mark Present", use_container_width=True):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO attendance_logs VALUES (?, ?, ?)", (target_student, date_str, "Present"))
                conn.commit()
                conn.close()
                st.success(f"Logged Present on {date_str}")
                st.rerun()
                
            if btn_col2.button("❌ Mark Absent", use_container_width=True):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO attendance_logs VALUES (?, ?, ?)", (target_student, date_str, "Absent"))
                conn.commit()
                conn.close()
                st.warning(f"Logged Absent on {date_str}")
                st.rerun()

        with col_grades:
            st.subheader("📝 Input Performance Scores")
            with st.form("grades_form"):
                txt_q1 = st.text_input("Quiz 1 Marks (0-100):", value=str(current_data[1]))
                txt_q2 = st.text_input("Quiz 2 Marks (0-100):", value=str(current_data[2]))
                txt_exam = st.text_input("Final Exam Marks (0-100):", value=str(current_data[3]))
                txt_ec = st.text_input("Extra-Curricular Score (0-10):", value=str(current_data[4]))
                updated_feed = st.text_area("Progress Feedback:", value=current_data[5] if current_data[5] else "")
                
                if st.form_submit_button("💾 Save Metrics to SQL"):
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE academic_records 
                            SET quiz_1 = ?, quiz_2 = ?, exam_marks = ?, extra_curricular_rating = ?, feedback = ? 
                            WHERE student_id = ?
                        """, (int(txt_q1), int(txt_q2), int(txt_exam), int(txt_ec), updated_feed, target_student))
                        conn.commit()
                        conn.close()
                        st.success("Performance matrix updated.")
                        st.rerun()
                    except ValueError:
                        st.error("Enter valid numeric scores.")

# =========================================================================
# 6. STUDENT WORKFLOW (PROGRESS & PHOTO / BARCODE ID CARD VIEW)
# =========================================================================
elif st.session_state.user_role == "Student":
    student_id = st.session_state.user_id
    st.title("🎓 Personal Academic Progress Portal")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, class, photo_path, barcode_token FROM users WHERE user_id = ?", (student_id,))
    user_info = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(CASE WHEN status = 'Present' THEN 1 END), COUNT(*) FROM attendance_logs WHERE student_id = ?", (student_id,))
    att_stats = cursor.fetchone()
    
    student_record = pd.read_sql_query("SELECT * FROM academic_records WHERE student_id = ?", conn, params=(student_id,))
    conn.close()
    
    card_col, metrics_col = st.columns([1, 2])
    
    with card_col:
        st.subheader("🪪 Digital Student ID Card")
        if user_info[2] and os.path.exists(user_info[2]):
            st.image(user_info[2], width=200)
        else:
            st.info("No profile photo attached.")
        
        st.markdown(f"**Name:** {user_info[0]}")
        st.markdown(f"**Student ID:** {student_id}")
        st.markdown(f"**Class Room:** {user_info[1]}")
        st.code(f"Barcode Token: {user_info[3]}", language="text")

        student_photo_upload = st.file_uploader("Upload Profile Photo:", type=["jpg", "png", "jpeg"], key="student_self_upload")
        if st.button("Upload Photo"):
            if student_photo_upload is not None:
                photo_file_path = os.path.join(UPLOAD_DIR, f"{student_id}_{student_photo_upload.name}")
                with open(photo_file_path, "wb") as f:
                    f.write(student_photo_upload.getbuffer())
                
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET photo_path = ? WHERE user_id = ?", (photo_file_path, student_id))
                conn.commit()
                conn.close()
                st.success("Profile photo uploaded!")
                st.rerun()

    with metrics_col:
        if not student_record.empty:
            record_data = student_record.iloc[0]
            present_days = att_stats[0] if att_stats[0] else 0
            total_days = att_stats[1] if att_stats[1] else 0
            att_pct = round((present_days / total_days * 100), 1) if total_days > 0 else 100.0
            
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("Attendance Rate", f"{att_pct}%")
            kpi2.metric("Final Exam Score", f"{record_data['exam_marks']} / 100")
            kpi3.metric("Extra-Curricular Rating", f"{record_data['extra_curricular_rating']} / 10")
            
            chart_data = pd.DataFrame({
                "Evaluation Milestones": ["Quiz 1", "Quiz 2", "Final Exam", "Extra-Curricular (x10)"],
                "Achieved Ratios (%)": [int(record_data["quiz_1"]), int(record_data["quiz_2"]), int(record_data["exam_marks"]), int(record_data["extra_curricular_rating"]) * 10]
            }).set_index("Evaluation Milestones")
            
            st.bar_chart(chart_data)
            
            st.markdown("#### 📝 Instructor Comments:")
            if record_data['feedback'] and record_data['feedback'].strip():
                st.info(f"\"{record_data['feedback']}\"")
            else:
                st.info("No feedback recorded for this evaluation cycle.")
