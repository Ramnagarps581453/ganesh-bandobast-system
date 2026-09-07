import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd
from io import BytesIO

# Safe import for ReportLab
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

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
    import urllib.request
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register a Unicode font capable of rendering Kannada glyphs
@st.cache_resource
def load_kannada_font():
    font_url = "https://github.com/google/fonts/raw/main/ofl/notosanskannada/NotoSansKannada-Regular.ttf"
    font_path = "NotoSansKannada-Regular.ttf"
    try:
        urllib.request.urlretrieve(font_url, font_path)
        pdfmetrics.registerFont(TTFont('KannadaFont', font_path))
        return 'KannadaFont'
    except Exception:
        return 'Helvetica'

def generate_pdf(dataframe):
    if not REPORTLAB_AVAILABLE:
        return None
    
    font_name = load_kannada_font()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    
    # Custom style using the registered Kannada font
    kannada_style = styles['Normal'].clone('KannadaStyle')
    kannada_style.fontName = font_name
    kannada_style.fontSize = 9
    kannada_style.leading = 12

    title_style = styles['Title'].clone('KannadaTitleStyle')
    title_style.fontName = font_name

    title = Paragraph("<b>Ganesh Bandobast Digital Monitoring System</b>", title_style)
    subtitle = Paragraph("<b>Division Control Report</b>", styles['Heading2'])
    elements.extend([title, subtitle, Spacer(1, 12)])
    
    if not dataframe.empty:
        headers = [Paragraph(f"<b>{col}</b>", kannada_style) for col in dataframe.columns]
        table_data = [headers]
        
        for _, row in dataframe.iterrows():
            formatted_row = [Paragraph(str(val) if val is not None else "", kannada_style) for val in row]
            table_data.append(formatted_row)
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ]))
        elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title = Paragraph("<b>Ganesh Bandobast Digital Monitoring System</b>", styles['Title'])
    subtitle = Paragraph("<b>Division Control Report</b>", styles['Heading2'])
    elements.extend([title, subtitle, Spacer(1, 12)])
    
    if not dataframe.empty:
        # Format table headers and convert cell values to Paragraphs for clean text wrapping
        headers = [Paragraph(f"<b>{col}</b>", styles['Normal']) for col in dataframe.columns]
        table_data = [headers]
        
        for _, row in dataframe.iterrows():
            formatted_row = [Paragraph(str(val) if val is not None else "", styles['Normal']) for val in row]
            table_data.append(formatted_row)
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),  # Fixed: Must be uppercase 'CENTER'
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ]))
        elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# Main Title with Logos
st.markdown(
    "<h1 style='text-align: center;'>🐘 Ganesh Bandobast Digital Monitoring System 🐘</h1>", 
    unsafe_allow_html=True
)

role = st.sidebar.selectbox(
    "ಪಾತ್ರವನ್ನು ಆಯ್ಕೆಮಾಡಿ (Select Role)", 
    ["Division Control Dashboard", "ಠಾಣಾ ಬರಹಗಾರರು (Station Writer)", "ಬೀಟ್ ಸಿಬ್ಬಂದಿ (Beat Staff)"]
)

# ==========================================
# 1. DIVISION CONTROL DASHBOARD
# ==========================================
if role == "Division Control Dashboard":
    st.markdown("<h2 style='text-align: center; color: #800000;'>Division Control Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    try:
        response = supabase.table("ganesh_idols").select("*").execute()
        all_idols = response.data
    except Exception as e:
        all_idols = []

    df_all = pd.DataFrame(all_idols) if all_idols else pd.DataFrame()

    col_date, col_stn = st.columns(2)
    
    with col_date:
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        if not df_all.empty and "immersion_date" in df_all.columns:
            raw_dates = df_all["immersion_date"].dropna().unique().tolist()
            valid_dates = []
            for d in raw_dates:
                try:
                    # Parse standard YYYY-MM-DD date
                    if isinstance(d, str) and "-" in d:
                        parsed_d = datetime.datetime.strptime(d, "%Y-%m-%d").date()
                    else:
                        parsed_d = datetime.datetime.strptime(d, "%d/%m/%Y").date()
                        
                    if parsed_d >= datetime.date.today():
                        valid_dates.append(str(parsed_d))
                except ValueError:
                    valid_dates.append(str(d))
            date_options = ["All Dates"] + sorted(list(set(valid_dates)))
        else:
            date_options = ["All Dates"]
            
        selected_date = st.selectbox("Date of immersion:", date_options)

    with col_stn:
        default_stations = ["Haliyal", "Dandeli Town", "Dandeli Rural", "Ambikanagar", "Ramanagar", "Joida"]
        if not df_all.empty and "station_name" in df_all.columns:
            existing_stns = df_all["station_name"].dropna().unique().tolist()
            all_stns = list(set(default_stations + existing_stns))
        else:
            all_stns = default_stations
            
        selected_station = st.selectbox("ಪೋಲಿಸ್ ಠಾಣೆ:", ["ಎಲ್ಲಾ ಠಾಣೆಗಳು (All)"] + sorted(all_stns))

    selected_category = st.selectbox("ವರ್ಗ:", ["ಎಲ್ಲಾ (All)", "ಅತೀಸೂಕ್ಷ್ಮ", "ಸೂಕ್ಷ್ಮ", "ಸಾಮಾನ್ಯ"])

    filtered_df = df_all.copy() if not df_all.empty else pd.DataFrame()

    if not filtered_df.empty:
        if selected_date != "All Dates":
            filtered_df = filtered_df[filtered_df["immersion_date"] == selected_date]
        if selected_station != "ಎಲ್ಲಾ ಠಾಣೆಗಳು (All)":
            filtered_df = filtered_df[filtered_df["station_name"] == selected_station]
        if selected_category != "ಎಲ್ಲಾ (All)":
            filtered_df = filtered_df[filtered_df["sensitivity_level"] == selected_category]

    st.markdown("---")

    m1, m2 = st.columns(2)
    current_installed_count = len(filtered_df) if not filtered_df.empty else 0
    m1.metric("ಪ್ರಸ್ತುತ ಪ್ರತಿಷ್ಠಾಪನೆಯಾಗಿರುವ ಗಣೇಶ ಮೂರ್ತಿಗಳು", current_installed_count)
    
    if not df_all.empty and "immersion_date" in df_all.columns:
        today_immersions = df_all[df_all["immersion_date"] == today_str]
        m2.metric("ಇಂದು ವಿಸರ್ಜನೆಯಾಗಲಿರುವ ಗಣೇಶ ಮೂರ್ತಿಗಳು", len(today_immersions))
    else:
        m2.metric("ಇಂದು ವಿಸರ್ಜನೆಯಾಗಲಿರುವ ಗಣೇಶ ಮೂರ್ತಿಗಳು", 0)

    st.markdown("<br>", unsafe_allow_html=True)

    st.subheader("View PDF Report")
    if REPORTLAB_AVAILABLE:
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
    else:
        st.warning("`reportlab` ಲೈಬ್ರರಿಯನ್ನು ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಲಾಗುತ್ತಿದೆ... `requirements.txt` ಅಪ್‌ಡೇಟ್ ಮಾಡಿ.")

    st.markdown("---")

    st.subheader("ಗಣೇಶೋತ್ಸವ ಸಮಿತಿಗಳ ಸಂಪೂರ್ಣ ವಿವರ (All Idol Registrations)")
    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.write("ಯಾವುದೇ ವಿವರಗಳು ಲಭ್ಯವಿಲ್ಲ.")

# ==========================================
# 2. STATION WRITER INTERFACE (Kannada / Unicode Input)
# ==========================================
elif role == "ಠಾಣಾ ಬರಹಗಾರರು (Station Writer)":
    st.markdown("<h2 style='text-align: center; color: #800000;'>ಠಾಣಾ ಬರಹಗಾರರ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್</h2>", unsafe_allow_html=True)
    st.caption("ಸೂಚನೆ: ಈ ಕೆಳಗಿನ ಎಲ್ಲಾ ವಿವರಗಳನ್ನು ಯುನಿಕೋಡ್ ಕನ್ನಡದಲ್ಲಿ (Kannada Unicode / Indic Keyboard) ನೇರವಾಗಿ ಟೈಪ್ ಮಾಡಬಹುದು.")
    
    default_stations = ["Haliyal", "Dandeli Town", "Dandeli Rural", "Ambikanagar", "Ramanagar", "Joida"]
    try:
        res_stns = supabase.table("police_stations").select("station_name").execute()
        added_stns = [r["station_name"] for r in res_stns.data] if res_stns.data else []
        station_options = sorted(list(set(default_stations + added_stns)))
    except Exception:
        station_options = default_stations

    selected_stn = st.selectbox("ಪೋಲಿಸ್ ಠಾಣೆ :", station_options)

    # Calculate Total Target vs Entered Records Count
    try:
        res_target = supabase.table("station_targets").select("target_count").eq("station_name", selected_stn).execute()
        target_val = res_target.data[0]["target_count"] if res_target.data else 0
    except Exception:
        target_val = 0

    try:
        res_entered = supabase.table("ganesh_idols").select("id", count="exact").eq("station_name", selected_stn).execute()
        entered_val = res_entered.count if res_entered.count is not None else 0
    except Exception:
        entered_val = 0

    col_target_input, col_target_status = st.columns([2, 2])

    with col_target_input:
        if target_val == 0:
            new_target = st.number_input(
                "ಪೋಲಿಸ್ ಠಾಣಾ ವ್ಯಾಪ್ತಿಯಲ್ಲಿ ಪ್ರತಿಷ್ಠಾಪನೆಯಾಗಲಿರುವ ಒಟ್ಟು ಗಣೇಶ ಮೂರ್ತಿಗಳ ಸಂಖ್ಯೆ :", 
                min_value=1, max_value=500, value=10
            )
            if st.button("ಸಂಖ್ಯೆಯನ್ನು ಉಳಿಸಿ (Save Total Target)"):
                supabase.table("station_targets").upsert({"station_name": selected_stn, "target_count": new_target}).execute()
                st.success("ಒಟ್ಟು ಸಂಖ್ಯೆಯನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಉಳಿಸಲಾಗಿದೆ!")
                st.rerun()
        else:
            st.info(f"**ಒಟ್ಟು ನಿಗದಿತ ಗಣೇಶ ಮೂರ್ತಿಗಳ ಸಂಖ್ಯೆ:** {target_val}")

    with col_target_status:
        remaining_val = max(0, target_val - entered_val) if target_val > 0 else 0
        st.metric("ದಾಖಲಿಸಲಾದ ವಿವರಗಳು", f"{entered_val} / {target_val if target_val > 0 else 'ನಿಗದಿಯಾಗಿಲ್ಲ'}")
        if target_val > 0:
            st.warning(f"**ಇನ್ನೂ ಭರ್ತಿ ಮಾಡಲು ಬಾಕಿ ಇರುವ ಸಂಖ್ಯೆ:** {remaining_val}")

    st.markdown("---")

    # Form accepting Unicode Kannada text directly
    with st.form("station_writer_form"):
        pandal_name = st.text_input("ಗಣೇಶೋತ್ಸವ ಸಮಿತಿಯ ಹೆಸರು :", placeholder="ಉದಾ: ಶ್ರೀ ವಿನಾಯಕ ಯುವಕ ಮಂಡಳಿ")
        location_address = st.text_input("ಪ್ರತಿಷ್ಠಾಪನೆಯಾಗುವ ಸ್ಥಳ :", placeholder="ಉದಾ: ಬಸ್ ನಿಲ್ದಾಣದ ಹತ್ತಿರ")

        col_beat, col_staff = st.columns(2)
        beat_number = col_beat.number_input("ಬೀಟ್ ನಂಬರ :", min_value=1, max_value=100, value=1)
        beat_staff_details = col_staff.text_input("ಬೀಟ್ ಸಿಬ್ಬಂದಿ ವಿವರ (ಹೆಸರು, ಮೊಬೈಲ್ ನಂ) :", placeholder="ಉದಾ: ಹೆಚ್‌ಸಿ 452 ರಮೇಶ್, 9876543210")

        install_date = st.date_input(
            "ಗಣೇಶ ಪ್ರತಿಷ್ಠಾಪನ ದಿನಾಂಕ :", 
            datetime.date.today(), 
            format="DD/MM/YYYY"
        )

        col_p1, col_p2 = st.columns(2)
        president_name = col_p1.text_input("ಕಮಿಟಿ ಅಧ್ಯಕ್ಷರ ಹೆಸರು :", placeholder="ಅಧ್ಯಕ್ಷರ ಹೆಸರು")
        president_phone = col_p2.text_input("ಮೊಬೈಲ್ ನಂ (ಅಧ್ಯಕ್ಷರು) :", placeholder="9876543210")

        col_v1, col_v2 = st.columns(2)
        vice_president_name = col_v1.text_input("ಕಮಿಟಿ ಉಪಾಧ್ಯಕ್ಷರ ಹೆಸರು :", placeholder="ಉಪಾಧ್ಯಕ್ಷರ ಹೆಸರು")
        vice_president_phone = col_v2.text_input("ಮೊಬೈಲ್ ನಂ (ಉಪಾಧ್ಯಕ್ಷರು) :", placeholder="9876543210")

        sensitivity_level = st.selectbox("ವರ್ಗ :", ["ಸಾಮಾನ್ಯ", "ಸೂಕ್ಷ್ಮ", "ಅತೀಸೂಕ್ಷ್ಮ"])

        immersion_date = st.date_input(
            "ವಿಸರ್ಜನೆಯಾಗುವ ದಿನಾಂಕ :", 
            datetime.date.today(), 
            format="DD/MM/YYYY"
        )

        sensitive_route_details = st.text_area(
            "ಮಾರ್ಗಮಧ್ಯದಲ್ಲಿರುವ ಮಸೀದಿ ಹಾಗೂ ಚರ್ಚಗಳ ವಿವರ :", 
            placeholder="20-30 ಅಕ್ಷರಗಳಲ್ಲಿ ಕನ್ನಡದಲ್ಲಿ ವಿವರಗಳನ್ನು ಇಲ್ಲಿ ಟೈಪ್ ಮಾಡಿ..."
        )

        past_incident_details = st.text_area(
            "ಈ ಹಿಂದೆ ನಡೆದ ಘಟನೆ/ಪ್ರಕರಣಗಳ ವಿವರ :", 
            placeholder="20-30 ಅಕ್ಷರಗಳಲ್ಲಿ ವಿವರಗಳನ್ನು ಇಲ್ಲಿ ಟೈಪ್ ಮಾಡಿ..."
        )

        submit_btn = st.form_submit_button("ಮಾಹಿತಿ ಸಲ್ಲಿಸಿ (Submit Record)")

        if submit_btn:
            if not pandal_name.strip():
                st.warning("ದಯವಿಟ್ಟು ಗಣೇಶೋತ್ಸವ ಸಮಿತಿಯ ಹೆಸರನ್ನು ನಮೂದಿಸಿ.")
            else:
                record = {
                    "station_name": str(selected_stn),
                    "pandal_name": str(pandal_name).strip(),
                    "location_address": str(location_address).strip() if location_address else "",
                    "beat_number": int(beat_number),
                    "beat_staff_details": str(beat_staff_details).strip() if beat_staff_details else "",
                    # Format as YYYY-MM-DD for PostgreSQL DATE columns
                    "installation_date": install_date.strftime("%Y-%m-%d"),
                    "president_name": str(president_name).strip() if president_name else "",
                    "president_phone": str(president_phone).strip() if president_phone else "",
                    "vice_president_name": str(vice_president_name).strip() if vice_president_name else "",
                    "vice_president_phone": str(vice_president_phone).strip() if vice_president_phone else "",
                    "sensitivity_level": str(sensitivity_level),
                    # Format as YYYY-MM-DD for PostgreSQL DATE columns
                    "immersion_date": immersion_date.strftime("%Y-%m-%d"),
                    "sensitive_route_details": str(sensitive_route_details).strip() if sensitive_route_details else "",
                    "past_incident_details": str(past_incident_details).strip() if past_incident_details else ""
                }
                try:
                    supabase.table("ganesh_idols").insert(record).execute()
                    st.success("ವಿವರಗಳನ್ನು ಯಶಸ್ವಿಯಾಗಿ ನಮೂದಿಸಲಾಗಿದೆ!")
                    st.rerun()
                except Exception as db_err:
                    st.error(f"ಡೇಟಾಬೇಸ್‌ನಲ್ಲಿ ದಾಖಲಿಸಲು ಸಾಧ್ಯವಾಗಿಲ್ಲ: {db_err}")

# ==========================================
# 3. BEAT STAFF FIELD UPDATE INTERFACE
# ==========================================
elif role == "ಬೀಟ್ ಸಿಬ್ಬಂದಿ (Beat Staff)":
    st.header("ಬೀಟ್ ಸಿಬ್ಬಂದಿ ಕ್ಷೇತ್ರ ವರದಿ")
    
    default_stations = ["Haliyal", "Dandeli Town", "Dandeli Rural", "Ambikanagar", "Ramanagar", "Joida"]
    selected_stn = st.selectbox("ನಿಮ್ಮ ಠಾಣೆ ಆಯ್ಕೆಮಾಡಿ", default_stations, key="staff_stn")
    beat_num = st.number_input("ನಿಮ್ಮ ಬೀಟ್ ಸಂಖ್ಯೆ", min_value=1, max_value=50, value=1, key="staff_beat")
    
    res = supabase.table("ganesh_idols").select("*").eq("station_name", selected_stn).eq("beat_number", beat_num).execute()
    idols_in_beat = res.data
    
    if not idols_in_beat:
        st.info("ಈ ಬೀಟ್‌ನಲ್ಲಿ ಯಾವುದೇ ಗಣೇಶ ಮೂರ್ತಿಗಳು ನೋಂದಾಯಿಸಲ್ಪಟ್ಟಿಲ್ಲ.")
    else:
        pandal_options = {f"{i['pandal_name']} ({i.get('sensitivity_level', 'ಸಾಮಾನ್ಯ')})": i for i in idols_in_beat}
        selected_key = st.selectbox("ಗಣೇಶ ಮಂಡಳಿಯನ್ನು ಆಯ್ಕೆಮಾಡಿ", list(pandal_options.keys()))
        selected_idol = pandal_options[selected_key]
        
        st.write(f"**ವರ್ಗ (Category):** {selected_idol.get('sensitivity_level', 'ಸಾಮಾನ್ಯ')}")
        st.write(f"**ಸ್ಥಳ:** {selected_idol.get('location_address', '')}")
        st.write(f"**ವಿಸರ್ಜನೆ ದಿನಾಂಕ:** {selected_idol.get('immersion_date', '')}")
        st.write(f"**ಮಾರ್ಗ ವಿವರ:** {selected_idol.get('sensitive_route_details', 'ಲಭ್ಯವಿಲ್ಲ')}")
        
        st.subheader("ಸ್ಥಿತಿ ನವೀಕರಿಸಿ")
        install_status = st.radio("ಪ್ರತಿಷ್ಠಾಪನೆ ಸ್ಥಿತಿ", ["ಪೆಂಡಿಂಗ್", "ಶಾಂತಿಯುತವಾಗಿ ಪೂರ್ಣಗೊಂಡಿದೆ", "ಸಮಸ್ಯೆ ವರದಿಯಾಗಿದೆ"], index=0)
        immersion_status = st.radio("ವಿಸರ್ಜನೆ ಸ್ಥಿತಿ", ["ಪ್ರಾರಂಭವಾಗಿಲ್ಲ", "ಮೆರವಣಿಗೆಯಲ್ಲಿದೆ", "ಶಾಂತಿಯುತವಾಗಿ ಪೂರ್ಣಗೊಂಡಿದೆ"], index=0)
        
        if st.button("ಸ್ಥಿತಿ ಅಪ್‌ಡೇಟ್ ಮಾಡಿ"):
            supabase.table("ganesh_idols").update({
                "installation_status": install_status,
                "immersion_status": immersion_status
            }).eq("id", selected_idol["id"]).execute()
            st.success("ಸ್ಥಿತಿಯನ್ನು ಯಶಸ್ವಿಯಾಗಿ ನವೀಕರಿಸಲಾಗಿದೆ!")
