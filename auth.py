import streamlit as st
from db_connection import get_user_by_username, setup_new_user_credentials

def add_church_styling():
    st.markdown(
        """
        <style>
        /* Professional deep blue/slate gradient background */
        .stApp {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            background-attachment: fixed;
        }
        .block-container {
            background-color: rgba(255, 255, 255, 0.95);
            padding: 3rem;
            border-radius: 15px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
            margin-top: 2rem;
            max-width: 800px;
        }
        .block-container h1, .block-container h2, .block-container h3, 
        .block-container p, .block-container label, .block-container span {
            color: #2c3e50 !important;
        }
        /* Style the submit buttons to match the professional theme */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #1e3c72;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 0.5rem 1rem;
            font-weight: bold;
        }
        div[data-testid="stFormSubmitButton"] > button:hover {
            background-color: #2a5298;
            color: white;
            border: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def initialize_auth_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "needs_setup" not in st.session_state: # NEW
        st.session_state.needs_setup = False
    if "setup_user_data" not in st.session_state: # NEW
        st.session_state.setup_user_data = None
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "current_user_name" not in st.session_state:
        st.session_state.current_user_name = None
    if "role" not in st.session_state:         
        st.session_state.role = None
    if "users" not in st.session_state:
        st.session_state.users = {}

def show_auth_screen():
    add_church_styling()
    st.title("Church Attendance Monitoring System (CAMS)")
    st.markdown("Welcome! Please log in to access the system.")

    with st.form("login_form", clear_on_submit=False):
        st.subheader("System Login")
        login_username = st.text_input("Username")
        login_password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Log In", use_container_width=True)

        if login_btn:
            user = get_user_by_username(login_username)

            if user and user["PasswordHash"] == login_password:
                # --- NEW LOGIC: Check for AdminCreated flag ---
                if user.get("SecurityAnswer") == "AdminCreated":
                    st.session_state.needs_setup = True
                    st.session_state.setup_user_data = user  # Store user data temporarily
                    st.warning("First time setup required. Redirecting...")
                    st.rerun()
                else:
                    # Standard Login
                    st.session_state.logged_in = True
                    st.session_state.current_user = user["Username"]
                    st.session_state.current_user_name = user["FullName"]
                    st.session_state.role = user.get("Role", "Admin") 
                    
                    st.success(f"Welcome back, {user['FullName']}!")
                    st.rerun()
            else:
                st.error("Invalid username or password. Please contact the Administrator if you have forgotten your credentials.")

# --- NEW FUNCTION: First Time Setup Screen ---
def show_first_time_setup():
    add_church_styling()
    st.title("Complete Your Account Setup")
    st.warning("Since this is your first time logging in, you must update your temporary password and set a security question to secure your account.")
    
    user_data = st.session_state.get("setup_user_data", {})
    username = user_data.get("Username")

    with st.form("setup_form"):
        st.subheader("1. Change Your Password")
        new_pw = st.text_input("New Permanent Password", type="password")
        confirm_pw = st.text_input("Confirm New Password", type="password")
        
        st.divider()
        st.subheader("2. Set Account Recovery")
        new_question = st.selectbox("Select a Security Question", [
            "What is the title of your favorite Hymn or Worship song?",
            "In what city did your parents meet?",
            "What was the name of your first pet?",
            "What is your mother's maiden name?",
            "What high school did you attend?"
        ])
        new_answer = st.text_input("Your Secret Answer", type="password")
        
        submit_setup = st.form_submit_button("Save & Continue", use_container_width=True)
        
        if submit_setup:
            if new_pw != confirm_pw:
                st.error("Passwords do not match!")
            elif len(new_pw) < 6:
                st.error("Password must be at least 6 characters long.")
            elif not new_answer:
                st.error("Please provide an answer to the security question.")
            else:
                # Update DB via db_connection
                if setup_new_user_credentials(username, new_pw, new_question, new_answer):
                    st.success("Account secured successfully! Logging you in...")
                    
                    # Grant full access
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.session_state.current_user_name = user_data.get("FullName")
                    st.session_state.role = user_data.get("Role", "Admin")
                    
                    st.session_state.needs_setup = False
                    st.session_state.setup_user_data = None
                    
                    st.rerun()
                else:
                    st.error("Database error. Could not update credentials.")