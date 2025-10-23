import streamlit as st
from database import get_connection
import streamlit_authenticator as stauth
import os, json

# --- LOAD OR CREATE CREDENTIALS ---
if os.path.exists("credentials.json"):
    with open("credentials.json", "r") as f:
        credentials = json.load(f)
else:
    from credentials import credentials


def save_credentials():
    with open("credentials.json", "w") as f:
        json.dump(credentials, f)


# --- AUTH SETUP ---
authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name="ticket_app",
    key="abcdef",
    cookie_expiry_days=1,
)

st.set_page_config(page_title="Ticket System", layout="centered")

# --- FIX: ensure streamlit_authenticator has required session keys ---
if "logout" not in st.session_state:
    st.session_state["logout"] = None
if "name" not in st.session_state:
    st.session_state["name"] = None
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None

# --- DATABASE CONNECTION ---
conn, c = get_connection()

# --- LOGIN / SIGNUP SWITCH ---
# --- LOGIN / SIGNUP ---
if st.session_state.get("authentication_status") is None:
    auth_mode = st.radio("Select Mode", ["Login", "Signup"], horizontal=True)

    if auth_mode == "Login":
        authenticator.login(location="main")

    elif auth_mode == "Signup":
        st.subheader("Create a New Account")
        with st.form("signup_form"):
            new_username = st.text_input("Choose a Username").strip()
            new_password = st.text_input("Choose a Password", type="password")
            signup_submit = st.form_submit_button("Signup")

            if signup_submit:
                if not new_username or not new_password:
                    st.error("All fields are required.")
                elif new_username in credentials["usernames"]:
                    st.error("That username already exists. Please choose another.")
                else:
                    credentials["usernames"][new_username] = {
                        "name": new_username,
                        "password": new_password,
                        "role": "user",
                    }
                    save_credentials()
                    st.success("Signup successful! You can now log in.")
                    st.session_state["authentication_status"] = None
                    st.session_state["username"] = None
                    st.rerun()

# --- MAIN APP LOGIC ---
if st.session_state.get("authentication_status"):
    name = st.session_state.get("name")
    username = st.session_state.get("username")
    user_role = credentials["usernames"][username]["role"]

    st.sidebar.title("Ticket System")
    authenticator.logout("Logout", "sidebar")
    st.sidebar.write(f"Logged in as: **{username} ({user_role})**")

    if user_role == "user":
        from views.user_view import user_view

        user_view(username, conn, c)
    elif user_role == "admin":
        from views.admin_view import admin_view

        admin_view(conn, c)

elif st.session_state.get("authentication_status") is False:
    st.error("Username/password is incorrect.")
else:
    st.warning("Please log in to continue.")
