import streamlit as st
from supabase import create_client, Client

st.set_page_config(
    page_title="Ganesh Bandobast Digital Monitoring",
    page_icon="🚔",
    layout="wide"
)

# Initialize Supabase client using secrets
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["supabase"]["SUPABASE_URL"]
    key = st.secrets["supabase"]["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"Failed to connect to Supabase: {e}")
    st.stop()

st.title("Ganesh Bandobast Digital Monitoring System")

# Navigation Role Switcher
role = st.sidebar.selectbox("Select Access Role", ["District HQ", "Station Writer", "Beat Staff"])

if role == "District HQ":
    st.header("District Control Dashboard")
    try:
        response = supabase.table("ganesh_idols").select("*").execute()
        idols = response.data
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Registered Idols", len(idols))
        
        sensitive_count = sum(1 for i in idols if i.get("sensitivity_level") in ["Sensitive", "Hyper-Sensitive"])
        col2.metric("Sensitive / Hyper-Sensitive", sensitive_count)
        
        immersed_count = sum(1 for i in idols if i.get("immersion_status") == "Completed Peacefully")
        col3.metric("Immersions Completed", immersed_count)

        st.subheader("All Idol Registrations")
        st.dataframe(idols)
    except Exception as e:
        st.warning(f"No records found or table not created yet. Error: {e}")

elif role == "Station Writer":
    st.header("Station Level Idol & Committee Entry")
    with st.form("add_idol_form"):
        station = st.text_input("Station Name", value="Ramanagar PS")
        beat = st.number_input("Beat Number", min_value=1, max_value=20, value=1)
        pandal = st.text_input("Pandal / Committee Name")
        address = st.text_input("Location / Landmark")
        sensitivity = st.selectbox("Sensitivity Level", ["Normal", "Sensitive", "Hyper-Sensitive"])
        
        president = st.text_input("President Name")
        phone = st.text_input("President Contact Number")
        immersion_date = st.date_input("Planned Immersion Date")
        
        submitted = st.form_submit_button("Submit Record")
        if submitted:
            data = {
                "station_name": station,
                "beat_number": beat,
                "pandal_name": pandal,
                "location_address": address,
                "sensitivity_level": sensitivity,
                "president_name": president,
                "president_phone": phone,
                "immersion_date": str(immersion_date)
            }
            supabase.table("ganesh_idols").insert(data).execute()
            st.success("Record submitted successfully!")

elif role == "Beat Staff":
    st.header("Beat Staff Status Update")
    st.info("Beat staff can quickly select an assigned idol and report real-time status updates.")
