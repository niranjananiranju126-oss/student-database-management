import io
import barcode
from barcode.writer import ImageWriter
import pandas as pd

from PIL import Image
from pyzbar.pyzbar import decode
import streamlit as st

st.title("Barcode Generator & Scanner")

# Tab navigation
tab1, tab2 = st.tabs(["Generate Barcode", "Scan Barcode"])

# ---------------------------------------------------------
# TAB 1: GENERATE BARCODE (No default input)
# ---------------------------------------------------------
with tab1:
    st.subheader("Generate a Barcode")

    # Text input with NO default value
    user_input = st.text_input(
        "Enter text or numbers for the barcode:", value=""
    )

    # Barcode format selection
    barcode_type = st.selectbox(
        "Select Barcode Type:", ["code128", "code39", "ean13", "upc"]
    )

    if st.button("Generate Barcode"):
        if user_input.strip():
            try:
                # Generate barcode in memory
                code_class = barcode.get_barcode_class(barcode_type)
                barcode_instance = code_class(
                    user_input, writer=ImageWriter()
                )

                buffer = io.BytesIO()
                barcode_instance.write(buffer)
                buffer.seek(0)

                # Display barcode image
                img = Image.open(buffer)
                st.image(
                    img, caption=f"Generated ({barcode_type.upper()})", use_container_width=True
                )

                # Download button for the image
                st.download_button(
                    label="Download Barcode Image",
                    data=buffer.getvalue(),
                    file_name=f"barcode_{user_input}.png",
                    mime="image/png",
                )
            except Exception as e:
                st.error(
                    f"Error generating barcode: {e}. (Ensure input format matches the selected type, e.g., 12/13 digits for EAN/UPC)."
                )
        else:
            st.warning("Please enter text or numeric value first.")

# ---------------------------------------------------------
# TAB 2: SCAN BARCODE (Upload image to decode)
# ---------------------------------------------------------
with tab2:
    st.subheader("Scan & Decode Barcode Image")

    uploaded_file = st.file_uploader(
        "Upload a barcode image:", type=["png", "jpg", "jpeg"]
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)

        # Decode using pyzbar
        decoded_objects = decode(image)

        if decoded_objects:
            st.success(f"Found {len(decoded_objects)} barcode(s):")
            results = []
            for obj in decoded_objects:
                results.append(
                    {
                        "Type": obj.type,
                        "Data": obj.data.decode("utf-8"),
                    }
                )

            # Display as DataFrame
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
        else:
            st.error("No valid barcode could be detected in this image.")
