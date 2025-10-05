import streamlit as st
import json
import os
import hashlib

USER_DATA_FILE = "user_data.json"

# --- Helpers ---
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

# --- Page setup ---
st.set_page_config(page_title="Settings", layout="wide")

if "logged_in" in st.session_state and st.session_state.logged_in:
    users = load_users()
    user = users[st.session_state.email]

    st.title("⚙️ Settings")
    st.write("Update your account details below:")

    new_username = st.text_input("Change Username", value=user["username"])
    new_age = st.number_input("Change Age", value=user["age"], min_value=5, max_value=100, step=1)
    new_password = st.text_input("New Password", type="password")

    if st.button("Save Changes"):
        user["username"] = new_username
        user["age"] = new_age
        if new_password:
            user["password"] = hash_password(new_password)
        save_users(users)
        st.success("Profile updated successfully!")


else:
    st.warning("Please log in first to access settings.")
    if st.button("⬅️ Back to Dashboard"):
        st.query_params["page"] = "dashboard"
        st.rerun()

st.write("For more information, please contact agrodecisionmaking@gmail.com")