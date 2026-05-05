import streamlit as st
from db_connection import get_user_by_username

def add_church_styling():
    background_image_url = "https://png.pngtree.com/thumb_back/fh260/background/20221114/pngtree-cross-on-mountain-vector-church-image_1462431.jpg"
    
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("{background_image_url}");
            background-attachment: fixed;
            background-size: cover;
            background-position: center;
        }}
        .block-container {{
            background-color: rgba(255, 255, 255, 0.90);
            padding: 3rem;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-top: 2rem;
            max-width: 800px;
        }}
        .block-container h1, .block-container h2, .block-container h3, 
        .block-container p, .block-container label, .block-container span {{
            color: #2c3e50 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def initialize_auth_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
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
                st.session_state.logged_in = True
                st.session_state.current_user = user["Username"]
                st.session_state.current_user_name = user["FullName"]
                st.session_state.role = user.get("Role", "Admin") 
                
                st.success(f"Welcome back, {user['FullName']}!")
                st.rerun()
            else:
                st.error("Invalid username or password. Please contact the Administrator if you have forgotten your credentials.")