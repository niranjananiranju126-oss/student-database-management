from datetime import datetime
import io
import barcode
from barcode.writer import ImageWriter
import pandas as pd
from PIL import Image
import streamlit as st
import zxingcpp

# Page Config
st.set_page_config(
    page_title="Student Attendance & Grade Management",
    page_icon="🎓",
    layout="wide",
)

# ---------------------------------------------------------
# IN-MEMORY DATABASE INITIALIZATION
# ---------------------------------------------------------
if "users" not in st.session_state:
    st.session_state.users = pd.DataFrame(
        [
            {
                "User ID": "STU101",
                "Name": "Aarav Sharma",
                "Role": "Student",
                "Grade": "A",
            },
            {
                "User ID": "TEA201",
                "Name": "Priya Nair",
                "Role": "Teacher",
                "Grade": "N/A",
            },
        ]
    )

if "attendance_log" not in st.session_state:
    st.session_state.attendance_log = pd.DataFrame(
        columns=["Timestamp", "User ID", "Name", "Role", "Entry Type"]
    )

st.title("🎓 Student Attendance & Grade Management System")

# Primary Navigation
main_tab, scan_tab, report_tab = st.tabs(
    ["⚙️ Admin Control Panel", "📷 Barcode Scanner & Login", "📊 Records & Reports"]
)

# ---------------------------------------------------------
# TAB 1: ADMIN CONTROL PANEL
# ---------------------------------------------------------
with main_tab:
    st.header("Admin Management Hub")

    admin_action = st.radio(
        "Select Task",
        ["Generate Barcodes", "Manual Attendance Logging", "Grade Management"],
        horizontal=True,
    )

    # --- 1. BARCODE GENERATION ---
    if admin_action == "Generate Barcodes":
        st.subheader("Generate ID Barcode for Teacher / Student")
        col1, col2 = st.columns(2)

        with col1:
            role = st.selectbox("Role", ["Student", "Teacher"])
            user_name = st.text_input("Full Name", value="")
            user_id = st.text_input("User ID (e.g., STU102, TEA202)", value="")
            initial_grade = st.selectbox(
                "Initial Grade (Students only)",
                ["A+", "A", "B", "C", "D", "F", "N/A"],
            )

        with col2:
            st.write(" ")
            st.write(" ")
            if st.button("Generate & Register Barcode", use_container_width=True):
                if user_id.strip() and user_name.strip():
                    # Register User into System DB if not present
                    if (
                        user_id.strip()
                        not in st.session_state.users["User ID"].values
                    ):
                        new_user = pd.DataFrame(
                            [
                                {
                                    "User ID": user_id.strip(),
                                    "Name": user_name.strip(),
                                    "Role": role,
                                    "Grade": (
                                        initial_grade
                                        if role == "Student"
                                        else "N/A"
                                    ),
                                }
                            ]
                        )
                        st.session_state.users = pd.concat(
                            [st.session_state.users, new_user],
                            ignore_index=True,
                        )

                    # Encode Barcode Payload (ROLE:USER_ID:NAME)
                    payload = f"{role.upper()}:{user_id.strip()}:{user_name.strip()}"
                    code_class = barcode.get_barcode_class("code128")
                    barcode_img = code_class(payload, writer=ImageWriter())

                    buffer = io.BytesIO()
                    barcode_img.write(buffer)
                    buffer.seek(0)

                    st.image(
                        Image.open(buffer),
                        caption=f"Barcode for {user_name} ({user_id})",
                        use_container_width=True,
                    )
                    st.download_button(
                        label=f"Download Barcode PNG",
                        data=buffer.getvalue(),
                        file_name=f"{user_id}_barcode.png",
                        mime="image/png",
                        use_container_width=True,
                    )
                    st.success(f"Registered {user_name} successfully!")
                else:
                    st.warning("Please fill in both Name and User ID.")

    # --- 2. MANUAL ATTENDANCE LOGGING ---
    elif admin_action == "Manual Attendance Logging":
        st.subheader("Manual Attendance Entry")
        col1, col2 = st.columns(2)

        with col1:
            selected_id = st.selectbox(
                "Select Registered User",
                st.session_state.users["User ID"].tolist(),
            )
            entry_type = st.selectbox(
                "Attendance Status", ["Present", "Late", "Absent"]
            )

        with col2:
            st.write(" ")
            st.write(" ")
            if st.button("Log Attendance Manually", use_container_width=True):
                user_row = st.session_state.users[
                    st.session_state.users["User ID"] == selected_id
                ].iloc[0]
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                log_entry = pd.DataFrame(
                    [
                        {
                            "Timestamp": timestamp,
                            "User ID": selected_id,
                            "Name": user_row["Name"],
                            "Role": user_row["Role"],
                            "Entry Type": f"Manual ({entry_type})",
                        }
                    ]
                )
                st.session_state.attendance_log = pd.concat(
                    [st.session_state.attendance_log, log_entry],
                    ignore_index=True,
                )
                st.success(
                    f"Manually logged attendance for {user_row['Name']} at {timestamp}"
                )

    # --- 3. GRADE MANAGEMENT ---
    elif admin_action == "Grade Management":
        st.subheader("Update Student Grades")

        student_users = st.session_state.users[
            st.session_state.users["Role"] == "Student"
        ]
        if not student_users.empty:
            selected_student_id = st.selectbox(
                "Select Student", student_users["User ID"].tolist()
            )
            new_grade = st.selectbox(
                "Assign Grade", ["A+", "A", "B", "C", "D", "F"]
            )

            if st.button("Update Grade"):
                st.session_state.users.loc[
                    st.session_state.users["User ID"] == selected_student_id,
                    "Grade",
                ] = new_grade
                st.success(
                    f"Updated grade for {selected_student_id} to {new_grade}."
                )
        else:
            st.info("No students currently registered in the database.")

# ---------------------------------------------------------
# TAB 2: BARCODE SCANNER & LOGIN
# ---------------------------------------------------------
with scan_tab:
    st.header("Scan Barcode to Log In & Record Attendance")

    scan_source = st.radio(
        "Input Method", ["Webcam Capture", "Upload Image"], horizontal=True
    )
    img_input = None

    if scan_source == "Webcam Capture":
        cam_file = st.camera_input("Hold Barcode up to Camera")
        if cam_file:
            img_input = Image.open(cam_file)
    else:
        uploaded_img = st.file_uploader(
            "Upload Image File", type=["png", "jpg", "jpeg"]
        )
        if uploaded_img:
            img_input = Image.open(uploaded_img)

    if img_input is not None:
        decoded_results = zxingcpp.read_barcodes(img_input)

        if decoded_results:
            for item in decoded_results:
                raw_payload = item.text
                parts = raw_payload.split(":")

                if len(parts) == 3:
                    u_role, u_id, u_name = parts[0], parts[1], parts[2]
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Record Attendance Log automatically upon scan
                    auto_log = pd.DataFrame(
                        [
                            {
                                "Timestamp": timestamp,
                                "User ID": u_id,
                                "Name": u_name,
                                "Role": u_role,
                                "Entry Type": "Barcode Scan",
                            }
                        ]
                    )
                    st.session_state.attendance_log = pd.concat(
                        [st.session_state.attendance_log, auto_log],
                        ignore_index=True,
                    )

                    st.balloons()
                    st.success(
                        f"**Logged In & Attendance Marked!**\n\n"
                        f"- **Name:** {u_name}\n"
                        f"- **ID:** {u_id}\n"
                        f"- **Role:** {u_role}\n"
                        f"- **Time:** {timestamp}"
                    )
                else:
                    st.error("Invalid Barcode Format detected.")
        else:
            st.error("No valid barcode detected in the image.")

# ---------------------------------------------------------
# TAB 3: RECORDS & REPORTS
# ---------------------------------------------------------
with report_tab:
    st.header("System Databases & Reports")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Registered Users & Grades")
        st.dataframe(st.session_state.users, use_container_width=True)

    with col2:
        st.subheader("Attendance Log")
        st.dataframe(st.session_state.attendance_log, use_container_width=True)

        if not st.session_state.attendance_log.empty:
            csv_data = st.session_state.attendance_log.to_csv(index=False)
            st.download_button(
                label="Export Attendance Log CSV",
                data=csv_data,
                file_name="attendance_records.csv",
                mime="text/csv",
            )
