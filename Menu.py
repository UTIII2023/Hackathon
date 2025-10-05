import streamlit as st
import os
import json
import random
import time
from datetime import datetime
import hashlib

def image_carousel(image_paths, key="carousel"):
    """
    Displays a simple image carousel with left/right buttons.

    Args:
        image_paths (list): List of image file paths or URLs.
        key (str): Unique key for session state.
    """
    # Initialize carousel index in session state
    if f"{key}_index" not in st.session_state:
        st.session_state[f"{key}_index"] = 0

    # Display current image
    current_index = st.session_state[f"{key}_index"]
    st.image(image_paths[current_index], use_container_width=True)

    # Create navigation buttons
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        if st.button("⬅️", key=f"{key}_prev"):
            st.session_state[f"{key}_index"] = (current_index - 1) % len(image_paths)
            st.rerun()
    with col3:
        if st.button("➡️", key=f"{key}_next"):
            st.session_state[f"{key}_index"] = (current_index + 1) % len(image_paths)
            st.rerun()

# -------------------------
# 🌟 Page Setup
# -------------------------
st.set_page_config(page_title="AgroDM", layout="wide")

USER_DATA_FILE = "user_data.json"

# -------------------------
# 🌾 Helper Functions
# -------------------------
def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

def update_streak(user):
    today = str(datetime.date.today())
    last_login = user.get("last_login")
    if last_login == today:
        return
    if last_login:
        last_date = datetime.datetime.strptime(last_login, "%Y-%m-%d").date()
        diff = (datetime.date.today() - last_date).days
        user["streak"] = user.get("streak", 0) + 1 if diff == 1 else 0
    else:
        user["streak"] = 1
    user["last_login"] = today

def safe_image(img_path, **kwargs):
    if os.path.exists(img_path):
        st.image(img_path, **kwargs)
    else:
        st.warning(f"Image not found: {img_path}")

# -------------------------
# 🌾 Tips Setup (Logged-in only)
# -------------------------
TIPS = [
    "Healthy soil grows healthy crops—test your soil every season!",
    "Bees are nature’s pollinators—protect them to boost your yield.",
    "Crop rotation keeps soil nutrients balanced.",
    "Cover crops prevent erosion and feed your soil.",
    "Drip irrigation saves up to 60% water compared to sprinklers.",
    "Compost adds natural nutrients without chemicals.",
    "Harvesting early morning preserves flavor and freshness.",
    "Shade-loving plants thrive under partial sunlight.",
    "A handful of worms means your soil is alive!",
    "Organic mulch reduces weeds naturally.",
    # (add all other tips from your previous list)
]

if "show_tip" not in st.session_state:
    st.session_state.show_tip = True
if "current_tip" not in st.session_state:
    st.session_state.current_tip = random.choice(TIPS)
if "last_change" not in st.session_state:
    st.session_state.last_change = time.time()

def rotate_tip():
    if time.time() - st.session_state.last_change > 6:
        st.session_state.current_tip = random.choice(TIPS)
        st.session_state.last_change = time.time()

# -------------------------
# 🌿 Sidebar Login / Signup
# -------------------------
users = load_users()
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "email" not in st.session_state:
    st.session_state.email = None

st.sidebar.title("🌿 AgroDM Panel")

if not st.session_state.logged_in:
    choice = st.sidebar.radio("Select an option", ["Login", "Sign Up"])
    if choice == "Login":
        email = st.sidebar.text_input("Email")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            if email in users and verify_password(password, users[email]["password"]):
                st.session_state.logged_in = True
                st.session_state.email = email
                update_streak(users[email])
                save_users(users)
                st.success(f"✅ Welcome back, {users[email]['username']}!")
                st.rerun()
            else:
                st.error("❌ Invalid email or password.")
    else:
        email = st.sidebar.text_input("Email")
        username = st.sidebar.text_input("Username")
        age = st.sidebar.number_input("Age", min_value=5, max_value=100, step=1)
        password = st.sidebar.text_input("Password", type="password")
        confirm = st.sidebar.text_input("Confirm Password", type="password")
        if st.sidebar.button("Sign Up"):
            if not email or not username or not password:
                st.warning("⚠️ Fill all fields.")
            elif password != confirm:
                st.warning("⚠️ Passwords don’t match.")
            elif email in users:
                st.warning("⚠️ Email already registered.")
            else:
                users[email] = {
                    "username": username,
                    "age": age,
                    "password": hash_password(password),
                    "streak": 0,
                    "created": str(datetime.date.today()),
                    "last_login": None,
                    "projects": []
                }
                save_users(users)
                st.success("✅ Account created! You can now log in.")
else:
    st.sidebar.success(f"Logged in as {users[st.session_state.email]['username']}")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.email = None
        st.rerun()

# -------------------------
# 🌄 Menu Page (Visible to all)
# -------------------------

# ---------------- Top: Menu ----------------
st.image("mainmenu.jpeg", use_container_width=True)
st.markdown(
    '<div style="text-align:center;font-size:50px;font-weight:bold;color:white;'
    'text-shadow:2px 2px 5px black;margin-top:-200px;">AgroDM - Agricultural Decision Making</div>',
    unsafe_allow_html=True
)
st.write("---")

st.subheader("WELCOME TO AGRODM!")
st.write(
    "AgroDM is a web application designed for farmers and hobbyists to simulate the development "
    "of their farms. It provides a virtual environment where users can observe the outcomes of their decisions, "
    "learn, and adapt to modern farming techniques and technologies. By visualizing the effects of their choices, "
    "AgroDM offers a realistic and engaging experience powered by NASA’s datasets, helping users make informed decisions while having fun."
)

st.subheader("Menu Page")
st.write(
    "You are currently on the Menu page, the main hub of this web application. "
    "Here, you can find key information about the website, understand its structure — the logic connecting our simulation and platform — "
    "and begin your journey into agricultural decision-making."
)
st.image(r"C:/Users/yusuf/OneDrive/Resimler/Ekran Görüntüleri/Ekran görüntüsü 2025-10-05 145344.png", use_container_width=True)

st.write("---")

# ---------------- Middle: Dashboard Carousel ----------------
st.subheader("Dash Board")
st.write(
    "DashBoard is the page in which the website and the simulation connects. "
    "Here, you can create a new project, view your previous projects and their analyses. "
    "You will be led to download the simulation when creating your first project. "
    "Once created, you can view your previous projects, label, save, and launch them "
    "to help analyze your overall performance."
)

dashboard_images = [
    r"C:/Users/yusuf/OneDrive/Resimler/Ekran Görüntüleri/Ekran görüntüsü 2025-10-05 115157.png",
    r"C:/Users/yusuf/OneDrive/Resimler/Ekran Görüntüleri/Ekran görüntüsü 2025-10-05 115208.png",
    r"C:/Users/yusuf/OneDrive/Resimler/Ekran Görüntüleri/Ekran görüntüsü 2025-10-05 122311.png",
    r"C:/Users/yusuf/OneDrive/Resimler/Ekran Görüntüleri/Ekran görüntüsü 2025-10-05 122439.png"
]
image_carousel(dashboard_images, key="dashboard_gallery")

st.write("---")

# ---------------- Bottom: Profile Carousel ----------------
st.subheader("Profile and Settings")
st.write(
    "You should sign up and log in to save your progress and access your personalized farming data. "
    "You can create an account by selecting “Sign Up” on the Profile page, and once your account is created, you can log in. "
    "After logging in, a “Log Out” button will appear on the Profile page. "
    "You can also update or modify your information anytime through the Settings page."
)

profile_images = [
    r"C:/Users/yusuf/OneDrive/Resimler/Ekran Görüntüleri/Ekran görüntüsü 2025-10-05 115157.png",
    r"C:/Users/yusuf/OneDrive/Resimler/Ekran Görüntüleri/Ekran görüntüsü 2025-10-05 115208.png",
    r"C:/Users/yusuf/OneDrive/Resimler/Ekran Görüntüleri/Ekran görüntüsü 2025-10-05 122311.png",
    r"C:/Users/yusuf/OneDrive/Resimler/Ekran Görüntüleri/Ekran görüntüsü 2025-10-05 122439.png"
]
image_carousel(profile_images, key="profile_gallery")

# -------------------------
# 🌱 Project Section (Logged-in only)
# -------------------------
if st.session_state.logged_in:
    rotate_tip()
    st.markdown(f"""
        <div style='background: rgba(255,255,255,0.6); backdrop-filter: blur(8px); border-radius: 14px; border: 1px solid rgba(255,255,255,0.25); padding:12px 18px; margin-bottom:18px; color:#2e7d32; box-shadow:0 4px 10px rgba(0,0,0,0.08);'>
            💡 <b>Tip:</b> {st.session_state.current_tip}
        </div>
    """, unsafe_allow_html=True)

    user = users[st.session_state.email]

    # Add New Project
    st.divider()
    st.subheader("🌱 Create a New Project")
    with st.form("create_project_menu"):
        name = st.text_input("Project Name")
        description = st.text_area("Project Description")
        submitted = st.form_submit_button("Create Project")
        if submitted:
            if not name.strip():
                st.error("Please enter a valid project name.")
            else:
                new_project = {
                    "name": name.strip(),
                    "description": description.strip(),
                    "date": datetime.today().strftime("%Y-%m-%d"),
                    "status": "Not Started",
                    "last_modified": datetime.today().strftime("%Y-%m-%d"),
                    "game_data": {},
                }
                user["projects"].append(new_project)
                save_users(users)
                st.success(f"✅ Project '{name}' created successfully!")

    # List Existing Projects
    st.subheader("📂 Your Projects")
    if not user["projects"]:
        st.info("You don't have any projects yet.")
    else:
        STATUS_OPTIONS = ["Not Started", "In Progress", "Completed"]
        for idx, proj in enumerate(user["projects"]):
            key_prefix = f"proj_{idx}_"
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
                    new_name_edit = st.text_input("Edit name", value=proj["name"], key=key_prefix + "name")
                    new_desc_edit = st.text_area("Edit description", value=proj["description"], key=key_prefix + "desc", height=120)
                with col_b:
                    new_status_edit = st.selectbox("Status", options=STATUS_OPTIONS, index=STATUS_OPTIONS.index(proj.get("status","Not Started")), key=key_prefix + "status")
                    if st.button("💾 Save", key=key_prefix + "save"):
                        user["projects"][idx]["name"] = new_name_edit.strip()
                        user["projects"][idx]["description"] = new_desc_edit.strip()
                        user["projects"][idx]["status"] = new_status_edit
                        user["projects"][idx]["last_modified"] = datetime.today().strftime("%Y-%m-%d")
                        save_users(users)
                        st.success(f"Saved '{new_name_edit}'")
                        st.rerun()
                    if st.button("🗑️ Delete", key=key_prefix + "delete"):
                        user["projects"].pop(idx)
                        save_users(users)
                        st.warning("Project deleted.")
                        st.rerun()

                st.write("**Simulation Data (preview):**")
                st.json(proj.get("game_data", {}), expanded=False)
                if st.button(f"🚀 Launch {proj['name']}", key=key_prefix + "launch"):
                    st.info(f"Launching project '{proj['name']}'... (functionality to be implemented)")
