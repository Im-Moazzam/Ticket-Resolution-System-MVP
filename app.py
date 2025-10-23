import streamlit as st
from database import get_connection
from credentials import credentials
from views.user_view import user_view
from views.admin_view import admin_view
import streamlit_authenticator as stauth

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

# --- LOGIN ---
authenticator.login(location="main")

# --- MAIN APP LOGIC ---
if st.session_state.get("authentication_status"):
    name = st.session_state.get("name")
    username = st.session_state.get("username")
    user_role = credentials["usernames"][username]["role"]

    st.sidebar.title("Ticket System")
    authenticator.logout("Logout", "sidebar")
    st.sidebar.write(f"Logged in as: **{name} ({user_role})**")

    if user_role == "user":
        user_view(name, conn, c)
    elif user_role == "admin":
        admin_view(conn, c)

elif st.session_state.get("authentication_status") is False:
    st.error("Username/password is incorrect.")
else:
    st.warning("Please log in to continue.")
