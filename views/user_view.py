import streamlit as st
import datetime
import pandas as pd


def user_view(name, conn, c):
    st.title("Submit a Ticket")
    if "subject" not in st.session_state:
        st.session_state["subject"] = ""
    if "description" not in st.session_state:
        st.session_state["description"] = ""
    if "email" not in st.session_state:
        st.session_state["email"] = ""

    with st.form("ticket_form"):
        subject = st.text_input("Subject", value=st.session_state["subject"])
        description = st.text_area("Description", value=st.session_state["description"])
        email = st.text_input("Your Email", value=st.session_state["email"])
        submitted = st.form_submit_button("Submit Ticket")

        if submitted:
            if not subject.strip() or not description.strip() or not email.strip():
                st.error("Please fill in all fields.")
            else:
                c.execute(
                    """
                    SELECT COUNT(*) FROM tickets 
                    WHERE name=? AND subject=? AND description=? AND status='Open'
                """,
                    (name, subject.strip(), description.strip()),
                )
                if c.fetchone()[0] > 0:
                    st.warning("You already submitted this ticket.")
                else:
                    c.execute(
                        """
                        INSERT INTO tickets (name, email, subject, description, status, created_at, updated_at, comments)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            name,
                            email.strip(),
                            subject.strip(),
                            description.strip(),
                            "Open",
                            datetime.datetime.now(),
                            datetime.datetime.now(),
                            "",
                        ),
                    )
                    conn.commit()
                    st.success("Ticket submitted successfully.")
                    st.session_state["subject"] = ""
                    st.session_state["description"] = ""
                    st.session_state["email"] = ""
                    st.rerun()

    st.header("Your Tickets")
    user_tickets = pd.read_sql_query(
        "SELECT id, subject, status, created_at, comments FROM tickets WHERE name=? ORDER BY id DESC",
        conn,
        params=(name,),
    )

    if not user_tickets.empty:
        latest_admin_replies = []
        for _, row in user_tickets.iterrows():
            comments = (row["comments"] or "").strip().splitlines()
            latest_admin_comment = "-"
            for line in reversed(comments):
                if "Admin:" in line:
                    latest_admin_comment = line.replace("Admin:", "").strip()
                    break
            latest_admin_replies.append(latest_admin_comment)
        user_tickets["Latest Admin Reply"] = latest_admin_replies
        user_tickets_display = user_tickets[
            ["id", "subject", "status", "created_at", "Latest Admin Reply"]
        ]
        st.dataframe(user_tickets_display, width="stretch")
    else:
        st.info("You haven't submitted any tickets yet.")

    st.markdown("---")
    st.subheader("Reopen a Ticket")

    with st.form("reopen_form"):
        reopen_id = st.number_input("Enter Ticket ID to Reopen", min_value=1, step=1)
        comment = st.text_area("Enter your comment or explanation")
        reopen_submit = st.form_submit_button("Reopen Ticket")

        if reopen_submit:
            ticket = c.execute(
                "SELECT id, comments, status FROM tickets WHERE id=? AND name=?",
                (reopen_id, name),
            ).fetchone()
            if not ticket:
                st.error("Ticket not found or not owned by you.")
            elif ticket[2] in ("Open", "Reopened"):
                st.warning("This ticket is already active.")
            else:
                prev_comments = ticket[1] or ""
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                new_comment = f"[{timestamp}] {name}: {comment.strip()}\n"
                updated_comments = prev_comments + new_comment
                c.execute(
                    """
                    UPDATE tickets SET status='Reopened', comments=?, updated_at=? WHERE id=?
                """,
                    (updated_comments, datetime.datetime.now(), reopen_id),
                )
                conn.commit()
                st.success("Ticket reopened successfully.")
                st.session_state["subject"] = ""
                st.session_state["description"] = ""
                st.session_state["email"] = ""
                st.rerun()
