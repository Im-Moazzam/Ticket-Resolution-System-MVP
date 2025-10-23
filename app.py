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

# --- ADD reopen_comment COLUMN IF NOT EXISTS ---
try:
    c.execute("ALTER TABLE tickets ADD COLUMN reopen_comment TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass  # column already exists

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
                    # Check for duplicate ticket
                    c.execute("""
                        SELECT COUNT(*) FROM tickets 
                        WHERE name=? AND subject=? AND description=? AND status='Open'
                    """, (name, subject.strip(), description.strip()))
                    duplicate_count = c.fetchone()[0]

                    if duplicate_count > 0:
                        st.warning("You have already submitted a ticket with the same subject and description.")
                    else:
                        # Insert new ticket
                        c.execute("""
                            INSERT INTO tickets (name, email, subject, description, status, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            name, email, subject.strip(), description.strip(), "Open",
                            datetime.datetime.now(), datetime.datetime.now()
                        ))
                        conn.commit()
                        st.success("Your ticket has been submitted.")
                        st.rerun()

        st.header("Your Tickets")
        user_tickets = pd.read_sql_query(
            "SELECT id, subject, status, created_at, reopen_comment FROM tickets WHERE name=? ORDER BY id DESC",
            conn, params=(name,)
        )

        if not user_tickets.empty:
            for _, row in user_tickets.iterrows():
                st.markdown(f"### {row['subject']} ({row['status']})")
                st.write(f"Created: {row['created_at']}")

                if row["status"] == "Reopened" and row["reopen_comment"]:
                    st.info(f"**Your comment:** {row['reopen_comment']}")

                if row["status"] in ["Resolved", "Discarded"]:
                    with st.expander("Reopen Ticket"):
                        comment = st.text_area(f"Comment (for ticket #{row['id']})", key=f"comment_{row['id']}")
                        if st.button(f"Reopen #{row['id']}", key=f"reopen_{row['id']}"):
                            if not comment.strip():
                                st.warning("Please add a comment before reopening.")
                            else:
                                c.execute("""
                                    UPDATE tickets 
                                    SET status='Reopened', reopen_comment=?, updated_at=?
                                    WHERE id=?
                                """, (comment.strip(), datetime.datetime.now(), row["id"]))
                                conn.commit()
                                st.success("Ticket reopened successfully.")
                                st.rerun()
                st.markdown("---")
        else:
            st.info("You haven't submitted any tickets yet.")

    # --- ADMIN VIEW ---
    elif user_role == "admin":
        st.title("Admin Dashboard")

        # --- Stats Section ---
        open_count = c.execute("SELECT COUNT(*) FROM tickets WHERE status='Open'").fetchone()[0]
        reopened_count = c.execute("SELECT COUNT(*) FROM tickets WHERE status='Reopened'").fetchone()[0]
        closed_count = c.execute("SELECT COUNT(*) FROM tickets WHERE status IN ('Resolved', 'Discarded')").fetchone()[0]

        col1, col2, col3 = st.columns(3)
        col1.markdown(
            f"<div style='background-color:#f8d7da;padding:15px;border-radius:10px;text-align:center;'>"
            f"<h2 style='color:#721c24;margin:0;'>Open</h2>"
            f"<h1 style='font-size:50px;margin:0;color:#000000;'>{open_count}</h1></div>",
            unsafe_allow_html=True
        )
        col2.markdown(
            f"<div style='background-color:#fff3cd;padding:15px;border-radius:10px;text-align:center;'>"
            f"<h2 style='color:#856404;margin:0;'>Reopened</h2>"
            f"<h1 style='font-size:50px;margin:0;color:#000000;'>{reopened_count}</h1></div>",
            unsafe_allow_html=True
        )
        col3.markdown(
            f"<div style='background-color:#d4edda;padding:15px;border-radius:10px;text-align:center;'>"
            f"<h2 style='color:#155724;margin:0;'>Closed</h2>"
            f"<h1 style='font-size:50px;margin:0;color:#000000;'>{closed_count}</h1></div>",
            unsafe_allow_html=True
        )

        st.markdown("---")

        # --- Fetch Tickets ---
        tickets = c.execute("SELECT * FROM tickets ORDER BY id DESC").fetchall()

        st.subheader("All Tickets")
        if not tickets:
            st.info("No tickets found.")
        else:
            for t in tickets:
                ticket_id, uname, email, subject, desc, status, created, updated, *rest = t
                reopen_comment = rest[0] if rest else None

                # Colors based on status
                if status == "Open":
                    bg, color = "#f8d7da", "#721c24"
                elif status == "Resolved":
                    bg, color = "#d4edda", "#155724"
                elif status == "Discarded":
                    bg, color = "#f5c6cb", "#721c24"
                elif status == "Reopened":
                    bg, color = "#fff3cd", "#856404"
                else:
                    bg, color = "#ffffff", "#000000"

                col1, col2, col3 = st.columns([6, 0.5, 0.5])
                with col1:
                    exp = st.expander(f"{uname} : {subject} ({status})")
                    with exp:
                        st.markdown(
                            f"""
                            <div style='background-color:{bg};padding:10px;border-radius:10px;margin-bottom:8px;color:{color};'>
                                <p><strong>Description:</strong> {desc}</p>
                                <p><strong>Email:</strong> {email}</p>
                                <p><strong>Submitted:</strong> {created}</p>
                                <p><strong>Last Updated:</strong> {updated}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        if reopen_comment:
                            st.warning(f"**Reopen Comment:** {reopen_comment}")

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

elif st.session_state.get("authentication_status") is False:
    st.error("Username/password is incorrect.")
else:
    st.warning("Please log in to continue.")
