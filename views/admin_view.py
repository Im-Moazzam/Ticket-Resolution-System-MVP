import streamlit as st
import pandas as pd
import datetime


def admin_view(conn, c):
    st.title("Admin Dashboard")

    open_count = c.execute(
        "SELECT COUNT(*) FROM tickets WHERE status='Open'"
    ).fetchone()[0]
    reopened_count = c.execute(
        "SELECT COUNT(*) FROM tickets WHERE status='Reopened'"
    ).fetchone()[0]
    closed_count = c.execute(
        "SELECT COUNT(*) FROM tickets WHERE status IN ('Resolved', 'Discarded')"
    ).fetchone()[0]

    col1, col2, col3 = st.columns(3)
    col1.markdown(
        f"<div style='background-color:#d1ecf1;padding:20px;border-radius:15px;text-align:center;'>"
        f"<h2 style='color:#0c5460;margin:0;'>Open</h2>"
        f"<h1 style='font-size:60px;margin:0;color:#000;'>{open_count}</h1></div>",
        unsafe_allow_html=True,
    )
    col2.markdown(
        f"<div style='background-color:#fff3cd;padding:20px;border-radius:15px;text-align:center;'>"
        f"<h2 style='color:#856404;margin:0;'>Reopened</h2>"
        f"<h1 style='font-size:60px;margin:0;color:#000;'>{reopened_count}</h1></div>",
        unsafe_allow_html=True,
    )
    col3.markdown(
        f"<div style='background-color:#d4edda;padding:20px;border-radius:15px;text-align:center;'>"
        f"<h2 style='color:#155724;margin:0;'>Resolved</h2>"
        f"<h1 style='font-size:60px;margin:0;color:#000;'>{closed_count}</h1></div>",
        unsafe_allow_html=True,
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

            colT, colB = st.columns([6, 2])
            with colT:
                exp = st.expander(f"{uname} : {subject} ({status})", expanded=False)
            with colB:
                if show_actions:
                    col_res, col_dis = st.columns(2)
                    with col_res:
                        if st.button("✅", key=f"res_{ticket_id}"):
                            with conn:
                                c.execute(
                                    "UPDATE tickets SET status='Resolved', updated_at=? WHERE id=?",
                                    (datetime.datetime.now(), ticket_id),
                                )
                            st.rerun()
                    with col_dis:
                        if st.button("🗑️", key=f"dis_{ticket_id}"):
                            with conn:
                                c.execute(
                                    "UPDATE tickets SET status='Discarded', updated_at=? WHERE id=?",
                                    (datetime.datetime.now(), ticket_id),
                                )
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
                    unsafe_allow_html=True,
                )

                if comments:
                    st.markdown("**Conversation Log:**")
                    for line in comments.strip().splitlines():
                        if "Admin:" in line:
                            st.markdown(
                                f"""
                                <div style='background-color:#e6ffe6;padding:8px 12px;border-radius:10px;
                                            margin:5px 0;text-align:right;color:#155724;font-weight:500;'>
                                    {line}
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                f"""
                                <div style='background-color:#f1f1f1;padding:8px 12px;border-radius:10px;
                                            margin:5px 0;text-align:left;color:#000;'>
                                    {line}
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                new_comment = st.text_input(
                    "Reply to user", key=f"comment_{ticket_id}"
                )
                if st.button("💬 Send Reply", key=f"reply_{ticket_id}"):
                    if new_comment.strip():
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
                        appended = (
                            comments or ""
                        ) + f"[{timestamp}] Admin: {new_comment.strip()}\n"
                        with conn:
                            c.execute(
                                "UPDATE tickets SET comments=?, updated_at=? WHERE id=?",
                                (appended, datetime.datetime.now(), ticket_id),
                            )
                        st.rerun()

    render_ticket_section(
        "Open Tickets",
        "SELECT * FROM tickets WHERE status='Open' ORDER BY id DESC",
        "#d1ecf1",
        "#0c5460",
        True,
    )
    render_ticket_section(
        "Reopened Tickets",
        "SELECT * FROM tickets WHERE status='Reopened' ORDER BY id DESC",
        "#fff3cd",
        "#856404",
        True,
    )
    render_ticket_section(
        "Resolved Tickets",
        "SELECT * FROM tickets WHERE status='Resolved' ORDER BY id DESC",
        "#d4edda",
        "#155724",
        False,
    )
    render_ticket_section(
        "Discarded Tickets",
        "SELECT * FROM tickets WHERE status='Discarded' ORDER BY id DESC",
        "#f8d7da",
        "#721c24",
        False,
    )
