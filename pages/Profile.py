import streamlit as st
import json
import os
import datetime
import hashlib

USER_DATA_FILE = "user_data.json"
st.set_page_config(page_title="Profile", layout="wide")

# --- Helper functions ---
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
        user["streak"] = user["streak"] + 1 if diff == 1 else 0
    else:
        user["streak"] = 1

    user["last_login"] = today


# --- Sign Up ---
def signup():
    st.subheader("Create Account")
    email = st.text_input("Email")
    username = st.text_input("Username")
    age = st.number_input("Age", min_value=5, max_value=100, step=1)
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Sign Up"):
        if not email or not username or not password:
            st.error("Please fill all fields.")
            return
        if password != confirm:
            st.error("Passwords don’t match.")
            return

        users = load_users()
        if email in users:
            st.error("This email is already registered.")
            return

        users[email] = {
            "username": username,
            "age": age,
            "password": hash_password(password),
            "streak": 0,
            "created": str(datetime.date.today()),
            "last_login": None,
            "projects": []  # Initialize empty projects list
        }
        save_users(users)
        st.success("Account created! You can now log in.")


# --- Login ---
def login():
    st.subheader("Log In")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Log In"):
        users = load_users()
        if email not in users:
            st.error("No account found with that email.")
            return
        if not verify_password(password, users[email]["password"]):
            st.error("Incorrect password.")
            return

        # Ensure "projects" exists even for old users
        if "projects" not in users[email]:
            users[email]["projects"] = []

        update_streak(users[email])
        save_users(users)

        st.session_state.logged_in = True
        st.session_state.email = email
        st.success(f"Welcome back, {users[email]['username']}!")
        st.rerun()


# --- Logout ---
def logout():
    st.session_state.logged_in = False
    st.session_state.email = None
    st.rerun()


# --- Session init ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "email" not in st.session_state:
    st.session_state.email = None

# --- UI ---
if not st.session_state.logged_in:
    st.title("Welcome!")
    choice = st.radio("Choose:", ["Login", "Sign Up"])
    if choice == "Login":
        login()
    else:
        signup()
else:
    users = load_users()
    user = users[st.session_state.email]

    # Auto-fix for old accounts
    if "projects" not in user:
        user["projects"] = []
        save_users(users)

    st.title("👤 Your Profile")
    st.write(f"**Username:** {user['username']}")
    st.write(f"**Email:** {st.session_state.email}")
    st.write(f"**Age:** {user['age']}")
    st.write(f"**🔥 Streak:** {user['streak']}")
    st.write(f"**📅 Joined:** {user['created']}")

    # Dashboard navigation
    if st.button("🏠 Go to Dashboard"):
        st.switch_page("pages/Dash Board.py")  # Adjust name if needed

    st.divider()
    if st.button("Log Out"):
        logout()
