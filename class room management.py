import streamlit as st
import pandas as pd

st.set_page_config(page_title="EduSphere Multi-Role Portal", layout="wide")

# =========================================================================
# 1. LIVE IN-MEMORY DATABASE STORAGE (Simulating a real database)
# =========================================================================
if "users_db" not in st.session_state:
    st.session_state.users_db = {
        "admin": {"password": "admin123", "role": "Admin", "name": "System Director"},
        "T101": {"password": "password123", "role": "Teacher", "name": "Prof. Aris", "dept": "Data Science", "class": "Class-A"},
        "T102": {"password": "password123", "role": "Teacher", "name": "Dr. Meera", "dept": "Mathematics", "class": "Class-B"},
        "S101": {"password": "student123", "role": "Student", "name": "Aarav Sharma", "class": "Class-A"},
        "S102": {"password": "student123", "role": "Student", "name": "Isha Patel", "class": "Class-A"}
    }

if "academic_records" not in st.session_state:
    st.session_state.academic_records = pd.DataFrame([
        {"Student ID": "S101", "Class": "Class-A", "Attendance %": 92, "Quiz 1": 85, "Quiz 2": 90, "Feedback": "Excellent participation."},
        {"Student ID": "S102", "Class": "Class-A", "Attendance %": 64, "Quiz 1": 55, "Quiz 2": 60, "Feedback": "Needs to improve regular attendance."}
    ])

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
    st.subheader("Real-Time Administrative, Faculty, & Student Login Hub")
    
    with st.form("login_form"):
        uid = st.text_input("Enter Unique ID (Admin / T-series / S-series):").strip()
        pwd = st.text_input("Password:", type="password")
        submit = st.form_submit_button("Authenticate Securely")
        
        if submit:
            if uid in st.session_state.users_db and st.session_state.users_db[uid]["password"] == pwd:
                st.session_state.logged_in = True
                st.session_state.user_id = uid
                st.session_state.user_role = st.session_state.users_db[uid]["role"]
                st.rerun()
            else:
                st.error("Invalid credentials. Please verify your ID or Password.")
    st.stop()

# Logout Handler in the Sidebar
st.sidebar.title(f"👤 Welcome, {st.session_state.users_db[st.session_state.user_id]['name']}")
st.sidebar.write(f"**Role Access Level:** {st.session_state.user_role}")
if st.sidebar.button("Secure Logout"):
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_role = None
    st.rerun()

# =========================================================================
# 3. ADMINISTRATIVE WORKFLOW (PROVISION, MODIFY, & DELETE)
# =========================================================================
if st.session_state.user_role == "Admin":
    st.title("⚙️ Global Administrative Control Dashboard")
    st.write("Generate distinct user profiles, modify dynamic records, and manage access parameters.")
    
    # Live User Infrastructure Matrix Top Display
    st.subheader("📋 Core Infrastructure User Matrix")
    display_users = [{"User ID": k, "Name": v["name"], "Role Access": v["role"], "Assigned Room": v.get("class", "Global")} for k, v in st.session_state.users_db.items()]
    st.dataframe(pd.DataFrame(display_users), use_container_width=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    # BLOCK A: CREATE NEW USERS
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
            elif full_id in st.session_state.users_db:
                st.error(f"User identity handle {full_id} already exists within records.")
            else:
                st.session_state.users_db[full_id] = {
                    "password": new_pass,
                    "role": new_role,
                    "name": new_name,
                    "class": assigned_class
                }
                
                if new_role == "Student":
                    new_entry = pd.DataFrame([{"Student ID": full_id, "Class": assigned_class, "Attendance %": 100, "Quiz 1": 0, "Quiz 2": 0, "Feedback": "Account opened."}])
                    st.session_state.academic_records = pd.concat([st.session_state.academic_records, new_entry], ignore_index=True)
                    
                st.success(f"Successfully configured active production profile for {full_id}")
                st.rerun()

    # BLOCK B: MODIFY OR DELETE RESTRUCTURING PANEL
    with col2:
        st.subheader("🛠️ Data Modification & Record Removal Panel")
        
        # Filter profiles to exclude the active root Admin account
        updatable_users = [uid for uid in st.session_state.users_db.keys() if uid != "admin"]
        
        if not updatable_users:
            st.info("No active teacher or student profiles currently logged in system.")
        else:
            target_uid = st.selectbox("Select Target User ID to Manage:", updatable_users)
            current_profile = st.session_state.users_db[target_uid]
            
            st.markdown(f"**Current Role:** {current_profile['role']} | **Assigned Room:** {current_profile.get('class', 'N/A')}")
            
            # Interactive Modification Fields
            mod_name = st.text_input("Modify Account Full Name:", value=current_profile["name"])
            mod_pass = st.text_input("Modify Account Password Access:", value=current_profile["password"], type="password")
            mod_class = st.selectbox("Modify Room Assignment Mapping:", ["Class-A", "Class-B", "Class-C"], index=["Class-A", "Class-B", "Class-C"].index(current_profile.get("class", "Class-A")))
            
            m_col1, m_col2 = st.columns(2)
            
            with m_col1:
                if st.button("💾 Apply Modifications", use_container_width=True):
                    # Save edits into core profiles database
                    st.session_state.users_db[target_uid]["name"] = mod_name
                    st.session_state.users_db[target_uid]["password"] = mod_pass
                    st.session_state.users_db[target_uid]["class"] = mod_class
                    
                    # Cascade class change to active gradebook lists if target is a Student
                    if current_profile["role"] == "Student":
                        idx_list = st.session_state.academic_records[st.session_state.academic_records["Student ID"] == target_uid].index
                        if not idx_list.empty:
                            st.session_state.academic_records.at[idx_list[0], "Class"] = mod_class
                            
                    st.success(f"Successfully updated data modifications for account {target_uid}.")
                    st.rerun()
                    
            with m_col2:
                if st.button("🗑️ Permanent Record Purge", type="primary", use_container_width=True):
                    # Remove from credentials directory
                    del st.session_state.users_db[target_uid]
                    
                    # Cascade removal across active academic grade lists
                    if current_profile["role"] == "Student":
                        st.session_state.academic_records = st.session_state.academic_records[st.session_state.academic_records["Student ID"] != target_uid].reset_index(drop=True)
                        
                    st.warning(f"Profile and matching academic footprints deleted for handle {target_uid}.")
                    st.rerun()

# =========================================================================
# 4. FACULTY WORKFLOW (GRADES & ATTENDANCE LOGISTICS)
# =========================================================================
elif st.session_state.user_role == "Teacher":
    teacher_class = st.session_state.users_db[st.session_state.user_id]["class"]
    st.title(f"👩‍🏫 Course Performance Management Engine: {teacher_class}")
    
    class_filter = st.session_state.academic_records["Class"] == teacher_class
    filtered_df = st.session_state.academic_records[class_filter]
    
    if filtered_df.empty:
        st.info(f"No students have been assigned to {teacher_class} by administration yet.")
    else:
        st.subheader("📊 Active Student Ledger View")
        st.dataframe(filtered_df, use_container_width=True)
        
        st.markdown("---")
        st.subheader("✍️ Update Student Evaluation File")
        
        target_student = st.selectbox("Select Target Student Record:", filtered_df["Student ID"].tolist())
        student_idx = st.session_state.academic_records[st.session_state.academic_records["Student ID"] == target_student].index[0]
        current_data = st.session_state.academic_records.loc[student_idx]
        
        c1, c2, c3 = st.columns(3)
        with c1:
            updated_att = st.slider("Update Absolute Attendance Log (%)", 0, 100, int(current_data["Attendance %"]))
        with c2:
            updated_q1 = st.slider("Quiz 1 Metric Evaluation Score", 0, 100, int(current_data["Quiz 1"]))
        with c3:
            updated_q2 = st.slider("Quiz 2 Metric Evaluation Score", 0, 100, int(current_data["Quiz 2"]))
            
        updated_feed = st.text_area("Provide Analytical Progress Feedback Remarks:", value=current_data["Feedback"])
        
        if st.button("Commit Performance Changes"):
            st.session_state.academic_records.at[student_idx, "Attendance %"] = updated_att
            st.session_state.academic_records.at[student_idx, "Quiz 1"] = updated_q1
            st.session_state.academic_records.at[student_idx, "Quiz 2"] = updated_q2
            st.session_state.academic_records.at[student_idx, "Feedback"] = updated_feed
            st.success(f"Performance database records updated for identity tracker {target_student}.")
            st.rerun()

# =========================================================================
# 5. STUDENT WORKFLOW (METRIC COMPREHENSION & DATA VISUALIZATION)
# =========================================================================
elif st.session_state.user_role == "Student":
    student_id = st.session_state.user_id
    st.title(f"🎓 Personal Academic Progress Portal")
    
    student_record = st.session_state.academic_records[st.session_state.academic_records["Student ID"] == student_id]
    
    if student_record.empty:
        st.warning("Your academic parameters haven't been provisioned by the department coordinator yet.")
    else:
        record_data = student_record.iloc[0]
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric(label="Your Logged Attendance Rate", value=f"{record_data['Attendance %']}%")
        
        avg_score = (record_data["Quiz 1"] + record_data["Quiz 2"]) / 2
        kpi2.metric(label="Aggregated Academic Test Average", value=f"{avg_score} / 100")
        
        risk_status = "Good Standing" if record_data["Attendance %"] >= 75 else "Attendance Risk Protocol"
        kpi3.metric(label="Operational Accountability Status", value=risk_status)
        
        st.markdown("---")
        
        v_col1, v_col2 = st.columns([1, 1])
        with v_col1:
            st.subheader("📊 Dynamic Metric Analysis View")
            chart_data = pd.DataFrame({
                "Evaluation Milestones": ["Quiz 1 Assessment", "Quiz 2 Assessment", "Attendance Rate"],
                "Achieved Ratios (%)": [record_data["Quiz 1"], record_data["Quiz 2"], record_data["Attendance %"]]
            }).set_index("Evaluation Milestones")
            
            st.bar_chart(chart_data)
            
        with v_col2:
            st.subheader("💬 Professor Review & Feedback Log")
            st.info(f"\"{record_data['Feedback']}\"")
            
            st.subheader("💡 Strategic Action Items")
            if record_data["Attendance %"] < 75:
                st.error("🚨 Attendance is below university requirement thresholds. Schedule a check-in with your assigned counselor immediately.")
            else:
                st.success("✅ Attendance criteria achieved. Keep up steady performance patterns during lectures.")
