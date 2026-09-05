from datetime import datetime
import io

import barcode
from barcode.writer import ImageWriter
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st
import zxingcpp

# Page Config
st.set_page_config(
    page_title="Role-Based Attendance, Performance & Ranking System",
    page_icon="🎓",
    layout="wide",
)

# ---------------------------------------------------------
# DATABASE INITIALIZATION IN SESSION STATE
# ---------------------------------------------------------
if "users" not in st.session_state:
    st.session_state.users = pd.DataFrame(
        [
            {
                "User ID": "ADM001",
                "Name": "System Administrator",
                "Role": "Admin",
                "Pin": "1234",
                "Photo": None,
                "Grade": "N/A",
            },
            {
                "User ID": "TEA201",
                "Name": "Priya Sharma",
                "Role": "Teacher",
                "Pin": "1234",
                "Photo": None,
                "Grade": "N/A",
            },
            {
                "User ID": "STU101",
                "Name": "Aarav Patel",
                "Role": "Student",
                "Pin": "1234",
                "Photo": None,
                "Grade": "A+",
            },
            {
                "User ID": "STU102",
                "Name": "Diya Sengupta",
                "Role": "Student",
                "Pin": "1234",
                "Photo": None,
                "Grade": "A",
            },
            {
                "User ID": "STU103",
                "Name": "Rohan Verma",
                "Role": "Student",
                "Pin": "1234",
                "Photo": None,
                "Grade": "B+",
            },
        ]
    )

if "attendance_log" not in st.session_state:
    st.session_state.attendance_log = pd.DataFrame(
        [
            {
                "Timestamp": "2026-08-15 09:00:00",
                "User ID": "STU101",
                "Name": "Aarav Patel",
                "Status": "Present",
                "Logged By": "Barcode Scan",
            },
            {
                "Timestamp": "2026-08-15 09:05:00",
                "User ID": "STU102",
                "Name": "Diya Sengupta",
                "Status": "Present",
                "Logged By": "Barcode Scan",
            },
            {
                "Timestamp": "2026-08-15 09:10:00",
                "User ID": "STU103",
                "Name": "Rohan Verma",
                "Status": "Late",
                "Logged By": "Teacher Scan",
            },
        ]
    )

if "grades_db" not in st.session_state:
    st.session_state.grades_db = pd.DataFrame(
        [
            {
                "User ID": "STU101",
                "Subject": "Mathematics",
                "Marks": 95,
                "Grade": "A+",
            },
            {
                "User ID": "STU101",
                "Subject": "Science",
                "Marks": 92,
                "Grade": "A+",
            },
            {
                "User ID": "STU102",
                "Subject": "Mathematics",
                "Marks": 88,
                "Grade": "A",
            },
            {
                "User ID": "STU102",
                "Subject": "Science",
                "Marks": 85,
                "Grade": "A",
            },
            {
                "User ID": "STU103",
                "Subject": "Mathematics",
                "Marks": 74,
                "Grade": "B",
            },
            {
                "User ID": "STU103",
                "Subject": "Science",
                "Marks": 78,
                "Grade": "B+",
            },
        ]
    )

if "credits_db" not in st.session_state:
    st.session_state.credits_db = pd.DataFrame(
        [
            {
                "User ID": "STU101",
                "Category": "Sports",
                "Activity": "Inter-School Basketball",
                "Points": 25,
            },
            {
                "User ID": "STU101",
                "Category": "Exams",
                "Activity": "Math Olympiad",
                "Points": 20,
            },
            {
                "User ID": "STU102",
                "Category": "Competition",
                "Activity": "Science Exhibition 1st Place",
                "Points": 30,
            },
            {
                "User ID": "STU103",
                "Category": "Sports",
                "Activity": "Annual Athletic Meet",
                "Points": 15,
            },
        ]
    )

if "logged_user" not in st.session_state:
    st.session_state.logged_user = None

if "user_photos" not in st.session_state:
    st.session_state.user_photos = {}


# Helper: Authenticate user by ID
def authenticate_user(user_id):
    matched = st.session_state.users[
        st.session_state.users["User ID"] == user_id.strip()
    ]
    if not matched.empty:
        return matched.iloc[0].to_dict()
    return None


# Helper: Decode scanned barcode payload
def process_barcode_image(image):
    results = zxingcpp.read_barcodes(image)
    if results:
        for item in results:
            payload = item.text
            parts = payload.split(":")
            if len(parts) >= 2:
                return parts[1]
            return payload
    return None


# Helper: Calculate Student Performance Leaderboard
def calculate_leaderboard():
    students = st.session_state.users[
        st.session_state.users["Role"] == "Student"
    ].copy()
    if students.empty:
        return pd.DataFrame()

    leaderboard_data = []

    for _, stu in students.iterrows():
        uid = stu["User ID"]

        # 1. Attendance %
        stu_att = st.session_state.attendance_log[
            st.session_state.attendance_log["User ID"] == uid
        ]
        total_att = len(stu_att)
        presents = len(
            stu_att[stu_att["Status"].isin(["Present", "Late"])]
        )
        att_pct = (presents / total_att * 100) if total_att > 0 else 100.0

        # 2. Academic Average Marks
        stu_grades = st.session_state.grades_db[
            st.session_state.grades_db["User ID"] == uid
        ]
        avg_marks = (
            stu_grades["Marks"].mean() if not stu_grades.empty else 0.0
        )

        # 3. Credits Breakdown
        stu_credits = st.session_state.credits_db[
            st.session_state.credits_db["User ID"] == uid
        ]
        sports_pts = stu_credits[stu_credits["Category"] == "Sports"][
            "Points"
        ].sum()
        comp_pts = stu_credits[stu_credits["Category"] == "Competition"][
            "Points"
        ].sum()
        exam_pts = stu_credits[stu_credits["Category"] == "Exams"][
            "Points"
        ].sum()
        total_credits = sports_pts + comp_pts + exam_pts

        # Overall Weighted Composite Score: 50% Academics + 30% Attendance + 20% Credits (capped at 50 points max)
        credit_score = min(total_credits, 50) * 2  # scaled to 100
        composite_score = (
            (avg_marks * 0.50) + (att_pct * 0.30) + (credit_score * 0.20)
        )

        leaderboard_data.append(
            {
                "Rank": 0,
                "User ID": uid,
                "Name": stu["Name"],
                "Composite Score": round(composite_score, 1),
                "Academic Avg (%)": round(avg_marks, 1),
                "Attendance (%)": round(att_pct, 1),
                "Total Credits": total_credits,
                "Sports Pts": sports_pts,
                "Competition Pts": comp_pts,
                "Exam Pts": exam_pts,
            }
        )

    df_lb = pd.DataFrame(leaderboard_data)
    df_lb = df_lb.sort_values(
        by="Composite Score", ascending=False
    ).reset_index(drop=True)
    df_lb["Rank"] = df_lb.index + 1
    return df_lb


# ---------------------------------------------------------
# VIEW 1: LOGIN SCREEN
# ---------------------------------------------------------
if st.session_state.logged_user is None:
    st.title("🎓 Portal Login System")
    st.caption(
        "Scan your official barcode card or enter credentials to access your portal."
    )

    login_tab1, login_tab2 = st.tabs(
        ["📷 Barcode Scan Login", "🔑 Manual Login"]
    )

    with login_tab1:
        st.subheader("Scan Barcode Card to Login")
        scan_source = st.radio(
            "Scan Option",
            ["Webcam Scanner", "Upload Barcode Image"],
            horizontal=True,
        )

        img_input = None
        if scan_source == "Webcam Scanner":
            cam_file = st.camera_input("Hold Barcode up to Camera")
            if cam_file:
                img_input = Image.open(cam_file)
        else:
            up_file = st.file_uploader(
                "Upload Barcode File", type=["png", "jpg", "jpeg"]
            )
            if up_file:
                img_input = Image.open(up_file)

        if img_input is not None:
            extracted_id = process_barcode_image(img_input)
            if extracted_id:
                user_info = authenticate_user(extracted_id)
                if user_info:
                    st.session_state.logged_user = user_info
                    st.success(
                        f"Welcome back, {user_info['Name']} ({user_info['Role']})!"
                    )
                    st.rerun()
                else:
                    st.error(
                        f"User ID '{extracted_id}' recognized from barcode, but not found in user database."
                    )
            else:
                st.error("No clear barcode could be decoded from the image.")

    with login_tab2:
        st.subheader("Manual Credential Entry")
        input_id = st.text_input("User ID", value="")
        input_pin = st.text_input("PIN / Password", type="password", value="")

        if st.button("Log In", use_container_width=True):
            user_info = authenticate_user(input_id)
            if user_info and str(user_info["Pin"]) == input_pin.strip():
                st.session_state.logged_user = user_info
                st.success(f"Login successful as {user_info['Name']}!")
                st.rerun()
            else:
                st.error("Invalid User ID or PIN. Please try again.")

# ---------------------------------------------------------
# VIEW 2: AUTHENTICATED DASHBOARDS
# ---------------------------------------------------------
else:
    current_user = st.session_state.logged_user
    user_role = current_user["Role"]

    # Top Banner Header
    header_col1, header_col2 = st.columns([4, 1])
    with header_col1:
        st.title(f"{user_role} Dashboard")
        st.caption(
            f"Logged in as **{current_user['Name']}** (ID: `{current_user['User ID']}`)"
        )
    with header_col2:
        st.write(" ")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_user = None
            st.rerun()

    # ---------------------------------------------------------
    # TOP RANKED STUDENT TICKER BANNER (FLOWS THROUGHOUT DASHBOARD)
    # ---------------------------------------------------------
    df_leaderboard = calculate_leaderboard()
    if not df_leaderboard.empty:
        top_student = df_leaderboard.iloc[0]
        st.info(
            f"🏆 **Top Ranked Student Overall:** **{top_student['Name']}** (`{top_student['User ID']}`) | "
            f"Composite Performance Score: **{top_student['Composite Score']} pts** | "
            f"Academics: **{top_student['Academic Avg (%)']}%** | "
            f"Attendance: **{top_student['Attendance (%)']}%** | "
            f"Total Credits: **{top_student['Total Credits']} pts**"
        )
    st.divider()

    # =========================================================
    # ROLE A: ADMIN DASHBOARD
    # =========================================================
    if user_role == "Admin":
        admin_tab1, admin_tab2, admin_tab3, admin_tab4, admin_tab5 = (
            st.tabs(
                [
                    "👤 User Registration",
                    "✏️ Modify / Edit Users",
                    "🏷️ Barcode Generator",
                    "🏆 Global Performance Analytics",
                    "📊 System Overview",
                ]
            )
        )

        # 1. USER REGISTRATION
        with admin_tab1:
            st.subheader("Register New User & Attach Profile Photo")
            col_a, col_b = st.columns(2)

            with col_a:
                new_role = st.selectbox(
                    "Assign Role", ["Teacher", "Student", "Admin"]
                )
                new_id = st.text_input("Assign User ID (e.g. STU104 Or TEA102)", value="")
                new_name = st.text_input("Full Name", value="")
                new_pin = st.text_input(
                    "Set Default PIN", value="1234", type="password"
                )

            with col_b:
                photo_file = st.file_uploader(
                    "Upload Official Photo", type=["jpg", "jpeg", "png"]
                )
                if photo_file:
                    st.image(
                        Image.open(photo_file),
                        width=120,
                        caption="Photo Preview",
                    )

            if st.button("Register & Grant Access", use_container_width=True):
                if new_id.strip() and new_name.strip():
                    if (
                        new_id.strip()
                        not in st.session_state.users["User ID"].values
                    ):
                        new_row = pd.DataFrame(
                            [
                                {
                                    "User ID": new_id.strip(),
                                    "Name": new_name.strip(),
                                    "Role": new_role,
                                    "Pin": new_pin.strip(),
                                    "Photo": photo_file.name
                                    if photo_file
                                    else None,
                                    "Grade": "N/A",
                                }
                            ]
                        )
                        st.session_state.users = pd.concat(
                            [st.session_state.users, new_row],
                            ignore_index=True,
                        )

                        if photo_file:
                            st.session_state.user_photos[new_id.strip()] = (
                                Image.open(photo_file)
                            )

                        st.success(
                            f"Successfully registered {new_role}: {new_name} ({new_id})"
                        )
                        st.rerun()
                    else:
                        st.warning("User ID already exists.")
                else:
                    st.warning("Please fill out Name and User ID.")

        # 2. MODIFY / EDIT USER DETAILS
        with admin_tab2:
            st.subheader("Modify Existing Student & Teacher Details")
            all_user_ids = st.session_state.users["User ID"].tolist()
            target_user_id = st.selectbox(
                "Select User to Edit", all_user_ids, key="edit_selector"
            )

            idx = st.session_state.users[
                st.session_state.users["User ID"] == target_user_id
            ].index[0]
            curr_row = st.session_state.users.loc[idx]

            col_edit1, col_edit2 = st.columns(2)

            with col_edit1:
                edit_name = st.text_input(
                    "Full Name", value=str(curr_row["Name"])
                )
                role_options = ["Student", "Teacher", "Admin"]
                edit_role = st.selectbox(
                    "Role",
                    role_options,
                    index=role_options.index(curr_row["Role"]),
                )
                edit_pin = st.text_input(
                    "PIN / Password", value=str(curr_row["Pin"])
                )

                if edit_role == "Student":
                    edit_grade = st.text_input(
                        "Overall Grade Summary", value=str(curr_row["Grade"])
                    )
                else:
                    edit_grade = "N/A"

            with col_edit2:
                st.write("**Current Profile Photo:**")
                if target_user_id in st.session_state.user_photos:
                    st.image(
                        st.session_state.user_photos[target_user_id],
                        width=120,
                    )
                else:
                    st.info("No profile photo attached.")

                new_photo = st.file_uploader(
                    "Replace Profile Photo",
                    type=["jpg", "jpeg", "png"],
                    key="edit_photo",
                )

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("💾 Save Changes", use_container_width=True):
                    st.session_state.users.loc[idx, "Name"] = edit_name.strip()
                    st.session_state.users.loc[idx, "Role"] = edit_role
                    st.session_state.users.loc[idx, "Pin"] = edit_pin.strip()
                    st.session_state.users.loc[idx, "Grade"] = edit_grade

                    if new_photo:
                        st.session_state.user_photos[target_user_id] = (
                            Image.open(new_photo)
                        )

                    st.success(
                        f"Updated details for **{edit_name}** (`{target_user_id}`)!"
                    )
                    st.rerun()

            with btn_col2:
                if st.button(
                    "🗑️ Delete User", type="primary", use_container_width=True
                ):
                    if target_user_id == current_user["User ID"]:
                        st.error(
                            "You cannot delete your own logged-in Admin account."
                        )
                    else:
                        st.session_state.users = st.session_state.users.drop(
                            idx
                        ).reset_index(drop=True)
                        if target_user_id in st.session_state.user_photos:
                            del st.session_state.user_photos[target_user_id]
                        st.success(f"User {target_user_id} removed.")
                        st.rerun()

            st.divider()
            st.subheader("All System Users")
            st.dataframe(
                st.session_state.users[
                    ["User ID", "Name", "Role", "Pin", "Grade"]
                ],
                use_container_width=True,
            )

        # 3. BARCODE GENERATOR
        with admin_tab3:
            st.subheader("Generate ID Barcode Card")
            user_list = st.session_state.users["User ID"].tolist()
            selected_user_id = st.selectbox(
                "Select User", user_list, key="bc_select"
            )

            selected_row = st.session_state.users[
                st.session_state.users["User ID"] == selected_user_id
            ].iloc[0]

            col_bc1, col_bc2 = st.columns(2)
            with col_bc1:
                st.write(f"**Name:** {selected_row['Name']}")
                st.write(f"**Role:** {selected_row['Role']}")

                if selected_user_id in st.session_state.user_photos:
                    st.image(
                        st.session_state.user_photos[selected_user_id],
                        width=140,
                        caption="Official Photo",
                    )

            with col_bc2:
                payload = (
                    f"{selected_row['Role'].upper()}:{selected_user_id.strip()}"
                )
                code_class = barcode.get_barcode_class("code128")
                barcode_img = code_class(payload, writer=ImageWriter())

                buffer = io.BytesIO()
                barcode_img.write(buffer)
                buffer.seek(0)

                st.image(
                    Image.open(buffer),
                    caption=f"Barcode for {selected_row['Name']}",
                    use_container_width=True,
                )
                st.download_button(
                    label=f"Download Barcode Card ({selected_user_id})",
                    data=buffer.getvalue(),
                    file_name=f"barcode_{selected_user_id}.png",
                    mime="image/png",
                    use_container_width=True,
                )

        # 4. GLOBAL PERFORMANCE ANALYTICS (NEW)
        with admin_tab4:
            st.subheader("📈 Integrated Student Performance & Rankings")
            if not df_leaderboard.empty:
                st.dataframe(
                    df_leaderboard[
                        [
                            "Rank",
                            "Name",
                            "User ID",
                            "Composite Score",
                            "Academic Avg (%)",
                            "Attendance (%)",
                            "Total Credits",
                            "Sports Pts",
                            "Competition Pts",
                            "Exam Pts",
                        ]
                    ],
                    use_container_width=True,
                )

                # Analytical Multi-Bar Graph
                st.subheader(
                    "Comparative Analytics: Academics vs Attendance vs Credits"
                )
                fig, ax = plt.subplots(figsize=(10, 4))
                x = np.arange(len(df_leaderboard))
                width = 0.25

                ax.bar(
                    x - width,
                    df_leaderboard["Academic Avg (%)"],
                    width,
                    label="Academic Avg (%)",
                    color="#4F46E5",
                )
                ax.bar(
                    x,
                    df_leaderboard["Attendance (%)"],
                    width,
                    label="Attendance (%)",
                    color="#10B981",
                )
                ax.bar(
                    x + width,
                    df_leaderboard["Total Credits"],
                    width,
                    label="Total Credits (pts)",
                    color="#F59E0B",
                )

                ax.set_ylabel("Scores / Points")
                ax.set_title("Student Comparison Breakdown")
                ax.set_xticks(x)
                ax.set_xticklabels(df_leaderboard["Name"])
                ax.legend()
                st.pyplot(fig)
            else:
                st.info("No student data available for ranking.")

        # 5. SYSTEM OVERVIEW
        with admin_tab5:
            st.subheader("System Metrics")
            m1, m2, m3 = st.columns(3)
            m1.metric(
                "Total Users", len(st.session_state.users), delta="Active"
            )
            m2.metric(
                "Total Students",
                len(
                    st.session_state.users[
                        st.session_state.users["Role"] == "Student"
                    ]
                ),
            )
            m3.metric(
                "Attendance Logs", len(st.session_state.attendance_log)
            )

    # =========================================================
    # ROLE B: TEACHER DASHBOARD
    # =========================================================
    elif user_role == "Teacher":
        teach_tab1, teach_tab2, teach_tab3, teach_tab4 = st.tabs(
            [
                "📝 Attendance Management",
                "📚 Grade & Marks Updating",
                "🏅 Award Credits (Sports/Comp/Exams)",
                "📈 Student Performance Analytics",
            ]
        )

        # 1. ATTENDANCE LOGGING
        with teach_tab1:
            st.subheader("Record Student Attendance")
            att_mode = st.radio(
                "Entry Method",
                ["Manual Selection", "Barcode Scan"],
                horizontal=True,
            )

            if att_mode == "Manual Selection":
                students = st.session_state.users[
                    st.session_state.users["Role"] == "Student"
                ]
                if not students.empty:
                    selected_stu = st.selectbox(
                        "Select Student", students["User ID"].tolist()
                    )
                    status = st.selectbox(
                        "Attendance Status", ["Present", "Late", "Absent"]
                    )

                    if st.button("Log Attendance"):
                        stu_info = students[
                            students["User ID"] == selected_stu
                        ].iloc[0]
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        new_entry = pd.DataFrame(
                            [
                                {
                                    "Timestamp": timestamp,
                                    "User ID": selected_stu,
                                    "Name": stu_info["Name"],
                                    "Status": status,
                                    "Logged By": f"Teacher ({current_user['Name']})",
                                }
                            ]
                        )
                        st.session_state.attendance_log = pd.concat(
                            [st.session_state.attendance_log, new_entry],
                            ignore_index=True,
                        )
                        st.success(
                            f"Recorded '{status}' for {stu_info['Name']} at {timestamp}"
                        )
                        st.rerun()
                else:
                    st.info("No registered students found.")
            else:
                st.caption("Scan Student's Barcode to drop attendance")
                scan_file = st.file_uploader(
                    "Upload Barcode Image", type=["png", "jpg", "jpeg"]
                )
                if scan_file:
                    scanned_id = process_barcode_image(Image.open(scan_file))
                    if scanned_id:
                        stu_match = st.session_state.users[
                            (st.session_state.users["User ID"] == scanned_id)
                            & (st.session_state.users["Role"] == "Student")
                        ]
                        if not stu_match.empty:
                            stu_name = stu_match.iloc[0]["Name"]
                            timestamp = datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                            new_entry = pd.DataFrame(
                                [
                                    {
                                        "Timestamp": timestamp,
                                        "User ID": scanned_id,
                                        "Name": stu_name,
                                        "Status": "Present",
                                        "Logged By": "Teacher Barcode Scan",
                                    }
                                ]
                            )
                            st.session_state.attendance_log = pd.concat(
                                [st.session_state.attendance_log, new_entry],
                                ignore_index=True,
                            )
                            st.success(
                                f"Attendance marked 'Present' for {stu_name}!"
                            )
                            st.rerun()
                        else:
                            st.error(
                                "Scanned barcode is not a registered student."
                            )

        # 2. GRADE ENTRY
        with teach_tab2:
            st.subheader("Update Student Marks & Grades")
            students = st.session_state.users[
                st.session_state.users["Role"] == "Student"
            ]
            if not students.empty:
                stu_id = st.selectbox(
                    "Select Student ID", students["User ID"].tolist()
                )
                subject = st.text_input(
                    "Subject Name (e.g., Mathematics)", value=""
                )
                marks = st.number_input(
                    "Marks Obtained (0-100)", min_value=0, max_value=100, value=75
                )
                grade_letter = st.selectbox(
                    "Grade", ["A+", "A", "B+", "B", "C", "D", "F"]
                )

                if st.button("Submit Grade Record"):
                    if subject.strip():
                        grade_entry = pd.DataFrame(
                            [
                                {
                                    "User ID": stu_id,
                                    "Subject": subject.strip(),
                                    "Marks": marks,
                                    "Grade": grade_letter,
                                }
                            ]
                        )
                        st.session_state.grades_db = pd.concat(
                            [st.session_state.grades_db, grade_entry],
                            ignore_index=True,
                        )
                        st.success(
                            f"Added {subject} marks for student {stu_id}."
                        )
                        st.rerun()
                    else:
                        st.warning("Please enter a subject name.")

        # 3. AWARD CREDITS (NEW)
        with teach_tab3:
            st.subheader("🏅 Log Credits (Sports, Competition, Exams)")
            students = st.session_state.users[
                st.session_state.users["Role"] == "Student"
            ]
            if not students.empty:
                c_stuid = st.selectbox(
                    "Select Student",
                    students["User ID"].tolist(),
                    key="credit_stu",
                )
                c_category = st.selectbox(
                    "Credit Category", ["Sports", "Competition", "Exams"]
                )
                c_activity = st.text_input(
                    "Activity Description",
                    placeholder="e.g. State Level Swimming Competition",
                )
                c_points = st.number_input(
                    "Credit Points Awarded", min_value=1, max_value=50, value=10
                )

                if st.button("Award Credit Points"):
                    if c_activity.strip():
                        c_entry = pd.DataFrame(
                            [
                                {
                                    "User ID": c_stuid,
                                    "Category": c_category,
                                    "Activity": c_activity.strip(),
                                    "Points": c_points,
                                }
                            ]
                        )
                        st.session_state.credits_db = pd.concat(
                            [st.session_state.credits_db, c_entry],
                            ignore_index=True,
                        )
                        st.success(
                            f"Awarded {c_points} points in {c_category} to `{c_stuid}`!"
                        )
                        st.rerun()
                    else:
                        st.warning("Please enter an activity description.")

            st.divider()
            st.subheader("All Student Activity Credits Logged")
            st.dataframe(st.session_state.credits_db, use_container_width=True)

        # 4. TEACHER ANALYTICS & LEADERBOARD (NEW)
        with teach_tab4:
            st.subheader("Class Leaderboard & Analytical Graph")
            if not df_leaderboard.empty:
                st.dataframe(
                    df_leaderboard[
                        [
                            "Rank",
                            "Name",
                            "Composite Score",
                            "Academic Avg (%)",
                            "Attendance (%)",
                            "Total Credits",
                        ]
                    ],
                    use_container_width=True,
                )

                fig, ax = plt.subplots(figsize=(8, 3.5))
                ax.barh(
                    df_leaderboard["Name"],
                    df_leaderboard["Composite Score"],
                    color="#6366F1",
                )
                ax.set_xlabel("Composite Performance Score")
                ax.set_title("Overall Student Ranking Index")
                ax.invert_yaxis()
                st.pyplot(fig)

    # =========================================================
    # ROLE C: STUDENT DASHBOARD
    # =========================================================
    elif user_role == "Student":
        st.subheader(f"Welcome to your Academic Portal, {current_user['Name']}")

        # Retrieve student performance rank from calculation
        stu_rank_info = (
            df_leaderboard[
                df_leaderboard["User ID"] == current_user["User ID"]
            ]
            if not df_leaderboard.empty
            else None
        )

        # Student Profile Card with Photo
        card_col1, card_col2 = st.columns([1, 3])
        with card_col1:
            if current_user["User ID"] in st.session_state.user_photos:
                st.image(
                    st.session_state.user_photos[current_user["User ID"]],
                    width=150,
                    caption="Student Profile Photo",
                )
            else:
                st.info("📷 No Photo Uploaded")

        with card_col2:
            m_col1, m_col2, m_col3 = st.columns(3)
            if stu_rank_info is not None and not stu_rank_info.empty:
                r_data = stu_rank_info.iloc[0]
                m_col1.metric("Your Class Rank", f"#{r_data['Rank']}")
                m_col2.metric("Composite Score", f"{r_data['Composite Score']}")
                m_col3.metric("Total Credits", f"{r_data['Total Credits']} pts")

            st.write(f"**Student ID:** `{current_user['User ID']}`")
            st.write(f"**Official Role:** {current_user['Role']}")

        st.divider()

        # Student Navigation Tabs
        stu_tab1, stu_tab2, stu_tab3 = st.tabs(
            [
                "📊 Marks & Subject Score",
                "🏆 Credits & Accomplishments",
                "📅 Detailed Attendance Log",
            ]
        )

        with stu_tab1:
            st.subheader("Your Subject Grades")
            stu_grades = st.session_state.grades_db[
                st.session_state.grades_db["User ID"] == current_user["User ID"]
            ]

            if not stu_grades.empty:
                st.dataframe(
                    stu_grades[["Subject", "Marks", "Grade"]],
                    use_container_width=True,
                )

                fig, ax = plt.subplots(figsize=(6, 2.5))
                ax.bar(
                    stu_grades["Subject"],
                    stu_grades["Marks"],
                    color="#6366F1",
                )
                ax.set_ylim(0, 100)
                ax.set_ylabel("Marks")
                ax.set_title("Subject Score Performance")
                st.pyplot(fig)
            else:
                st.info("No grade records entered yet by your teacher.")

        with stu_tab2:
            st.subheader("Your Credits (Sports, Competitions, Exams)")
            stu_credits = st.session_state.credits_db[
                st.session_state.credits_db["User ID"]
                == current_user["User ID"]
            ]

            if not stu_credits.empty:
                st.dataframe(
                    stu_credits[["Category", "Activity", "Points"]],
                    use_container_width=True,
                )

                # Category Breakdown Chart
                cat_summary = stu_credits.groupby("Category")["Points"].sum()
                fig, ax = plt.subplots(figsize=(5, 3))
                ax.pie(
                    cat_summary,
                    labels=cat_summary.index,
                    autopct="%1.1f%%",
                    colors=["#10B981", "#F59E0B", "#6366F1"],
                )
                ax.set_title("Credit Points Distribution")
                st.pyplot(fig)
            else:
                st.info("No activity credits awarded yet.")

        with stu_tab3:
            st.subheader("Your Attendance History")
            stu_logs = st.session_state.attendance_log[
                st.session_state.attendance_log["User ID"]
                == current_user["User ID"]
            ]
            if not stu_logs.empty:
                st.dataframe(
                    stu_logs[["Timestamp", "Status", "Logged By"]],
                    use_container_width=True,
                )
            else:
                st.info("No attendance entries recorded yet.")
