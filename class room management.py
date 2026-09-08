import io
import barcode
from barcode.writer import ImageWriter
import pandas as pd
from PIL import Image
import streamlit as st
from datetime import datetime, date

# =========================================================
# INITIALIZATION & STATE MANAGEMENT
# =========================================================
st.set_page_config(page_title="School & HR Management Portal", layout="wide")

if "users" not in st.session_state:
    st.session_state.users = pd.DataFrame(
        [
            {"User ID": "STU101", "Name": "Alice Smith", "Role": "Student", "Class": "Grade 10-A", "Department": "Academics", "Salary": 0},
            {"User ID": "STU102", "Name": "Bob Jones", "Role": "Student", "Class": "Grade 10-A", "Department": "Academics", "Salary": 0},
            {"User ID": "STU103", "Name": "Charlie Brown", "Role": "Student", "Class": "Grade 10-B", "Department": "Academics", "Salary": 0},
            {"User ID": "TCH201", "Name": "Dr. Sarah Conner", "Role": "Teacher", "Class": "Grade 10-A", "Department": "Science", "Salary": 55000},
            {"User ID": "ADM301", "Name": "HR Admin Office", "Role": "HR / Admin", "Class": "N/A", "Department": "Administration", "Salary": 65000},
        ]
    )

if "attendance_log" not in st.session_state:
    st.session_state.attendance_log = pd.DataFrame(
        columns=["Date", "Timestamp", "User ID", "Name", "Class", "Status", "Logged By"]
    )

if "grades_db" not in st.session_state:
    st.session_state.grades_db = pd.DataFrame(
        [
            {"User ID": "STU101", "Class": "Grade 10-A", "Subject": "Mathematics", "Marks": 95, "Grade": "A+"},
            {"User ID": "STU102", "Class": "Grade 10-A", "Subject": "Mathematics", "Marks": 78, "Grade": "B+"},
            {"User ID": "STU103", "Class": "Grade 10-B", "Subject": "Mathematics", "Marks": 88, "Grade": "A"},
        ]
    )

if "credits_db" not in st.session_state:
    st.session_state.credits_db = pd.DataFrame(
        [
            {"User ID": "STU101", "Class": "Grade 10-A", "Category": "Sports", "Activity": "Football", "Points": 25},
            {"User ID": "STU102", "Class": "Grade 10-A", "Category": "Competition", "Activity": "Science Fair", "Points": 40},
            {"User ID": "STU103", "Class": "Grade 10-B", "Category": "Exams", "Activity": "Math Olympiad", "Points": 30},
        ]
    )

# =========================================================
# NAVIGATION & LOGIN
# =========================================================
st.title("🏫 Integrated HR & School Management System")

all_roles = st.session_state.users["Role"].unique().tolist()
selected_role = st.sidebar.selectbox("Select Portal", all_roles)

filtered_users = st.session_state.users[st.session_state.users["Role"] == selected_role]
user_list = filtered_users["User ID"].tolist()
selected_user_id = st.sidebar.selectbox("Select User Account", user_list)

current_user = filtered_users[filtered_users["User ID"] == selected_user_id].iloc[0]
user_role = current_user["Role"]

st.sidebar.markdown("---")
st.sidebar.write(f"**Logged in as:** {current_user['Name']}")
st.sidebar.write(f"**Role:** {current_user['Role']}")

# =========================================================
# ROLE 1: HR / ADMIN PORTAL
# =========================================================
if user_role == "HR / Admin":
    hr_tab1, hr_tab2, hr_tab3 = st.tabs([
        "👥 Staff & User Management",
        "💼 Payroll & HR Overview",
        "📈 System Analytics & Visualizations"
    ])

    with hr_tab1:
        st.subheader("Add / Register New System User")
        with st.form("add_user_form"):
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                new_id = st.text_input("User ID (e.g., TCH202, STU104)")
                new_name = st.text_input("Full Name")
                new_role = st.selectbox("Role", ["Student", "Teacher", "HR / Admin"])
            with col_u2:
                new_class = st.text_input("Class Assigned (or N/A)", value="Grade 10-A")
                new_dept = st.text_input("Department", value="Academics")
                new_salary = st.number_input("Monthly Salary (0 for Students)", min_value=0, value=0)

            if st.form_submit_button("Register User"):
                if new_id and new_name:
                    new_user_data = pd.DataFrame([{
                        "User ID": new_id, "Name": new_name, "Role": new_role,
                        "Class": new_class, "Department": new_dept, "Salary": new_salary
                    }])
                    st.session_state.users = pd.concat([st.session_state.users, new_user_data], ignore_index=True)
                    st.success(f"Registered {new_name} ({new_id}) successfully!")
                    st.rerun()

        st.divider()
        st.subheader("Current User Directory")
        st.dataframe(st.session_state.users, use_container_width=True)

    with hr_tab2:
        st.subheader("Payroll & Staff Overview")
        staff_df = st.session_state.users[st.session_state.users["Role"] != "Student"]
        
        m1, m2 = st.columns(2)
        m1.metric("Total Active Staff", len(staff_df))
        m2.metric("Monthly Payroll Expense", f"${staff_df['Salary'].sum():,.2f}")

        st.dataframe(staff_df[["User ID", "Name", "Role", "Department", "Salary"]], use_container_width=True)

    with hr_tab3:
        st.subheader("📊 Administrative Data Visualizations")
        
        # Chart 1: Role Distribution
        st.write("**Users Distribution by Role**")
        role_counts = st.session_state.users["Role"].value_counts()
        st.bar_chart(role_counts)

        # Chart 2: Grade Distributions
        if not st.session_state.grades_db.empty:
            st.write("**Academic Performance Distribution across Classes**")
            chart_data = st.session_state.grades_db.pivot_table(
                index="Subject", columns="Class", values="Marks", aggfunc="mean"
            )
            st.line_chart(chart_data)

# =========================================================
# ROLE 2: TEACHER PORTAL
# =========================================================
elif user_role == "Teacher":
    teach_tab1, teach_tab2, teach_tab3, teach_tab4 = st.tabs([
        "📅 Attendance Management",
        "📊 Grade Entry",
        "🏅 Extra-Curricular Credits",
        "🏆 Top Achievers Dashboard"
    ])

    available_classes = sorted(st.session_state.users["Class"].dropna().unique().tolist())

    with teach_tab1:
        st.subheader("Date-Wise Attendance")
        c1, c2 = st.columns(2)
        target_class = c1.selectbox("Select Class", available_classes)
        att_date = c2.date_input("Select Date", value=date.today())

        class_students = st.session_state.users[
            (st.session_state.users["Role"] == "Student") & 
            (st.session_state.users["Class"] == target_class)
        ]

        # FIXED: Changed .empty() to .empty
        if not class_students.empty:
            with st.form("attendance_form"):
                attendance_data = {}
                for idx, row in class_students.iterrows():
                    st_col1, st_col2 = st.columns([2, 1])
                    st_col1.write(f"**{row['Name']}** ({row['User ID']})")
                    attendance_data[row['User ID']] = st_col2.selectbox(
                        "Status", ["Present", "Absent", "Late"], key=f"att_{row['User ID']}"
                    )
                
                if st.form_submit_button("Submit Attendance"):
                    formatted_date = att_date.strftime("%Y-%m-%d")
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    st.session_state.attendance_log = st.session_state.attendance_log[
                        ~((st.session_state.attendance_log["Class"] == target_class) & 
                          (st.session_state.attendance_log["Date"] == formatted_date))
                    ]

                    new_entries = [
                        {
                            "Date": formatted_date, "Timestamp": timestamp, "User ID": sid,
                            "Name": class_students[class_students["User ID"] == sid]["Name"].values[0],
                            "Class": target_class, "Status": status, "Logged By": current_user['Name']
                        }
                        for sid, status in attendance_data.items()
                    ]
                    
                    st.session_state.attendance_log = pd.concat(
                        [st.session_state.attendance_log, pd.DataFrame(new_entries)], ignore_index=True
                    )
                    st.success(f"Attendance recorded for {formatted_date}!")
        else:
            st.info("No students registered in this class.")

    with teach_tab2:
        st.subheader("Grade Entry")
        target_class_g = st.selectbox("Select Class", available_classes, key="grade_class")
        students_g = st.session_state.users[
            (st.session_state.users["Role"] == "Student") & 
            (st.session_state.users["Class"] == target_class_g)
        ]

        # FIXED: Changed .empty() to .empty
        if not students_g.empty:
            col_g1, col_g2 = st.columns(2)
            selected_stu_g = col_g1.selectbox("Select Student", students_g["User ID"].tolist())
            subject = col_g1.text_input("Subject", value="Mathematics")
            marks = col_g2.number_input("Marks (0-100)", min_value=0, max_value=100, value=85)
            grade = col_g2.selectbox("Grade", ["A+", "A", "B+", "B", "C", "D", "F"])

            if st.button("Submit Grade"):
                match_mask = (
                    (st.session_state.grades_db["User ID"] == selected_stu_g) &
                    (st.session_state.grades_db["Subject"].str.lower() == subject.strip().lower())
                )
                if not st.session_state.grades_db[match_mask].empty:
                    idx = st.session_state.grades_db[match_mask].index[0]
                    st.session_state.grades_db.loc[idx, "Marks"] = marks
                    st.session_state.grades_db.loc[idx, "Grade"] = grade
                else:
                    new_grade_row = pd.DataFrame([{
                        "User ID": selected_stu_g, "Class": target_class_g,
                        "Subject": subject.strip(), "Marks": marks, "Grade": grade
                    }])
                    st.session_state.grades_db = pd.concat([st.session_state.grades_db, new_grade_row], ignore_index=True)
                st.success("Grade updated!")
                st.rerun()

    with teach_tab3:
        st.subheader("Extra-Curricular Credits")
        target_class_c = st.selectbox("Select Class", available_classes, key="credit_class")
        students_c = st.session_state.users[
            (st.session_state.users["Role"] == "Student") & 
            (st.session_state.users["Class"] == target_class_c)
        ]

        # FIXED: Changed .empty() to .empty
        if not students_c.empty:
            selected_stu_c = st.selectbox("Select Student", students_c["User ID"].tolist())
            category = st.selectbox("Category", ["Sports", "Arts", "Competitions", "Exams"])
            activity = st.text_input("Activity Name", value="Football Tournament")
            points = st.number_input("Points Awarded", min_value=1, max_value=100, value=10)

            if st.button("Award Points"):
                new_credit = pd.DataFrame([{
                    "User ID": selected_stu_c, "Class": target_class_c,
                    "Category": category, "Activity": activity, "Points": points
                }])
                st.session_state.credits_db = pd.concat([st.session_state.credits_db, new_credit], ignore_index=True)
                st.success("Points awarded!")
                st.rerun()

    with teach_tab4:
        st.subheader("Class Leaderboard")
        selected_lb_class = st.selectbox("Select Class", available_classes, key="lb_class")
        students_lb = st.session_state.users[
            (st.session_state.users["Role"] == "Student") & 
            (st.session_state.users["Class"] == selected_lb_class)
        ]

        # FIXED: Changed .empty() to .empty
        if not students_lb.empty:
            acad_df = st.session_state.grades_db.groupby("User ID")["Marks"].mean().reset_index()
            extra_df = st.session_state.credits_db.groupby("User ID")["Points"].sum().reset_index()

            lb_df = pd.merge(students_lb[["User ID", "Name"]], acad_df, on="User ID", how="left").fillna(0)
            lb_df = pd.merge(lb_df, extra_df, on="User ID", how="left").fillna(0)

            st.dataframe(lb_df, use_container_width=True)

# =========================================================
# ROLE 3: STUDENT PORTAL
# =========================================================
elif user_role == "Student":
    stu_tab1, stu_tab2, stu_tab3 = st.tabs(["👤 Profile & ID", "📊 Academic Marks", "📅 Attendance Record"])
    stu_id = current_user["User ID"]

    with stu_tab1:
        st.subheader(f"Student Card - {current_user['Name']}")
        st.write(f"**ID:** {stu_id} | **Class:** {current_user['Class']}")
        
        payload = f"STUDENT:{stu_id}"
        code_class = barcode.get_barcode_class("code128")
        barcode_img = code_class(payload, writer=ImageWriter())
        buffer = io.BytesIO()
        barcode_img.write(buffer)
        buffer.seek(0)
        st.image(Image.open(buffer), caption="Official Student Barcode")

    with stu_tab2:
        st.subheader("My Marks")
        my_grades = st.session_state.grades_db[st.session_state.grades_db["User ID"] == stu_id]
        st.dataframe(my_grades, use_container_width=True)

    with stu_tab3:
        st.subheader("My Attendance History")
        my_att = st.session_state.attendance_log[st.session_state.attendance_log["User ID"] == stu_id]
        st.dataframe(my_att, use_container_width=True)
