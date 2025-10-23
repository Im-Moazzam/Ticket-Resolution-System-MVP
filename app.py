import streamlit as st
import streamlit_authenticator as stauth
import sqlite3
import datetime
import pandas as pd

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
        "admin": {"name": "Admin", "password": "1234", "role": "admin"},
        "user1": {"name": "User1", "password": "abcd", "role": "user"},
        "user2": {"name": "User2", "password": "xyz", "role": "user"},
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
        user_tickets = pd.read_sql_query(
            "SELECT id, subject, status, created_at FROM tickets WHERE name=? ORDER BY id DESC",
            conn, params=(name,)
        )
        if not user_tickets.empty:
            st.dataframe(user_tickets, use_container_width=True)
        else:
            st.info("You haven't submitted any tickets yet.")

    # --- ADMIN VIEW ---
    elif user_role == "admin":
        st.title("Admin Dashboard")

        # Stats
        open_count = c.execute("SELECT COUNT(*) FROM tickets WHERE status='Open'").fetchone()[0]
        resolved_count = c.execute("SELECT COUNT(*) FROM tickets WHERE status='Resolved'").fetchone()[0]
        st.subheader("Ticket Stats")
        st.write(f"Open Tickets: {open_count} | Resolved Tickets: {resolved_count}")

        tickets = c.execute("SELECT * FROM tickets ORDER BY id DESC").fetchall()
        if not tickets:
            st.info("No tickets yet.")
        else:
            for t in tickets:
                ticket_id, uname, email, subject, desc, status, created, updated = t

                header = f"{uname} : {subject} ({status})"
                with st.expander(header):
                    st.write(f"**Description:** {desc}")
                    st.write(f"**Email:** {email}")
                    st.write(f"**Submitted At:** {created}")
                    col1, col2 = st.columns(2)
                    if status == "Open":
                        if col1.button(f"Resolved ✅ - {ticket_id}", key=f"res_{ticket_id}"):
                            c.execute("UPDATE tickets SET status=?, updated_at=? WHERE id=?",
                                      ("Resolved", datetime.datetime.now(), ticket_id))
                            conn.commit()
                            st.experimental_rerun()
                        if col2.button(f"Discard ❌ - {ticket_id}", key=f"discard_{ticket_id}"):
                            c.execute("DELETE FROM tickets WHERE id=?", (ticket_id,))
                            conn.commit()
                            st.experimental_rerun()

elif st.session_state.get("authentication_status") is False:
    st.error("Username/password is incorrect.")
else:
    st.warning("Please log in to continue.")
