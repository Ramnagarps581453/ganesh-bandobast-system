import datetime
from io import BytesIO
import pandas as pd
import streamlit as st
from supabase import Client, create_client

st.set_page_config(
    page_title="Ganesh Bandobast Digital Monitoring System", layout="wide"
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

# Main Title
st.markdown(
    "<h1 style='text-align: center;'>Ganesh Bandobast Digital Monitoring System</h1>",
    unsafe_allow_html=True,
)

role = st.sidebar.selectbox(
    "ಪಾತ್ರವನ್ನು ಆಯ್ಕೆಮಾಡಿ (Select Role)",
    [
        "Division Control Dashboard",
        "ಠಾಣಾ ಬರಹಗಾರರು (Station Writer)",
        "ಬೀಟ್ ಸಿಬ್ಬಂದಿ (Beat Staff)",
    ],
)

ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin")

# ==========================================
# 1. DIVISION CONTROL DASHBOARD
# ==========================================
if role == "Division Control Dashboard":
    st.markdown(
        "<h2 style='text-align: center; color: #800000;'>Division Control Dashboard</h2>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    try:
        response = supabase.table("ganesh_idols").select("*").execute()
        all_idols = response.data
    except Exception as e:
        st.error(f"Error loading records: {e}")
        all_idols = []

    df_all = pd.DataFrame(all_idols) if all_idols else pd.DataFrame()

    if not df_all.empty and "id" in df_all.columns:
        cols = ["id"] + [c for c in df_all.columns if c != "id"]
        df_all = df_all[cols]

    col_date, col_stn = st.columns(2)

    with col_date:
        if not df_all.empty and "immersion_date" in df_all.columns:
            entered_dates = (
                df_all["immersion_date"].dropna().unique().tolist()
            )
            raw_dates = sorted(
                [str(d).strip() for d in entered_dates if str(d).strip() != ""]
            )

            date_map = {}
            for rd in raw_dates:
                try:
                    dt_obj = datetime.datetime.strptime(rd, "%Y-%m-%d")
                    date_map[dt_obj.strftime("%d/%m/%Y")] = rd
                except ValueError:
                    date_map[rd] = rd

            date_options = ["All Dates"] + list(date_map.keys())
        else:
            date_map = {}
            date_options = ["All Dates"]

        selected_date_display = st.selectbox(
            "ವಿಸರ್ಜನೆ ದಿನಾಂಕ (Date of Immersion):", date_options
        )

    default_stations = [
        "Haliyal",
        "Dandeli Town",
        "Dandeli Rural",
        "Ambikanagar",
        "Ramanagar",
        "Joida",
    ]

    with col_stn:
        if not df_all.empty and "station_name" in df_all.columns:
            existing_stns = df_all["station_name"].dropna().unique().tolist()
            all_stns = list(set(default_stations + existing_stns))
        else:
            all_stns = default_stations

        selected_station = st.selectbox(
            "ಪೋಲಿಸ್ ಠಾಣೆ:", ["ಎಲ್ಲಾ ಠಾಣೆಗಳು (All)"] + sorted(all_stns)
        )

    selected_category = st.selectbox(
        "ವರ್ಗ:", ["ಎಲ್ಲಾ (All)", "ಅತೀಸೂಕ್ಷ್ಮ", "ಸೂಕ್ಷ್ಮ", "ಸಾಮಾನ್ಯ"]
    )

    filtered_df = df_all.copy() if not df_all.empty else pd.DataFrame()

    if not filtered_df.empty:
        if (
            selected_date_display != "All Dates"
            and selected_date_display in date_map
        ):
            raw_selected_date = date_map[selected_date_display]
            filtered_df = filtered_df[
                filtered_df["immersion_date"] == raw_selected_date
            ]
        if selected_station != "ಎಲ್ಲಾ ಠಾಣೆಗಳು (All)":
            filtered_df = filtered_df[
                filtered_df["station_name"] == selected_station
            ]
        if selected_category != "ಎಲ್ಲಾ (All)":
            filtered_df = filtered_df[
                filtered_df["sensitivity_level"] == selected_category
            ]

    st.markdown("---")

    # Main Metrics Calculation
    m1, m2 = st.columns(2)
    current_installed_count = len(filtered_df) if not filtered_df.empty else 0
    m1.metric(
        "ಪ್ರಸ್ತುತ ಪ್ರತಿಷ್ಠಾಪನೆಯಾಗಿರುವ ಗಣೇಶ ಮೂರ್ತಿಗಳು", current_installed_count
    )

    if selected_date_display != "All Dates":
        metric_label = f"ದಿನಾಂಕ {selected_date_display} ರಂದು ವಿಸರ್ಜನೆಯಾಗಲಿರುವ ಗಣೇಶ ಮೂರ್ತಿಗಳ ಸಂಖ್ಯೆ"
        m2.metric(metric_label, current_installed_count)
    else:
        metric_label = "ವಿಸರ್ಜನೆಗೆ ಬಾಕಿ ಇರುವ ಗಣೇಶ ಮೂರ್ತಿಗಳ ಸಂಖ್ಯೆ"
        if not filtered_df.empty and "immersion_status" in filtered_df.columns:
            pending_count = len(
                filtered_df[
                    filtered_df["immersion_status"] != "ಶಾಂತಿಯುತವಾಗಿ ಪೂರ್ಣಗೊಂಡಿದೆ"
                ]
            )
        else:
            pending_count = current_installed_count
        m2.metric(metric_label, pending_count)

    st.markdown("<br>", unsafe_allow_html=True)

    # Category Breakdown Metrics
    st.subheader("📊 ವರ್ಗೀಕರಣದ ವಿವರ (Category Breakdown)")
    c1, c2, c3 = st.columns(3)

    if not filtered_df.empty and "sensitivity_level" in filtered_df.columns:
        v_hyper = len(
            filtered_df[filtered_df["sensitivity_level"] == "ಅತೀಸೂಕ್ಷ್ಮ"]
        )
        v_sens = len(
            filtered_df[filtered_df["sensitivity_level"] == "ಸೂಕ್ಷ್ಮ"]
        )
        v_norm = len(
            filtered_df[filtered_df["sensitivity_level"] == "ಸಾಮಾನ್ಯ"]
        )
    else:
        v_hyper, v_sens, v_norm = 0, 0, 0

    c1.metric("🔴 ಅತೀಸೂಕ್ಷ್ಮ (Hyper-sensitive)", v_hyper)
    c2.metric("🟡 ಸೂಕ್ಷ್ಮ (Sensitive)", v_sens)
    c3.metric("🟢 ಸಾಮಾನ್ಯ (Normal)", v_norm)

    st.markdown("---")

    # Excel Download
    st.subheader("📊 ಡೌನ್‌ಲೋಡ್ ವರದಿ (Download Excel Report)")
    if not filtered_df.empty:
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            filtered_df.to_excel(
                writer, index=False, sheet_name="Ganesh_Bandobast"
            )

        st.download_button(
            label="📥 Excel ವರದಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ (Download Excel)",
            data=buffer.getvalue(),
            file_name=f"Ganesh_Bandobast_Report_{datetime.date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.info("ವರದಿ ರಚಿಸಲು ಯಾವುದೇ ಡೇಟಾ ಲಭ್ಯವಿಲ್ಲ.")

    st.markdown("---")

    st.subheader("ಗಣೇಶೋತ್ಸವ ಸಮಿತಿಗಳ ಸಂಪೂರ್ಣ ವಿವರ (All Idol Registrations)")
    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.write("ಯಾವುದೇ ವಿವರಗಳು ಲಭ್ಯವಿಲ್ಲ.")

    # Admin Login, Target Setting & Delete Section
    st.markdown("---")
    st.subheader("🔑 Admin Controls & Record Management")

    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False

    if not st.session_state["admin_logged_in"]:
        with st.expander("Admin Login (To Manage Targets & Delete Records)"):
            pwd = st.text_input("Enter Admin Password:", type="password")
            if st.button("Login as Admin"):
                if pwd == ADMIN_PASSWORD:
                    st.session_state["admin_logged_in"] = True
                    st.success("Admin Login Successful!")
                    st.rerun()
                else:
                    st.error("Incorrect Password.")
    else:
        st.success("🔓 Admin Mode Active")
        if st.button("Logout Admin"):
            st.session_state["admin_logged_in"] = False
            st.rerun()

        # DIVISION CONTROL: SET STATION TARGETS (VISIBLE ONLY FOR ADMIN)
        st.markdown("---")
        st.subheader(
            "🎯 ಠಾಣಾವಾರು ಗಣೇಶ ಮೂರ್ತಿಗಳ ನಿಗದಿತ ಸಂಖ್ಯೆ (Set Police Station Targets)"
        )
        st.caption(
            "ವಿಭಾಗೀಯ ಕಚೇರಿಯಿಂದ ಪ್ರತಿಯೊಂದು ಪೋಲಿಸ್ ಠಾಣೆಗೆ ಒಟ್ಟು ಗಣೇಶ ಮೂರ್ತಿಗಳ ಸಂಖ್ಯೆಯನ್ನು ಇಲ್ಲಿ ನಮೂದಿಸಿ."
        )

        col_target_stn, col_target_num, col_target_btn = st.columns([2, 2, 1])

        with col_target_stn:
            target_stn_choice = st.selectbox(
                "ಪೋಲಿಸ್ ಠಾಣೆ ಆಯ್ಕೆಮಾಡಿ:", sorted(all_stns), key="div_target_stn"
            )

        try:
            res_t = (
                supabase.table("station_targets")
                .select("target_count")
                .eq("station_name", target_stn_choice)
                .execute()
            )
            current_t_val = (
                res_t.data[0]["target_count"] if res_t.data else 10
            )
        except Exception:
            current_t_val = 10

        with col_target_num:
            set_target_val = st.number_input(
                "ಒಟ್ಟು ನಿಗದಿತ ಗಣೇಶ ಮೂರ್ತಿಗಳ ಸಂಖ್ಯೆ:",
                min_value=1,
                max_value=1000,
                value=current_t_val,
                key="div_target_val",
            )

        with col_target_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("ಸಂಖ್ಯೆ ಉಳಿಸಿ (Save Target)", type="primary"):
                try:
                    supabase.table("station_targets").upsert({
                        "station_name": target_stn_choice,
                        "target_count": set_target_val,
                    }).execute()
                    st.success(
                        f"{target_stn_choice} ಠಾಣೆಗೆ {set_target_val} ಮೂರ್ತಿಗಳ ಸಂಖ್ಯೆಯನ್ನು ಉಳಿಸಲಾಗಿದೆ!"
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving target: {e}")

        st.markdown("---")
        st.markdown("### 🗑️ Delete Record")
        if not df_all.empty and "id" in df_all.columns:
            record_to_delete = st.selectbox(
                "Select Record to Delete (Search by SP Office Unique ID / Pandal Name):",
                df_all["id"].tolist(),
                format_func=lambda x: f"ID: {x} - {df_all[df_all['id'] == x]['pandal_name'].values[0] if not df_all[df_all['id'] == x].empty else ''}",
            )

            if st.button("❌ Remove Selected Record", type="primary"):
                try:
                    supabase.table("ganesh_idols").delete().eq(
                        "id", record_to_delete
                    ).execute()
                    st.success(
                        f"Record '{record_to_delete}' successfully removed!"
                    )
                    st.rerun()
                except Exception as del_err:
                    st.error(f"Error removing record: {del_err}")
        else:
            st.info("No records available to delete.")

# ==========================================
# 2. STATION WRITER INTERFACE
# ==========================================
elif role == "ಠಾಣಾ ಬರಹಗಾರರು (Station Writer)":
    st.markdown(
        "<h2 style='text-align: center; color: #800000;'>ಠಾಣಾ ಬರಹಗಾರರ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್</h2>",
        unsafe_allow_html=True,
    )
    st.caption(
        "💡 ಸೂಚನೆ: ಈ ಕೆಳಗಿನ ಎಲ್ಲಾ ವಿವರಗಳನ್ನು ಯುನಿಕೋಡ್ ಕನ್ನಡದಲ್ಲಿ (Kannada Unicode / Indic Keyboard) ನೇರವಾಗಿ ಟೈಪ್ ಮಾಡಬಹುದು."
    )

    default_stations = [
        "Haliyal",
        "Dandeli Town",
        "Dandeli Rural",
        "Ambikanagar",
        "Ramanagar",
        "Joida",
    ]
    try:
        res_stns = (
            supabase.table("police_stations").select("station_name").execute()
        )
        added_stns = (
            [r["station_name"] for r in res_stns.data] if res_stns.data else []
        )
        station_options = sorted(list(set(default_stations + added_stns)))
    except Exception:
        station_options = default_stations

    if "selected_station_writer" not in st.session_state:
        st.session_state["selected_station_writer"] = None

    if not st.session_state["selected_station_writer"]:
        st.markdown("---")
        st.subheader(
            "🏢 ಪೋಲಿಸ್ ಠಾಣೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ (Select Police Station)"
        )

        selected_stn = st.selectbox(
            "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಠಾಣೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ:",
            ["-- ಠಾಣೆ ಆಯ್ಕೆಮಾಡಿ --"] + station_options,
        )

        if st.button(
            "ಠಾಣೆ ಪ್ರವೇಶಿಸಿ (Proceed to Station Entry)", type="primary"
        ):
            if selected_stn != "-- ಠಾಣೆ ಆಯ್ಕೆಮಾಡಿ --":
                st.session_state["selected_station_writer"] = selected_stn
                st.rerun()
            else:
                st.warning("ದಯವಿಟ್ಟು ಪಟ್ಟಿಯಿಂದ ನಿಮ್ಮ ಠಾಣೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ.")
    else:
        selected_stn = st.session_state["selected_station_writer"]

        col_stn_title, col_stn_change = st.columns([3, 1])
        with col_stn_title:
            st.success(f"📌 ಪ್ರಸ್ತುತ ಆಯ್ಕೆ ಮಾಡಲಾದ ಠಾಣೆ: **{selected_stn}**")
        with col_stn_change:
            if st.button("🔄 ಠಾಣೆಯನ್ನು ಬದಲಾಯಿಸಿ"):
                st.session_state["selected_station_writer"] = None
                st.rerun()

        # Retrieve Target Set by Division Control
        try:
            res_target = (
                supabase.table("station_targets")
                .select("target_count")
                .eq("station_name", selected_stn)
                .execute()
            )
            target_val = (
                res_target.data[0]["target_count"] if res_target.data else 0
            )
        except Exception:
            target_val = 0

        # Retrieve Station-Specific Idol Records
        try:
            res_stn_records = (
                supabase.table("ganesh_idols")
                .select("*")
                .eq("station_name", selected_stn)
                .execute()
            )
            stn_records = (
                res_stn_records.data if res_stn_records.data else []
            )
        except Exception:
            stn_records = []

        entered_val = len(stn_records)
        remaining_val = (
            max(0, target_val - entered_val) if target_val > 0 else 0
        )

        # Read-Only Progress Display
        col_t1, col_t2, col_t3 = st.columns(3)
        col_t1.metric(
            "ನಿಗದಿತ ಒಟ್ಟು ಗಣೇಶ ಮೂರ್ತಿಗಳು (Division Target)",
            target_val if target_val > 0 else "ನಿಗದಿಯಾಗಿಲ್ಲ",
        )
        col_t2.metric("ದಾಖಲಿಸಲಾದ ವಿವರಗಳು (Entered)", entered_val)
        col_t3.metric(
            "ದಾಖಲಿಸಲು ಬಾಕಿ ಇರುವ ವಿವರಗಳು (Remaining)", remaining_val
        )

        if target_val == 0:
            st.info(
                "ℹ️ ಸೂಚನೆ: ನಿಮ್ಮ ಠಾಣೆಗೆ ನಿಗದಿತ ಒಟ್ಟು ಗಣೇಶ ಮೂರ್ತಿಗಳ ಸಂಖ್ಯೆಯನ್ನು ವಿಭಾಗೀಯ ಕಚೇರಿಯಿಂದ (Division Control) ಇನ್ನು ನಮೂದಿಸಬೇಕಾಗಿದೆ."
            )

        # Display persistent submission success notification if available
        if st.session_state.get("show_writer_success_msg"):
            st.success(st.session_state["show_writer_success_msg"], icon="✅")
            del st.session_state["show_writer_success_msg"]

        st.markdown("---")

        # Form accepting SP Office Unique ID & Unicode Kannada text
        with st.form("station_writer_form"):
            sp_unique_id = st.text_input(
                "ಜಿಲ್ಲಾ ಕಚೇರಿಯಿಂದ ನೀಡಲಾದ ಸಂಖ್ಯೆ (SP Office Unique ID) :",
                placeholder="ಉದಾ: SP/GNS/2026/01",
            )
            pandal_name = st.text_input(
                "ಗಣೇಶೋತ್ಸವ ಸಮಿತಿಯ ಹೆಸರು :",
                placeholder="ಉದಾ: ಶ್ರೀ ವಿನಾಯಕ ಯುವಕ ಮಂಡಳಿ",
            )
            location_address = st.text_input(
                "ಪ್ರತಿಷ್ಠಾಪನೆಯಾಗುವ ಸ್ಥಳ :",
                placeholder="ಉದಾ: ಬಸ್ ನಿಲ್ದಾಣದ ಹತ್ತಿರ",
            )

            col_beat, col_staff = st.columns(2)
            beat_number = col_beat.number_input(
                "ಬೀಟ್ ನಂಬರ :", min_value=1, max_value=100, value=1
            )
            beat_staff_details = col_staff.text_input(
                "ಬೀಟ್ ಸಿಬ್ಬಂದಿ ವಿವರ (ಹೆಸರು, ಮೊಬೈಲ್ ನಂ) :",
                placeholder="ಉದಾ: ಹೆಚ್‌ಸಿ 452 ರಮೇಶ್, 9876543210",
            )

            install_date = st.date_input(
                "ಗಣೇಶ ಪ್ರತಿಷ್ಠಾಪನ ದಿನಾಂಕ :",
                datetime.date.today(),
                format="DD/MM/YYYY",
            )

            col_p1, col_p2 = st.columns(2)
            president_name = col_p1.text_input(
                "ಕಮಿಟಿ ಅಧ್ಯಕ್ಷರ ಹೆಸರು :", placeholder="ಅಧ್ಯಕ್ಷರ ಹೆಸರು"
            )
            president_phone = col_p2.text_input(
                "ಮೊಬೈಲ್ ನಂ (ಅಧ್ಯಕ್ಷರು) :", placeholder="9876543210"
            )

            col_v1, col_v2 = st.columns(2)
            vice_president_name = col_v1.text_input(
                "ಕಮಿಟಿ ಉಪಾಧ್ಯಕ್ಷರ ಹೆಸರು :", placeholder="ಉಪಾಧ್ಯಕ್ಷರ ಹೆಸರು"
            )
            vice_president_phone = col_v2.text_input(
                "ಮೊಬೈಲ್ ನಂ (ಉಪಾಧ್ಯಕ್ಷರು) :", placeholder="9876543210"
            )

            sensitivity_level = st.selectbox(
                "ವರ್ಗ :", ["ಸಾಮಾನ್ಯ", "ಸೂಕ್ಷ್ಮ", "ಅತೀಸೂಕ್ಷ್ಮ"]
            )

            immersion_date = st.date_input(
                "ವಿಸರ್ಜನೆಯಾಗುವ ದಿನಾಂಕ :",
                datetime.date.today(),
                format="DD/MM/YYYY",
            )

            sensitive_route_details = st.text_area(
                "ಮಾರ್ಗಮಧ್ಯದಲ್ಲಿರುವ ಮಸೀದಿ ಹಾಗೂ ಚರ್ಚಗಳ ವಿವರ :",
                placeholder="ವಿವರಗಳನ್ನು ಇಲ್ಲಿ ಟೈಪ್ ಮಾಡಿ...",
            )

            past_incident_details = st.text_area(
                "ಈ ಹಿಂದೆ ನಡೆದ ಘಟನೆ/ಪ್ರಕರಣಗಳ ವಿವರ :",
                placeholder="ವಿವರಗಳನ್ನು ಇಲ್ಲಿ ಟೈಪ್ ಮಾಡಿ...",
            )

            submit_btn = st.form_submit_button(
                "ಮಾಹಿತಿ ಸಲ್ಲಿಸಿ (Submit Record)"
            )

            if submit_btn:
                if not sp_unique_id.strip():
                    st.warning(
                        "ದಯವಿಟ್ಟು 'ಜಿಲ್ಲಾ ಕಚೇರಿಯಿಂದ ನೀಡಲಾದ ಸಂಖ್ಯೆ'ಯನ್ನು ನಮೂದಿಸಿ."
                    )
                elif not pandal_name.strip():
                    st.warning(
                        "ದಯವಿಟ್ಟು ಗಣೇಶೋತ್ಸವ ಸಮಿತಿಯ ಹೆಸರನ್ನು ನಮೂದಿಸಿ."
                    )
                else:
                    record = {
                        "id": str(sp_unique_id).strip(),
                        "station_name": str(selected_stn),
                        "pandal_name": str(pandal_name).strip(),
                        "location_address": (
                            str(location_address).strip()
                            if location_address
                            else ""
                        ),
                        "beat_number": int(beat_number),
                        "beat_staff_details": (
                            str(beat_staff_details).strip()
                            if beat_staff_details
                            else ""
                        ),
                        "installation_date": install_date.strftime("%Y-%m-%d"),
                        "president_name": (
                            str(president_name).strip()
                            if president_name
                            else ""
                        ),
                        "president_phone": (
                            str(president_phone).strip()
                            if president_phone
                            else ""
                        ),
                        "vice_president_name": (
                            str(vice_president_name).strip()
                            if vice_president_name
                            else ""
                        ),
                        "vice_president_phone": (
                            str(vice_president_phone).strip()
                            if vice_president_phone
                            else ""
                        ),
                        "sensitivity_level": str(sensitivity_level),
                        "immersion_date": immersion_date.strftime("%Y-%m-%d"),
                        "sensitive_route_details": (
                            str(sensitive_route_details).strip()
                            if sensitive_route_details
                            else ""
                        ),
                        "past_incident_details": (
                            str(past_incident_details).strip()
                            if past_incident_details
                            else ""
                        ),
                    }
                    try:
                        supabase.table("ganesh_idols").insert(record).execute()

                        updated_entered = entered_val + 1
                        updated_remaining = (
                            max(0, target_val - updated_entered)
                            if target_val > 0
                            else 0
                        )

                        st.session_state["show_writer_success_msg"] = (
                            f"ವರದಿಯನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಸಲ್ಲಿಸಲಾಗಿದೆ! (Report Submitted Successfully!) - unique ID: {sp_unique_id}. "
                            f"ಮಾಹಿತಿ ಸಲ್ಲಿಸಲು ಬಾಕಿ ಇರುವ ಗಣೇಶ ಮೂರ್ತಿಗಳ ವಿವರ: {updated_remaining}"
                        )
                        st.rerun()
                    except Exception as db_err:
                        st.error(
                            f"ಡೇಟಾಬೇಸ್‌ನಲ್ಲಿ ದಾಖಲಿಸಲು ಸಾಧ್ಯವಾಗಿಲ್ಲ: {db_err}"
                        )

        # Display Station Submitted Details Table (Fetched directly from Supabase)
        st.markdown("---")
        st.subheader(
            f"📋 {selected_stn} ಠಾಣೆಯಲ್ಲಿ ನಮೂದಿಸಲಾದ ಎಲ್ಲಾ ವಿವರಗಳು (Submitted Station Records)"
        )

        df_stn = pd.DataFrame(stn_records) if stn_records else pd.DataFrame()
        if not df_stn.empty:
            if "id" in df_stn.columns:
                cols_stn = ["id"] + [c for c in df_stn.columns if c != "id"]
                df_stn = df_stn[cols_stn]
            st.dataframe(df_stn, use_container_width=True)
        else:
            st.info("ಈ ಠಾಣೆಗೆ ಯಾವುದೇ ವಿವರಗಳನ್ನು ಇನ್ನು ನಮೂದಿಸಲಾಗಿಲ್ಲ.")

# ==========================================
# 3. BEAT STAFF FIELD UPDATE INTERFACE
# ==========================================
elif role == "ಬೀಟ್ ಸಿಬ್ಬಂದಿ (Beat Staff)":
    st.header("ಬೀಟ್ ಸಿಬ್ಬಂದಿ ಕ್ಷೇತ್ರ ವರದಿ")

    default_stations = [
        "Haliyal",
        "Dandeli Town",
        "Dandeli Rural",
        "Ambikanagar",
        "Ramanagar",
        "Joida",
    ]

    try:
        res_stns = (
            supabase.table("police_stations").select("station_name").execute()
        )
        added_stns = (
            [r["station_name"] for r in res_stns.data] if res_stns.data else []
        )
        station_options = sorted(list(set(default_stations + added_stns)))
    except Exception:
        station_options = default_stations

    selected_stn = st.selectbox(
        "ನಿಮ್ಮ ಠಾಣೆ ಆಯ್ಕೆಮಾಡಿ", station_options, key="staff_stn"
    )
    beat_num = st.number_input(
        "ನಿಮ್ಮ ಬೀಟ್ ಸಂಖ್ಯೆ",
        min_value=1,
        max_value=50,
        value=1,
        key="staff_beat",
    )

    try:
        res = (
            supabase.table("ganesh_idols")
            .select("*")
            .eq("station_name", selected_stn)
            .eq("beat_number", beat_num)
            .execute()
        )
        idols_in_beat = res.data if res.data else []
    except Exception as e:
        st.error(f"Error fetching beat data: {e}")
        idols_in_beat = []

    if not idols_in_beat:
        st.info("ಈ ಬೀಟ್‌ನಲ್ಲಿ ಯಾವುದೇ ಗಣೇಶ ಮೂರ್ತಿಗಳು ನೋಂದಾಯಿಸಲ್ಪಟ್ಟಿಲ್ಲ.")
    else:
        pandal_options = {
            f"[{i.get('id', 'N/A')}] {i.get('pandal_name', 'N/A')} ({i.get('sensitivity_level', 'ಸಾಮಾನ್ಯ')})": i
            for i in idols_in_beat
        }
        selected_key = st.selectbox(
            "ಗಣೇಶ ಮಂಡಳಿಯನ್ನು ಆಯ್ಕೆಮಾಡಿ", list(pandal_options.keys())
        )
        selected_idol = pandal_options[selected_key]

        st.write(
            f"**ಜಿಲ್ಲಾ ಕಚೇರಿ ನೀಡಿದ ಸಂಖ್ಯೆ (ID):** {selected_idol.get('id', 'N/A')}"
        )
        st.write(
            f"**ವರ್ಗ (Category):** {selected_idol.get('sensitivity_level', 'ಸಾಮಾನ್ಯ')}"
        )
        st.write(f"**ಸ್ಥಳ:** {selected_idol.get('location_address', '')}")
        st.write(
            f"**ವಿಸರ್ಜನೆ ದಿನಾಂಕ:** {selected_idol.get('immersion_date', '')}"
        )
        st.write(
            f"**ಮಾರ್ಗ ವಿವರ:** {selected_idol.get('sensitive_route_details', 'ಲಭ್ಯವಿಲ್ಲ')}"
        )

        st.subheader("ಸ್ಥಿತಿ ನವೀಕರಿಸಿ")
        install_status = st.radio(
            "ಪ್ರತಿಷ್ಠಾಪನೆ ಸ್ಥಿತಿ",
            ["ಪೆಂಡಿಂಗ್", "ಶಾಂತಿಯುತವಾಗಿ ಪೂರ್ಣಗೊಂಡಿದೆ", "ಸಮಸ್ಯೆ ವರದಿಯಾಗಿದೆ"],
            index=0,
        )
        immersion_status = st.radio(
            "ವಿಸರ್ಜನೆ ಸ್ಥಿತಿ",
            [
                "ಪ್ರಾರಂಭವಾಗಿಲ್ಲ",
                "ಮೆರವಣಿಗೆಯಲ್ಲಿದೆ",
                "ಶಾಂತಿಯುತವಾಗಿ ಪೂರ್ಣಗೊಂಡಿದೆ",
            ],
            index=0,
        )

        if st.button("ಸ್ಥಿತಿ ಅಪ್‌ಡೇಟ್ ಮಾಡಿ"):
            try:
                supabase.table("ganesh_idols").update({
                    "installation_status": install_status,
                    "immersion_status": immersion_status,
                }).eq("id", selected_idol["id"]).execute()
                st.success("ಸ್ಥಿತಿಯನ್ನು ಯಶಸ್ವಿಯಾಗಿ ನವೀಕರಿಸಲಾಗಿದೆ!")
            except Exception as update_err:
                st.error(f"Error updating status: {update_err}")
