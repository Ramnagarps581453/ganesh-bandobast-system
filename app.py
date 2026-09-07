import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

st.set_page_config(
    page_title="Ganesh Bandobast Digital Monitoring System",
    page_icon="🐘",
    layout="wide"
)

# Initialize Supabase client
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["supabase"]["SUPABASE_URL"]
    key = st.secrets["supabase"]["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"ಸಂಪರ್ಕ ದೋಷ (Connection Error): {e}")
    st.stop()

# Helper function to generate PDF Report
def generate_pdf(dataframe):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title = Paragraph("<b>Ganesh Bandobast Digital Monitoring System</b>", styles['Title'])
    subtitle = Paragraph("<b>Division Control Report</b>", styles['Heading2'])
    elements.extend([title, subtitle, Spacer(1, 12)])
    
    if not dataframe.empty:
        # Convert dataframe to list for ReportLab Table
        data = [dataframe.columns.tolist()] + dataframe.values.tolist()
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'Center'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# Main Title with Logos on both sides
st.markdown(
    "<h1 style='text-align: center;'>🐘 Ganesh Bandobast Digital Monitoring System 🐘</h1>", 
    unsafe_allow_html=True
)

role = st.sidebar.selectbox(
    "ಪಾತ್ರವನ್ನು ಆಯ್ಕೆಮಾಡಿ (Select Role)", 
    ["Division Control Dashboard", "ಠಾಣಾ ಬರಹಗಾರರು (Station Writer)", "ಬೀಟ್ ಸಿಬ್ಬಂದಿ (Beat Staff)"]
)

# ==========================================
# DIVISION CONTROL DASHBOARD
# ==========================================
if role == "Division Control Dashboard":
    st.markdown("<h2 style='text-align: center; color: #800000;'>Division Control Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Fetch all data from Supabase
    try:
        response = supabase.table("ganesh_idols").select("*").execute()
        all_idols = response.data
    except Exception as e:
        all_idols = []

    df_all = pd.DataFrame(all_idols) if all_idols else pd.DataFrame()

    # --- FILTER ROW 1: Date & Station Filters ---
    col_date, col_stn = st.columns(2)
    
    with col_date:
        today_str = datetime.date.today().strftime("%d/%m/%Y")
        
        if not df_all.empty and "immersion_date" in df_all.columns:
            # Extract unique dates from DB
            raw_dates = df_all["immersion_date"].dropna().unique().tolist()
            valid_dates = []
            
            # Disable / Filter out past dates
            for d in raw_dates:
                try:
                    parsed_d = datetime.datetime.strptime(d, "%d/%m/%Y").date()
                    if parsed_d >= datetime.date.today():
                        valid_dates.append(d)
                except ValueError:
                    valid_dates.append(d)
            
            date_options = ["All Dates"] + sorted(valid_dates)
        else:
            date_options = ["All Dates"]
            
        selected_date = st.selectbox("Date of immersion:", date_options)

    with col_stn:
        # Pre-populated station list including default division stations
        default_stations = ["Haliyal", "Dandeli Town", "Dandeli Rural", "Ambikanagar", "Ramanagar", "Joida"]
        if not df_all.empty and "station_name" in df_all.columns:
            existing_stns = df_all["station_name"].dropna().unique().tolist()
            all_stns = list(set(default_stations + existing_stns))
        else:
            all_stns = default_stations
            
        selected_station = st.selectbox("ಪೋಲಿಸ್ ಠಾಣೆ:", ["ಎಲ್ಲಾ ಠಾಣೆಗಳು (All)"] + sorted(all_stns))

    # --- FILTER ROW 2: Category Filter ---
    selected_category = st.selectbox("ವರ್ಗ:", ["ಎಲ್ಲಾ (All)", "ಅತೀಸೂಕ್ಷ್ಮ", "ಸೂಕ್ಷ್ಮ", "ಸಾಮಾನ್ಯ"])

    # --- APPLY FILTERS TO DATAFRAME ---
    filtered_df = df_all.copy() if not df_all.empty else pd.DataFrame()

    if not filtered_df.empty:
        if selected_date != "All Dates":
            filtered_df = filtered_df[filtered_df["immersion_date"] == selected_date]
        if selected_station != "ಎಲ್ಲಾ ಠಾಣೆಗಳು (All)":
            filtered_df = filtered_df[filtered_df["station_name"] == selected_station]
        if selected_category != "ಎಲ್ಲಾ (All)":
            filtered_df = filtered_df[filtered_df["sensitivity_level"] == selected_category]

    st.markdown("---")

    # --- METRICS DISPLAY ---
    m1, m2 = st.columns(2)
    
    current_installed_count = len(filtered_df) if not filtered_df.empty else 0
    m1.metric("ಪ್ರಸ್ತುತ ಪ್ರತಿಷ್ಠಾಪನೆಯಾಗಿರುವ ಗಣೇಶ ಮೂರ್ತಿಗಳು", current_installed_count)
    
    # Calculate today's immersions count
    if not df_all.empty and "immersion_date" in df_all.columns:
        today_immersions = df_all[df_all["immersion_date"] == today_str]
        m2.metric("ಇಂದು ವಿಸರ್ಜನೆಯಾಗಲಿರುವ ಗಣೇಶ ಮೂರ್ತಿಗಳು", len(today_immersions))
    else:
        m2.metric("ಇಂದು ವಿಸರ್ಜನೆಯಾಗಲಿರುವ ಗಣೇಶ ಮೂರ್ತಿಗಳು", 0)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- VIEW / DOWNLOAD PDF REPORT BUTTON ---
    st.subheader("View PDF Report")
    if not filtered_df.empty:
        pdf_data = generate_pdf(filtered_df[['station_name', 'pandal_name', 'sensitivity_level', 'immersion_date', 'immersion_status']])
        st.download_button(
            label="📄 PDF ವರದಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ (Download PDF Report)",
            data=pdf_data,
            file_name=f"Ganesh_Bandobast_Report_{datetime.date.today()}.pdf",
            mime="application/pdf"
        )
    else:
        st.info("ವರದಿ ರಚಿಸಲು ಯಾವುದೇ ಡೇಟಾ ಲಭ್ಯವಿಲ್ಲ.")

    st.markdown("---")

    # --- FULL DATA TABLE ---
    st.subheader("ಗಣೇಶೋತ್ಸವ ಸಮಿತಿಗಳ ಸಂಪೂರ್ಣ ವಿವರ (All Idol Registrations)")
    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.write("ಯಾವುದೇ ವಿವರಗಳು ಲಭ್ಯವಿಲ್ಲ.")
