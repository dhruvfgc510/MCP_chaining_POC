# app.py - Streamlit frontend for the simple login system
# Fixes applied per CodeSherlock analysis:
# - Dependency Injection: uses AuthService instance (injectable)
# - Exception Handling: try/except around all backend calls
# - Input Validation: strip whitespace from username before use
# - Monitoring & Logging: logging for UI-level events
# Run with: streamlit run app.py

import logging
import streamlit as st
from login import AuthService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Login System", page_icon="🔐")
st.title("🔐 Simple Login System")

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "auth_service" not in st.session_state:
    # Single shared AuthService instance stored in session state
    st.session_state.auth_service = AuthService()


def logout():
    """Clear session state on logout."""
    st.session_state.logged_in = False
    st.session_state.current_user = None


def run_app(auth_service: AuthService = None):
    """Main app logic. Accepts an injected auth_service for testability."""
    svc = auth_service or st.session_state.auth_service

    # --- Logged-in view ---
    if st.session_state.logged_in:
        username = st.session_state.current_user
        st.success(f"Logged in as: {username}")

        try:
            info = svc.get_user_info(username)
        except Exception:
            logger.exception("app: failed to get user info for username=%r", username)
            info = None
            st.info("Account information is currently unavailable.")

        if info:
            st.info(f"Account created at: {info['created_at']}")

        st.button("Logout", on_click=logout)
        return

    # --- Auth view (Login / Register) ---
    mode = st.radio("Select action:", ["Login", "Register"], horizontal=True)
    st.divider()

    raw_username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    # Trim whitespace for immediate UX feedback
    username = raw_username.strip() if raw_username else ""

    # --- Register ---
    if mode == "Register":
        if st.button("Register"):
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                try:
                    success, message = svc.register(username, password)
                except Exception:
                    logger.exception("app: unexpected error during register for username=%r", username)
                    st.error("An unexpected error occurred while registering. Please try again later.")
                else:
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

    # --- Login ---
    elif mode == "Login":
        if st.button("Login"):
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                try:
                    success, message = svc.authenticate(username, password)
                except Exception:
                    logger.exception("app: unexpected error during login for username=%r", username)
                    st.error("An unexpected error occurred during login. Please try again later.")
                else:
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.current_user = username
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

                        # Show account status details
                        try:
                            info = svc.get_user_info(username)
                        except Exception:
                            logger.exception("app: failed to get user info after failed login for username=%r", username)
                            st.info("Unable to retrieve account status at this time.")
                        else:
                            if info:
                                if info["locked"]:
                                    st.warning("This account is locked.")
                                else:
                                    st.warning(
                                        f"Failed attempts: {info['failed_attempts']} / {svc.max_failed_attempts}"
                                    )


run_app()
