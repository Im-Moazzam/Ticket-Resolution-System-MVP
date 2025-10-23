import streamlit as st
import streamlit_authenticator as stauth
import sqlite3
import datetime

# --- DATABASE SETUP ---
conn = sqlite3.connect("tickets.db")
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS tickets
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT, email TEXT, subject TEXT,
              description TEXT, status TEXT,
              created_at TEXT, updated_at TEXT)''')
conn.commit()

# --- USER CREDENTIALS ---
credentials = {
    "usernames": {
        "admin": {
            "name": "Admin",
            "password": "1234",  # plain for now
            "role": "admin",
        },
        "user1": {
            "name": "User1",
            "password": "abcd",
            "role": "user",
        },
        "user2": {
            "name": "User2",
            "password": "xyz",
            "role": "user",
        },
    }
}

# --- AUTHENTICATION SETUP ---
authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name="ticket_app",
    key="abcdef",
    cookie_expiry_days=1,
)

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

    # --- USER VIEW ---
    if user_role == "user":
        st.title("Submit a Ticket")
        with st.form("ticket_form"):
            subject = st.text_input("Subject")
            description = st.text_area("Description")
            email = st.text_input("Your Email")
            submitted = st.form_submit_button("Submit Ticket")

            if submitted:
                if not subject.strip() or not description.strip() or not email.strip():
                    st.error("Please fill in all fields.")
                else:
                    c.execute("""
                        INSERT INTO tickets (name, email, subject, description, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        name, email, subject, description, "Open",
                        datetime.datetime.now(), datetime.datetime.now()
                    ))
                    conn.commit()
                    st.success("Your ticket has been submitted.")

        st.header("Your Tickets")
        user_tickets = c.execute(
            "SELECT id, subject, status, created_at FROM tickets WHERE name=? ORDER BY id DESC", (name,)
        ).fetchall()

        if user_tickets:
            for t in user_tickets:
                st.write(f"**ID:** {t[0]} | **Subject:** {t[1]} | **Status:** {t[2]} | **Created:** {t[3]}")
        else:
            st.info("You haven't submitted any tickets yet.")

    # --- ADMIN VIEW ---
    elif user_role == "admin":
        st.title("Admin Dashboard")
        tickets = c.execute("SELECT * FROM tickets ORDER BY id DESC").fetchall()
        if not tickets:
            st.info("No tickets yet.")
        else:
            for t in tickets:
                st.write("---")
                st.write(f"**ID:** {t[0]} | **Name:** {t[1]} | **Email:** {t[2]}")
                st.write(f"**Subject:** {t[3]}")
                st.write(f"**Description:** {t[4]}")
                st.write(f"**Status:** {t[5]}")
                if t[5] == "Open":
                    if st.button(f"Mark as Resolved (Ticket {t[0]})"):
                        c.execute(
                            "UPDATE tickets SET status=?, updated_at=? WHERE id=?",
                            ("Resolved", datetime.datetime.now(), t[0])
                        )
                        conn.commit()
                        st.success(f"Ticket {t[0]} marked as resolved.")
                        st.rerun()

elif st.session_state.get("authentication_status") is False:
    st.error("Username/password is incorrect.")
else:
    st.warning("Please log in to continue.")
