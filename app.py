import streamlit as st
from database import get_connection
import hashlib

# --- DATABASE CONNECTION ---
conn, c = get_connection()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


st.set_page_config(page_title="Ticket System", layout="centered")

# --- LOGIN / SIGNUP STATE ---
if "auth_status" not in st.session_state:
    st.session_state["auth_status"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None

if st.session_state["auth_status"] is None:
    mode = st.radio("Select Mode", ["Login", "Signup"], horizontal=True)

    if mode == "Signup":
        st.subheader("Create Account")
        with st.form("signup_form"):
            username = st.text_input("Username").strip().lower()
            email = st.text_input("Email").strip()
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign Up")

            if submit:
                if not username or not email or not password:
                    st.error("All fields are required.")
                else:
                    c.execute("SELECT * FROM users WHERE username=?", (username,))
                    if c.fetchone():
                        st.error("Username already exists.")
                    else:
                        c.execute(
                            "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, 'user')",
                            (username, email, hash_password(password)),
                        )
                        conn.commit()
                        st.markdown(
                            f"<p style='color:green; font-weight:bold;'>Account for <b>{username}</b> created successfully!</p>",
                            unsafe_allow_html=True,
                        )
                        st.info("You can now log in.")

    elif mode == "Login":
        st.subheader("Login to Continue")
        with st.form("login_form"):
            username = st.text_input("Username").strip().lower()
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")

            if login_btn:
                c.execute(
                    "SELECT username, password, role FROM users WHERE username=?",
                    (username,),
                )
                user = c.fetchone()
                if user and user[1] == hash_password(password):
                    st.session_state["auth_status"] = True
                    st.session_state["username"] = username
                    st.session_state["role"] = user[2]
                    st.success(f"Welcome {username}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

# --- MAIN APP AFTER LOGIN ---
if st.session_state["auth_status"]:
    username = st.session_state["username"]
    role = st.session_state["role"]

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

    # --- LOGGED-IN INFO + LOGOUT BUTTON INLINE ---
    info_col, button_col = st.columns([8, 2])
    with info_col:
        st.markdown(
            f"""
            <div style='display:flex; align-items:center; height:100%;'>
                <span style='font-size:16px; color:#555;'>Logged in as: <b>{username}</b></span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with button_col:
        if st.button("Logout"):
            for key in ["auth_status", "username", "role"]:
                st.session_state[key] = None
            st.rerun()

    # --- LOAD USER OR ADMIN VIEW ---
    if role == "user":
        from views.user_view import user_view

        user_view(username, conn, c)
    else:
        from views.admin_view import admin_view

        admin_view(conn, c)
