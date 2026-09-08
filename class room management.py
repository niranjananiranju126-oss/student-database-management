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
st.set_page_config(page_title="School Management System", layout="wide")

if "users" not in st.session_state:
    st.session_state.users = pd.DataFrame(
        [
            {"User ID": "STU101", "Name": "Alice Smith", "Role": "Student", "Class": "Grade 10-A"},
            {"User ID": "STU102", "Name": "Bob Jones", "Role": "Student", "Class": "Grade 10-A"},
            {"User ID": "STU103", "Name": "Charlie Brown", "Role": "Student", "Class": "Grade 10-B"},
            {"User ID": "TCH201", "Name": "Dr. Sarah Conner", "Role": "Teacher", "Class": "Grade 10-A"},
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

if "user_photos" not in st.session_state:
    st.session_state.user_photos = {}

# =========================================================
# MAIN APP HEADER & ROLE SELECTOR
# =========================================================
st.title("🎓 Smart School Dashboard & Management Portal")

all_roles = st.session_state.users["Role"].unique().tolist()
selected_role = st.sidebar.selectbox("Select Access Role", all_roles)

filtered_users = st.session_state.users[st.session_state.users["Role"] == selected_role]
user_list = filtered_users["User ID"].tolist()
selected_user_id = st.sidebar.selectbox("Select Account", user_list)

current_user = filtered_users[filtered_users["User ID"] == selected_user_id].iloc[0]
user_role = current_user["Role"]

st.sidebar.markdown("---")
st.sidebar.write(f"**Logged in as:** {current_user['Name']}")
st.sidebar.write(f"**Role:** {current_user['Role']}")

# =========================================================
# ROLE A: TEACHER DASHBOARD
# =========================================================
if user_role == "Teacher":
    teach_tab1, teach_tab2, teach_tab3, teach_tab4 = st.tabs(
        [
            "📅 Date-Wise Attendance",
            "📊 Grade & Marks Entry",
            "🏅 Award Extra-Curricular Credits",
            "🏆 Class Leaderboard & Top Achievers",
        ]
    )

    available_classes = sorted(st.session_state.users["Class"].dropna().unique().tolist())

    # 1. DATE-WISE ATTENDANCE MARKING
    with teach_tab1:
        st.subheader("Attendance Management")
        
        col_att1, col_att2 = st.columns(2)
        with col_att1:
            target_class = st.selectbox("Select Class", available_classes, key="att_class")
        with col_att2:
            att_date = st.date_input("Select Attendance Date", value=date.today())

        class_students = st.session_state.users[
            (st.session_state.users["Role"] == "Student") & 
            (st.session_state.users["Class"] == target_class)
        ]

        if not class_students.empty:
            st.write(f"**Marking Attendance for {target_class} on {att_date.strftime('%Y-%m-%d')}**")
            
            with st.form("manual_attendance_form"):
                attendance_data = {}
                for idx, row in class_students.iterrows():
                    col_s1, col_s2 = st.columns([2, 1])
                    with col_s1:
                        st.write(f"**{row['Name']}** ({row['User ID']})")
                    with col_s2:
                        attendance_data[row['User ID']] = st.selectbox(
                            "Status", 
                            ["Present", "Absent", "Late"], 
                            key=f"status_{row['User ID']}_{att_date}"
                        )
                
                submitted = st.form_submit_button("Save Attendance Records")
                if submitted:
                    formatted_date = att_date.strftime("%Y-%m-%d")
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Remove existing records for this class & date to prevent duplicates
                    st.session_state.attendance_log = st.session_state.attendance_log[
                        ~((st.session_state.attendance_log["Class"] == target_class) & 
                          (st.session_state.attendance_log["Date"] == formatted_date))
                    ]

                    new_entries = []
                    for stu_id, status in attendance_data.items():
                        stu_name = class_students[class_students["User ID"] == stu_id]["Name"].values[0]
                        new_entries.append({
                            "Date": formatted_date,
                            "Timestamp": timestamp,
                            "User ID": stu_id,
                            "Name": stu_name,
                            "Class": target_class,
                            "Status": status,
                            "Logged By": f"Teacher ({current_user['Name']})"
                        })
                    
                    st.session_state.attendance_log = pd.concat(
                        [st.session_state.attendance_log, pd.DataFrame(new_entries)], ignore_index=True
                    )
                    st.success(f"Successfully recorded attendance for {target_class} on {formatted_date}!")

        else:
            st.info("No students enrolled in the selected class.")

        st.divider()
        st.subheader("Attendance Log Viewer")
        filter_class = st.selectbox("Filter Class Log", ["All"] + available_classes)
        if filter_class != "All":
            st.dataframe(
                st.session_state.attendance_log[st.session_state.attendance_log["Class"] == filter_class],
                use_container_width=True
            )
        else:
            st.dataframe(st.session_state.attendance_log, use_container_width=True)

    # 2. GRADE & MARKS UPDATING
    with teach_tab2:
        st.subheader("Enter / Update Student Marks & Grades")
        target_class_g = st.selectbox("Select Class", available_classes, key="grade_class")
        students_g = st.session_state.users[
            (st.session_state.users["Role"] == "Student") & 
            (st.session_state.users["Class"] == target_class_g)
        ]

        if not students_g.empty():
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                selected_stu_g = st.selectbox("Select Student", students_g["User ID"].tolist(), key="grade_stu_select")
                subject = st.text_input("Subject Name", value="Mathematics")
            with col_g2:
                marks = st.number_input("Marks (0 - 100)", min_value=0, max_value=100, value=85)
                grade = st.selectbox("Letter Grade", ["A+", "A", "B+", "B", "C", "D", "F"])

            if st.button("Submit Grade Entry", use_container_width=True):
                match_mask = (
                    (st.session_state.grades_db["User ID"] == selected_stu_g) &
                    (st.session_state.grades_db["Subject"].str.lower() == subject.strip().lower())
                )
                if not st.session_state.grades_db[match_mask].empty:
                    idx = st.session_state.grades_db[match_mask].index[0]
                    st.session_state.grades_db.loc[idx, "Marks"] = marks
                    st.session_state.grades_db.loc[idx, "Grade"] = grade
                    st.session_state.grades_db.loc[idx, "Class"] = target_class_g
                    st.success(f"Updated {subject} marks for {selected_stu_g}!")
                else:
                    new_grade_row = pd.DataFrame([{
                        "User ID": selected_stu_g,
                        "Class": target_class_g,
                        "Subject": subject.strip(),
                        "Marks": marks,
                        "Grade": grade,
                    }])
                    st.session_state.grades_db = pd.concat([st.session_state.grades_db, new_grade_row], ignore_index=True)
                    st.success(f"Added {subject} grade for {selected_stu_g}!")
                st.rerun()

            st.divider()
            st.subheader("Academic Grade Database")
            st.dataframe(st.session_state.grades_db[st.session_state.grades_db["Class"] == target_class_g], use_container_width=True)
        else:
            st.info("No students found in this class.")

    # 3. AWARD EXTRA-CURRICULAR CREDITS
    with teach_tab3:
        st.subheader("Award Extra-Curricular Credits & Points")
        target_class_c = st.selectbox("Select Class", available_classes, key="credit_class")
        students_c = st.session_state.users[
            (st.session_state.users["Role"] == "Student") & 
            (st.session_state.users["Class"] == target_class_c)
        ]

        if not students_c.empty():
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                selected_stu_c = st.selectbox("Select Student", students_c["User ID"].tolist(), key="credit_stu_select")
                category = st.selectbox("Credit Category", ["Sports", "Competition", "Exams", "Arts", "Community Service"])
            with col_c2:
                activity = st.text_input("Activity / Event Name", value="Science Exhibition")
                points = st.number_input("Points Awarded", min_value=1, max_value=100, value=10)

            if st.button("Award Credits", use_container_width=True):
                new_credit_row = pd.DataFrame([{
                    "User ID": selected_stu_c,
                    "Class": target_class_c,
                    "Category": category,
                    "Activity": activity.strip(),
                    "Points": points,
                }])
                st.session_state.credits_db = pd.concat([st.session_state.credits_db, new_credit_row], ignore_index=True)
                st.success(f"Awarded {points} pts to {selected_stu_c} for '{activity}'!")
                st.rerun()

            st.divider()
            st.subheader("Activity Credits Log")
            st.dataframe(st.session_state.credits_db[st.session_state.credits_db["Class"] == target_class_c], use_container_width=True)
        else:
            st.info("No students found in this class.")

    # 4. CLASS LEADERBOARD & TOP ACHIEVERS
    with teach_tab4:
        st.subheader("🏆 Top Achievers Dashboard")
        selected_leaderboard_class = st.selectbox("Filter Class Leaderboard", available_classes, key="lb_class")

        students_in_lb = st.session_state.users[
            (st.session_state.users["Role"] == "Student") & 
            (st.session_state.users["Class"] == selected_leaderboard_class)
        ]

        if not students_in_lb.empty:
            # Academic Aggregates
            acad_df = st.session_state.grades_db.groupby("User ID")["Marks"].mean().reset_index()
            acad_df.rename(columns={"Marks": "Academic Average (%)"}, inplace=True)

            # Extra-Curricular Aggregates
            extra_df = st.session_state.credits_db.groupby("User ID")["Points"].sum().reset_index()
            extra_df.rename(columns={"Points": "Total Activity Points"}, inplace=True)

            # Merge with student profiles
            lb_df = pd.merge(students_in_lb[["User ID", "Name", "Class"]], acad_df, on="User ID", how="left").fillna(0)
            lb_df = pd.merge(lb_df, extra_df, on="User ID", how="left").fillna(0)

            # Highlighting Top Achievers
            top_academic = lb_df.loc[lb_df["Academic Average (%)"].idxmax()] if not lb_df.empty else None
            top_extra = lb_df.loc[lb_df["Total Activity Points"].idxmax()] if not lb_df.empty else None

            col_top1, col_top2 = st.columns(2)
            with col_top1:
                st.metric(
                    label="🥇 Top Academic Achiever",
                    value=f"{top_academic['Name']}" if top_academic is not None else "N/A",
                    delta=f"{top_academic['Academic Average (%)']:.1f}% Avg" if top_academic is not None else ""
                )
            with col_top2:
                st.metric(
                    label="🌟 Top Extra-Curricular Achiever",
                    value=f"{top_extra['Name']}" if top_extra is not None else "N/A",
                    delta=f"{top_extra['Total Activity Points']} Points" if top_extra is not None else ""
                )

            st.divider()
            st.write(f"**Complete Class Leaderboard for {selected_leaderboard_class}**")
            st.dataframe(lb_df.sort_values(by="Academic Average (%)", ascending=False), use_container_width=True)
        else:
            st.info("No data available for this class.")

# =========================================================
# ROLE B: STUDENT DASHBOARD
# =========================================================
elif user_role == "Student":
    stu_tab1, stu_tab2, stu_tab3, stu_tab4 = st.tabs(
        [
            "👤 My Profile & Digital ID",
            "📊 My Grades & Academics",
            "🏅 My Extra-Curricular Credits",
            "📅 My Attendance Record",
        ]
    )

    stu_id = current_user["User ID"]

    # 1. PROFILE & BARCODE CARD
    with stu_tab1:
        st.subheader("Student Digital Identity Card")
        col_p1, col_p2 = st.columns(2)

        with col_p1:
            st.write(f"**Name:** {current_user['Name']}")
            st.write(f"**User ID:** {stu_id}")
            st.write(f"**Class:** {current_user['Class']}")
            st.write(f"**Role:** {current_user['Role']}")

        with col_p2:
            payload = f"STUDENT:{stu_id}"
            code_class = barcode.get_barcode_class("code128")
            barcode_img = code_class(payload, writer=ImageWriter())

            buffer = io.BytesIO()
            barcode_img.write(buffer)
            buffer.seek(0)

            st.image(
                Image.open(buffer),
                caption="Official Student Barcode Card",
                use_container_width=True,
            )

    # 2. GRADES & ACADEMICS
    with stu_tab2:
        st.subheader("Academic Marksheet")
        my_grades = st.session_state.grades_db[st.session_state.grades_db["User ID"] == stu_id]

        if not my_grades.empty:
            st.dataframe(my_grades[["Subject", "Marks", "Grade"]], use_container_width=True)
            avg_m = my_grades["Marks"].mean()
            st.metric("Academic Average", f"{avg_m:.1f}%")
        else:
            st.info("No academic records found for your ID.")

    # 3. EXTRA-CURRICULAR CREDITS
    with stu_tab3:
        st.subheader("Earned Extra-Curricular Credits")
        my_credits = st.session_state.credits_db[st.session_state.credits_db["User ID"] == stu_id]

        if not my_credits.empty:
            st.dataframe(my_credits[["Category", "Activity", "Points"]], use_container_width=True)
            total_pts = my_credits["Points"].sum()
            st.metric("Total Credits Earned", f"{total_pts} Points")
        else:
            st.info("No extra-curricular credits recorded yet.")

    # 4. ATTENDANCE RECORD
    with stu_tab4:
        st.subheader("My Attendance History")
        my_att = st.session_state.attendance_log[st.session_state.attendance_log["User ID"] == stu_id]

        if not my_att.empty:
            st.dataframe(my_att[["Date", "Status", "Logged By"]].sort_values(by="Date", ascending=False), use_container_width=True)
            total = len(my_att)
            present_cnt = len(my_att[my_att["Status"].isin(["Present", "Late"])])
            pct = (present_cnt / total) * 100
            st.metric("Overall Attendance Rate", f"{pct:.1f}%")
        else:
            st.info("No attendance entries found.")
