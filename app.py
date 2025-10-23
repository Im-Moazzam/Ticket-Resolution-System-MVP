import streamlit as st
import streamlit_authenticator as stauth
import sqlite3
import datetime
import pandas as pd

# --- DATABASE SETUP ---
conn = sqlite3.connect("tickets.db", check_same_thread=False)
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
                    st.rerun()

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

        # --- Stats Section ---
        open_count = c.execute("SELECT COUNT(*) FROM tickets WHERE status='Open'").fetchone()[0]
        closed_count = c.execute("SELECT COUNT(*) FROM tickets WHERE status IN ('Resolved', 'Discarded')").fetchone()[0]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f"""
                <div style='background-color:#f8d7da;padding:15px;border-radius:10px;text-align:center;'>
                    <h2 style='color:#721c24;margin:0;'>Open Tickets</h2>
                    <h1 style='font-size:50px;margin:0;color:#000000;'>{open_count}</h1>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                f"""
                <div style='background-color:#d4edda;padding:15px;border-radius:10px;text-align:center;'>
                    <h2 style='color:#155724;margin:0;'>Closed Tickets</h2>
                    <h1 style='font-size:50px;margin:0;color:#000000;'>{closed_count}</h1>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("---")

        # --- Fetch Tickets ---
        open_tickets = c.execute("SELECT * FROM tickets WHERE status='Open' ORDER BY id DESC").fetchall()
        closed_tickets = c.execute("SELECT * FROM tickets WHERE status IN ('Resolved', 'Discarded') ORDER BY id DESC").fetchall()

        # --- ACTIVE TICKETS ---
        st.subheader("Active Tickets")
        if not open_tickets:
            st.info("No active tickets.")
        else:
            for t in open_tickets:
                ticket_id, uname, email, subject, desc, status, created, updated = t

                col1, col2, col3 = st.columns([6, 0.5, 0.5])
                with col1:
                    exp = st.expander(f"**{uname}** : {subject} ({status})")
                    with exp:
                        st.write(f"**Description:** {desc}")
                        st.write(f"**Email:** {email}")
                        st.write(f"**Submitted:** {created}")
                        st.write(f"**Last Updated:** {updated}")

                # --- Buttons with emojis only, centered ---
                with col2:
                    if st.button("✅", key=f"res_{ticket_id}"):
                        c.execute("UPDATE tickets SET status=?, updated_at=? WHERE id=?",
                                  ("Resolved", datetime.datetime.now(), ticket_id))
                        conn.commit()
                        st.rerun()

                with col3:
                    if st.button("🗑️", key=f"dis_{ticket_id}"):
                        c.execute("UPDATE tickets SET status=?, updated_at=? WHERE id=?",
                                  ("Discarded", datetime.datetime.now(), ticket_id))
                        conn.commit()
                        st.rerun()

        # --- CLOSED TICKETS ---
        st.subheader("Closed Tickets")
        if not closed_tickets:
            st.info("No closed tickets yet.")
        else:
            for t in closed_tickets:
                ticket_id, uname, email, subject, desc, status, created, updated = t
                bg_color = "#d4edda" if status == "Resolved" else "#f8d7da"
                text_color = "#155724" if status == "Resolved" else "#721c24"
                with st.expander(f"{uname} : {subject} ({status})"):
                    st.markdown(
                        f"""
                        <div style='background-color:{bg_color};padding:10px;border-radius:10px;margin-bottom:8px;color:{text_color};'>
                            <p><strong>Description:</strong> {desc}</p>
                            <p><strong>Email:</strong> {email}</p>
                            <p><strong>Submitted:</strong> {created}</p>
                            <p><strong>Last Updated:</strong> {updated}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

elif st.session_state.get("authentication_status") is False:
    st.error("Username/password is incorrect.")
else:
    st.warning("Please log in to continue.")
