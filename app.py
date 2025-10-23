import streamlit as st
from database import get_connection
from credentials import credentials
from views.user_view import user_view
from views.admin_view import admin_view
import streamlit_authenticator as stauth

# --- DATABASE CONNECTION ---
conn, c = get_connection()

# --- AUTHENTICATOR SETUP ---
authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name="ticket_app",
    key="abcdef",
    cookie_expiry_days=1,
)

st.set_page_config(page_title="Ticket System", layout="centered")

# --- ENSURE REQUIRED SESSION KEYS ---
for key in ["logout", "name", "authentication_status", "username"]:
    if key not in st.session_state:
        st.session_state[key] = None

# --- LOGIN / SIGNUP TABS ---
if not st.session_state.get("authentication_status"):
    tab1, tab2 = st.tabs(["Login", "Signup"])

    # --- LOGIN TAB ---
    with tab1:
        authenticator.login(location="main")

    # --- SIGNUP TAB ---
    with tab2:
        st.subheader("Create Account")
        with st.form("signup_form"):
            new_username = st.text_input("Username").strip().lower()
            new_email = st.text_input("Email").strip()
            new_password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign Up")

            if submit:
                if not new_username or not new_email or not new_password:
                    st.error("All fields are required.")
                else:
                    # Check if username already exists in DB
                    c.execute("SELECT * FROM users WHERE username=?", (new_username,))
                    if c.fetchone():
                        st.error("Username already exists.")
                    else:
                        # Insert new user into DB with default role "user"
                        c.execute(
                            "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, 'user')",
                            (new_username, new_email, new_password),
                        )
                        conn.commit()

                        # Update credentials dict for immediate login
                        credentials["usernames"][new_username] = {
                            "name": new_username,
                            "email": new_email,
                            "password": new_password,
                            "role": "user",
                        }

                        st.success(f"Account for {new_username} created successfully!")
                        st.info("You can now log in on the Login tab.")

# --- MAIN APP LOGIC AFTER LOGIN ---
if st.session_state.get("authentication_status"):
    name = st.session_state.get("name")
    username = st.session_state.get("username")
    user_role = credentials["usernames"][username]["role"]

    # --- TOP HEADER ---
    st.markdown(
        """
        <div style="background-color:#f8f9fa;padding:20px;border-radius:10px;
                    box-shadow:0 2px 6px rgba(0,0,0,0.1);margin-bottom:10px;">
            <h2 style="text-align:center;color:#333;margin:0;">Welcome to Ticket Portal</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- LOGGED-IN INFO + LOGOUT INLINE ---
    info_col, button_col = st.columns([8, 2])
    with info_col:
        st.markdown(
            f"""
            <div style='display:flex; align-items:center; height:100%;'>
                <span style='font-size:16px; color:#555;'>Logged in as: <b>{name}</b> ({user_role})</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with button_col:
        if st.button("Logout"):
            authenticator.logout("main")  # logs out and clears session properly
            st.session_state["name"] = None
            st.session_state["username"] = None
            st.session_state["authentication_status"] = None
            st.rerun()

    # --- LOAD USER OR ADMIN VIEW ---
    if user_role == "user":
        user_view(name, conn, c)
    elif user_role == "admin":
        admin_view(conn, c)

elif st.session_state.get("authentication_status") is False:
    st.error("Username/password is incorrect.")
else:
    st.warning("Please log in to continue.")
