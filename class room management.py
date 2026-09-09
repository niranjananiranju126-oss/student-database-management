import streamlit as st
import pandas as pd

st.title("Classroom Management System")

# Dummy student data for illustration (replace with your actual database/DataFrame source)
if "students_c" not in st.session_state:
    st.session_state.students_c = pd.DataFrame({
        "User ID": ["STU001", "STU002", "STU003", "STU004"],
        "Name": ["Alice", "Bob", "Charlie", "David"],
        "Grade": ["A", "B", "A", "C"]
    })

students_c = st.session_state.students_c

# Verify the data exists before rendering the widget
if not students_c.empty and "User ID" in students_c.columns:
    user_ids = students_c["User ID"].tolist()

    # FIX: Added explicit unique 'key' argument to eliminate StreamlitDuplicateElementId error
    selected_stu_c = st.selectbox(
        label="Select Student",
        options=user_ids,
        key="classroom_select_student_unique_key"
    )

    # Display selected student details
    selected_info = students_c[students_c["User ID"] == selected_stu_c]
    st.subheader("Student Details")
    st.dataframe(selected_info)
else:
    st.warning("No student data available to display.")
