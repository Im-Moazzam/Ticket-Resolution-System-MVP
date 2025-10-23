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
              created_at TEXT, updated_at TEXT,
              comments TEXT)''')
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

    # ==================== USER VIEW ====================
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
                        SELECT COUNT(*) FROM tickets 
                        WHERE name=? AND subject=? AND description=? AND status='Open'
                    """, (name, subject.strip(), description.strip()))
                    if c.fetchone()[0] > 0:
                        st.warning("You already submitted this ticket.")
                    else:
                        c.execute("""
                            INSERT INTO tickets (name, email, subject, description, status, created_at, updated_at, comments)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            name, email, subject.strip(), description.strip(), "Open",
                            datetime.datetime.now(), datetime.datetime.now(), ""
                        ))
                        conn.commit()
                        st.success("Ticket submitted successfully.")
                        st.rerun()

        st.header("Your Tickets")
        user_tickets = pd.read_sql_query(
            "SELECT id, subject, status, created_at, comments FROM tickets WHERE name=? ORDER BY id DESC",
            conn, params=(name,)
        )

        if not user_tickets.empty:
            for _, row in user_tickets.iterrows():
                exp = st.expander(f"#{row['id']} — {row['subject']} ({row['status']})", expanded=False)
                with exp:
                    comments = (row['comments'] or "").strip().splitlines()
                    latest_admin_comment = ""
                    for line in reversed(comments):
                        if "Admin:" in line:
                            latest_admin_comment = line
                            break
                    if latest_admin_comment:
                        st.write("**Latest Admin Reply:**")
                        st.code(latest_admin_comment, language="text")
                    else:
                        st.write("No admin reply yet.")
        else:
            st.info("You haven't submitted any tickets yet.")

        st.markdown("---")
        st.subheader("Reopen a Ticket")

        with st.form("reopen_form"):
            reopen_id = st.number_input("Enter Ticket ID to Reopen", min_value=1, step=1)
            comment = st.text_area("Enter your comment or explanation")
            reopen_submit = st.form_submit_button("Reopen Ticket")

            if reopen_submit:
                ticket = c.execute("SELECT id, comments, status FROM tickets WHERE id=? AND name=?", (reopen_id, name)).fetchone()
                if not ticket:
                    st.error("Ticket not found or not owned by you.")
                elif ticket[2] in ("Open", "Reopened"):
                    st.warning("This ticket is already active.")
                else:
                    prev_comments = ticket[1] or ""
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                    new_comment = f"[{timestamp}] {name}: {comment.strip()}\n"
                    updated_comments = prev_comments + new_comment
                    c.execute("""
                        UPDATE tickets SET status='Reopened', comments=?, updated_at=?
                        WHERE id=?
                    """, (updated_comments, datetime.datetime.now(), reopen_id))
                    conn.commit()
                    st.success("Ticket reopened successfully.")
                    st.rerun()

    # ==================== ADMIN VIEW ====================
    elif user_role == "admin":
        st.title("Admin Dashboard")

        # Stats
        open_count = c.execute("SELECT COUNT(*) FROM tickets WHERE status='Open'").fetchone()[0]
        reopened_count = c.execute("SELECT COUNT(*) FROM tickets WHERE status='Reopened'").fetchone()[0]
        closed_count = c.execute("SELECT COUNT(*) FROM tickets WHERE status IN ('Resolved', 'Discarded')").fetchone()[0]

        col1, col2, col3 = st.columns(3)
        col1.markdown(
            f"<div style='background-color:#d1ecf1;padding:20px;border-radius:15px;text-align:center;'>"
            f"<h2 style='color:#0c5460;margin:0;'>Open</h2>"
            f"<h1 style='font-size:60px;margin:0;color:#000;'>{open_count}</h1></div>",
            unsafe_allow_html=True
        )
        col2.markdown(
            f"<div style='background-color:#fff3cd;padding:20px;border-radius:15px;text-align:center;'>"
            f"<h2 style='color:#856404;margin:0;'>Reopened</h2>"
            f"<h1 style='font-size:60px;margin:0;color:#000;'>{reopened_count}</h1></div>",
            unsafe_allow_html=True
        )
        col3.markdown(
            f"<div style='background-color:#d4edda;padding:20px;border-radius:15px;text-align:center;'>"
            f"<h2 style='color:#155724;margin:0;'>Closed</h2>"
            f"<h1 style='font-size:60px;margin:0;color:#000;'>{closed_count}</h1></div>",
            unsafe_allow_html=True
        )

        st.markdown("---")

        def render_ticket_section(title, query, bg, color, show_actions=True):
            df = pd.read_sql_query(query, conn)
            st.subheader(title)
            if df.empty:
                st.info("No tickets here.")
                return

            for _, row in df.iterrows():
                ticket_id = row["id"]
                uname = row["name"]
                email = row["email"]
                subject = row["subject"]
                desc = row["description"]
                status = row["status"]
                created = row["created_at"]
                updated = row["updated_at"]
                comments = row.get("comments", "")

                header_col1, header_col2, header_col3 = st.columns([0.7, 0.15, 0.15])
                with header_col1:
                    exp = st.expander(f"{uname} : {subject} ({status})", expanded=False)
                with header_col2:
                    if show_actions and st.button("✅ Resolve", key=f"res_{ticket_id}"):
                        c.execute("UPDATE tickets SET status='Resolved', updated_at=? WHERE id=?",
                                  (datetime.datetime.now(), ticket_id))
                        conn.commit()
                        st.rerun()
                with header_col3:
                    if show_actions and st.button("🗑️ Discard", key=f"dis_{ticket_id}"):
                        c.execute("UPDATE tickets SET status='Discarded', updated_at=? WHERE id=?",
                                  (datetime.datetime.now(), ticket_id))
                        conn.commit()
                        st.rerun()

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

                    if comments:
                        st.markdown("**Conversation Log:**")
                        for line in comments.strip().splitlines():
                            if "Admin:" in line:
                                st.markdown(f"<div style='color:green;'><b>{line}</b></div>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div style='color:black;'>{line}</div>", unsafe_allow_html=True)

                    if show_actions:
                        new_comment = st.text_area(f"Add Comment (#{ticket_id})", key=f"comment_{ticket_id}")
                        if st.button(f"Reply to #{ticket_id}", key=f"reply_{ticket_id}"):
                            if new_comment.strip():
                                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                                appended = (comments or "") + f"[{timestamp}] Admin: {new_comment.strip()}\n"
                                c.execute("""
                                    UPDATE tickets SET comments=?, updated_at=? WHERE id=?
                                """, (appended, datetime.datetime.now(), ticket_id))
                                conn.commit()
                                st.rerun()

        render_ticket_section("Open Tickets",
                              "SELECT * FROM tickets WHERE status='Open' ORDER BY id DESC",
                              "#d1ecf1", "#0c5460", True)
        render_ticket_section("Reopened Tickets",
                              "SELECT * FROM tickets WHERE status='Reopened' ORDER BY id DESC",
                              "#fff3cd", "#856404", True)
        render_ticket_section("Resolved / Discarded Tickets",
                              "SELECT * FROM tickets WHERE status IN ('Resolved','Discarded') ORDER BY id DESC",
                              "#d4edda", "#155724", False)

elif st.session_state.get("authentication_status") is False:
    st.error("Username/password is incorrect.")
else:
    st.warning("Please log in to continue.")
