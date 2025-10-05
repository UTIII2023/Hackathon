# Dash Board.py
import streamlit as st
import json
import os
import random
import time
import plotly.express as px
from datetime import datetime

# -----------------------
# Config / Paths
# -----------------------
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
USER_FILE = os.path.join(THIS_DIR, "user_data.json")
SIM_EXE_PATH = os.path.join(THIS_DIR, "hehehe.exe")

# -----------------------
# Load & Save user_data.json
# -----------------------
def load_user_data():
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w") as f:
            json.dump({}, f)
    with open(USER_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_user_data(data):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

user_data = load_user_data()

# -----------------------
# Resolve current user or guest
# -----------------------
def find_active_user_key():
    if st.session_state.get("current_user_email") and st.session_state.current_user_email in user_data:
        return st.session_state.current_user_email
    if st.session_state.get("current_user"):
        uname = st.session_state.current_user
        for email_key, info in user_data.items():
            if info.get("username") == uname:
                st.session_state.current_user_email = email_key
                return email_key
    if len(user_data) == 1:
        email_key = list(user_data.keys())[0]
        st.session_state.current_user_email = email_key
        return email_key
    return None

active_email = find_active_user_key()
active_user = user_data.get(active_email)

# Fallback to guest
if not active_user:
    if "temp_user" not in st.session_state:
        st.session_state.temp_user = {
            "username": "Guest",
            "projects": [],
            "has_downloaded": False,
            "last_login": datetime.today().strftime("%Y-%m-%d")
        }
    active_user = st.session_state.temp_user
    active_email = "guest@example.com"

if "projects" not in active_user:
    active_user["projects"] = []
if "has_downloaded" not in active_user:
    active_user["has_downloaded"] = False

# -----------------------
# Tip rotation
# -----------------------
TIPS = [
    "Healthy soil grows healthy crops—test your soil every season!",
    "Bees are nature’s pollinators—protect them to boost your yield.",
    "Crop rotation keeps soil nutrients balanced.",
    "Cover crops prevent erosion and feed your soil.",
    "Drip irrigation saves up to 60% water compared to sprinklers.",
    "Compost adds natural nutrients without chemicals.",
]

if "current_tip" not in st.session_state:
    st.session_state.current_tip = random.choice(TIPS)
if "last_change" not in st.session_state:
    st.session_state.last_change = time.time()

def rotate_tip():
    if time.time() - st.session_state.last_change > 6:
        st.session_state.current_tip = random.choice(TIPS)
        st.session_state.last_change = time.time()

rotate_tip()
st.markdown(f"""
    <div style='background: rgba(255,255,255,0.6); padding: 12px; border-radius: 14px; margin-bottom: 18px; color:#2e7d32;'>
        💡 <b>Tip:</b> {st.session_state.current_tip}
    </div>
""", unsafe_allow_html=True)

# -----------------------
# Sidebar
# -----------------------
st.sidebar.title("🌿 AgroDM Panel")
st.sidebar.success(f"User: {active_user.get('username','---')}")
st.sidebar.caption(f"Last login: {active_user.get('last_login','N/A')}")
st.sidebar.write("---")
st.sidebar.header("💬 Chatbot Croppy")
st.sidebar.write("https://huggingface.co/spaces/Fnf0709/agrodc")

# -----------------------
# Dashboard title
# -----------------------
st.title("📊 Dashboard")

# -----------------------
# First-time download
# -----------------------
if len(active_user["projects"]) == 0 and not active_user.get("has_downloaded", False):
    st.info("Looks like this is your first project — download the simulation to begin.")
    if os.path.exists(SIM_EXE_PATH):
        with open(SIM_EXE_PATH, "rb") as f:
            data_bytes = f.read()
        if st.button("⬇️ Download Simulation (first-time)", key="first_download_btn"):
            st.download_button(
                label="Click to save the simulation (.exe)",
                data=data_bytes,
                file_name=os.path.basename(SIM_EXE_PATH),
                mime="application/octet-stream",
                key="dl_btn_internal"
            )
            active_user["has_downloaded"] = True
            active_user["last_login"] = datetime.today().strftime("%Y-%m-%d")
            user_data[active_email] = active_user
            save_user_data(user_data)
            st.success("Download prepared. Button will disappear after refresh.")
            st.rerun()
    else:
        st.warning(f"Simulation file not found at {SIM_EXE_PATH}.")

# -----------------------
# Project Creation
# -----------------------
st.subheader("➕ Create New Project")
with st.form("create_proj_form"):
    p_name = st.text_input("Project Name")
    p_desc = st.text_area("Project Description")
    submitted = st.form_submit_button("Create Project")
    if submitted:
        if not p_name.strip():
            st.error("Please enter a valid project name.")
        else:
            new_project = {
                "name": p_name.strip(),
                "description": p_desc.strip(),
                "date": datetime.today().strftime("%Y-%m-%d"),
                "status": "Not Started",
                "last_modified": datetime.today().strftime("%Y-%m-%d"),
                "game_data": {},
            }
            active_user["projects"].append(new_project)
            user_data[active_email] = active_user
            save_user_data(user_data)
            st.success(f"✅ Project '{p_name}' created and saved!")
            st.rerun()

# -----------------------
# Project Status Chart
# -----------------------
st.subheader("📈 Overall Performance")
STATUS_OPTIONS = ["Not Started", "In Progress", "Partially Done", "Done"]
status_counts = {s: 0 for s in STATUS_OPTIONS}
for proj in active_user["projects"]:
    status_counts[proj.get("status","Not Started")] += 1

fig = px.pie(
    names=list(status_counts.keys()),
    values=list(status_counts.values()),
    title="Project Status Distribution",
    hole=0.35,
    color_discrete_sequence=px.colors.qualitative.Pastel
)
st.plotly_chart(fig, use_container_width=True)

# -----------------------
# List Projects
# -----------------------
st.subheader("📂 Your Projects")
if not active_user["projects"]:
    st.info("You don't have any projects yet.")
else:
    for idx, proj in enumerate(active_user["projects"]):
        key_prefix = f"proj_{idx}_"
        confirm_delete_key = key_prefix + "confirm_delete"

        with st.container():
            st.markdown(f"""
                <div style='background-color:#f9f9f9;border-radius:12px;padding:14px;margin-bottom:12px;'>
                    <h4 style='margin:0'>{proj['name']}</h4>
                    <p style='margin:0'><b>Status:</b> {proj['status']}</p>
                    <p style='margin:0'><b>Created:</b> {proj['date']}</p>
                    <p style='margin:0'><b>Last Modified:</b> {proj['last_modified']}</p>
                    <p style='margin-top:8px;margin-bottom:0'><b>Description:</b></p>
                    <div style='margin-top:6px'>{proj['description']}</div>
                </div>
            """, unsafe_allow_html=True)

            col_a, col_b = st.columns([3,1])
            with col_a:
                new_name = st.text_input("Edit name", value=proj["name"], key=key_prefix+"name")
                new_desc = st.text_area("Edit description", value=proj["description"], key=key_prefix+"desc", height=120)
            with col_b:
                new_status = st.selectbox("Status", STATUS_OPTIONS, index=STATUS_OPTIONS.index(proj.get("status","Not Started")), key=key_prefix+"status")
                
                # Save edits
                if st.button("💾 Save", key=key_prefix+"save"):
                    proj["name"] = new_name.strip()
                    proj["description"] = new_desc.strip()
                    proj["status"] = new_status
                    proj["last_modified"] = datetime.today().strftime("%Y-%m-%d")
                    user_data[active_email] = active_user
                    save_user_data(user_data)
                    st.success(f"Saved '{new_name}'")
                    st.rerun()

                # Delete project
                if confirm_delete_key not in st.session_state:
                    st.session_state[confirm_delete_key] = False
                if not st.session_state[confirm_delete_key]:
                    if st.button("🗑️ Delete", key=key_prefix+"delete"):
                        st.session_state[confirm_delete_key] = True
                else:
                    st.warning(f"Are you sure you want to delete '{proj['name']}'? This cannot be undone.")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("Yes, Delete", key=key_prefix+"delete_yes"):
                            active_user["projects"].pop(idx)
                            user_data[active_email] = active_user
                            save_user_data(user_data)
                            st.warning("Project deleted.")
                            st.rerun()
                    with col_no:
                        if st.button("Cancel", key=key_prefix+"delete_no"):
                            st.session_state[confirm_delete_key] = False

            st.write("**Simulation Data (preview):**")
            st.json(proj.get("game_data", {}), expanded=False)
            if st.button(f"🚀 Launch {proj['name']}", key=key_prefix+"launch"):
                st.info(f"Launching simulation for '{proj['name']}' (placeholder).")
