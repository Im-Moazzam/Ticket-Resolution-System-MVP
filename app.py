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

# --- SESSION KEYS SAFETY CHECK ---
for key in ["logout", "name", "authentication_status", "username"]:
    if key not in st.session_state:
        st.session_state[key] = None

# --- DATABASE CONNECTION ---
conn, c = get_connection()

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

# --- MAIN APP SECTION ---
elif st.session_state.get("authentication_status"):
    name = st.session_state.get("name")
    username = st.session_state.get("username")
    user_role = credentials["usernames"][username]["role"]

    # --- HEADER BAR ---
    st.markdown(
        """
        <div style="
            background-color:#f8f9fa;
            padding:20px 40px;
            border-radius:12px;
            box-shadow:0 2px 6px rgba(0,0,0,0.1);
            margin-bottom:25px;
        ">
            <h2 style="margin:0; text-align:center; color:#333;">
                Welcome to Ticket Portal
            </h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- BELOW HEADER: USER INFO + LOGOUT ---
    left, right = st.columns([7, 1])
    with left:
        st.markdown(
            f"<p style='font-size:16px; color:#555; font-weight:500;'>"
            f"Logged in as: <b>{username}</b>"
            f"</p>",
            unsafe_allow_html=True,
        )
    with right:
        authenticator.logout("Logout", "main")

    # --- USER / ADMIN VIEW SWITCH ---
    if user_role == "user":
        from views.user_view import user_view

        user_view(username, conn, c)
    elif user_role == "admin":
        from views.admin_view import admin_view

        admin_view(conn, c)

# --- INVALID LOGIN ---
elif st.session_state.get("authentication_status") is False:
    st.error("Username/password is incorrect.")

# --- NO LOGIN YET ---
else:
    st.warning("Please log in to continue.")
