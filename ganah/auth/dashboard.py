"""Streamlit auth management dashboard — consolidated from ngen26 auth_page.py variants.

Supports both Shoonya (Windows Task Scheduler / xvfb-run) and Flattrade OAuth.
"""

import os
import sys

import streamlit as st
import pandas as pd

from ..db import get_all_credentials, update_credentials

_AUTH_DIR = os.path.dirname(os.path.abspath(__file__))
_API_KEY = "1e5e979458524cf2810943c542f91a5e"
_AUTH_URL = f"https://auth.flattrade.in/?app_key={_API_KEY}"


def show():
    st.title("🔐 Broker Authentication")

    # ── Flattrade OAuth ──
    st.subheader("Flattrade OAuth")
    st.caption("Refresh session token for live trading")
    st.markdown(f"**Auth URL:** [{_AUTH_URL}]({_AUTH_URL})")
    st.markdown("1. Click the link → login with UCC + Password + TOTP")
    st.markdown("2. Redirected to `krisha.cloud` — token stored in DB")

    try:
        import duckdb
        db_path = os.path.join(_AUTH_DIR, "auth.duckdb")
        con = duckdb.connect(db_path, read_only=True)
        row = con.execute(
            "SELECT sessionkey, updateddatetime FROM authsession "
            "WHERE brokername='FLATTRADE' AND username='FZ09213'"
        ).fetchone()
        con.close()
        if row and row[0]:
            st.markdown(f"✅ **Active** — last refresh: `{row[1] or 'unknown'}` IST")
        else:
            st.warning("No active Flattrade session.")
    except Exception as e:
        st.info(f"Status unavailable: {e}")

    st.link_button("🔐 Open Flattrade Auth", _AUTH_URL, type="primary", use_container_width=True)

    st.divider()

    # ── Shoonya / xvfb-run Instructions ──
    st.subheader("Shoonya Session")
    st.markdown("""
    **Session refresh** — runs `shoonya-fy26.py` via Selenium Chrome.

    **Local (Windows):** Run the script directly (launches Chrome).
    
    **VPS (Linux):** 
    ```bash
    cd /opt/pairt/ganah/ganah/auth
    xvfb-run python shoonya-fy26.py
    ```
    
    **Programmatic:**
    ```python
    from ganah import refresh_session
    success, msg = refresh_session("SHOONYA", "FA138862")
    ```
    """)

    st.divider()

    # ── Credentials Grid ──
    st.subheader("Credentials")

    df = get_all_credentials(db_path=os.path.join(_AUTH_DIR, "auth.duckdb"))
    if df.empty:
        st.info("No credentials found in auth.duckdb")
        return

    edited = st.data_editor(
        df,
        column_config={
            "id":              st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "brokername":      st.column_config.TextColumn("Broker", disabled=True, width="small"),
            "username":        st.column_config.TextColumn("Username", disabled=True),
            "pwd":             st.column_config.TextColumn("Password", width="medium"),
            "factor2":         st.column_config.TextColumn("TOTP Secret", width="medium"),
            "vc":              st.column_config.TextColumn("VC", disabled=True, width="small"),
            "apikey":          st.column_config.TextColumn("API Key", disabled=True, width="medium"),
            "secretkey":       st.column_config.TextColumn("Secret Key", disabled=True, width="medium"),
            "imei":            st.column_config.TextColumn("IMEI", disabled=True, width="small"),
            "has_session":     st.column_config.TextColumn("Session", disabled=True, width="small"),
            "updateddatetime": st.column_config.TextColumn("Updated", disabled=True),
        },
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="cred_editor"
    )

    if st.button("Save Changes", type="primary"):
        changes = 0
        for _, row in edited.iterrows():
            orig = df[df["id"] == row["id"]]
            if orig.empty:
                continue
            o = orig.iloc[0]
            pwd = row["pwd"] if row["pwd"] != o["pwd"] else None
            factor2 = row["factor2"] if row["factor2"] != o["factor2"] else None
            if pwd is not None or factor2 is not None:
                update_credentials(row["brokername"], row["username"],
                                   pwd=pwd, factor2=factor2,
                                   db_path=os.path.join(_AUTH_DIR, "auth.duckdb"))
                changes += 1
        if changes:
            st.success(f"{changes} row(s) updated")
            st.rerun()
        else:
            st.info("No changes detected")
