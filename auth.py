import streamlit as st
from db_connection import get_user_by_username, create_user, get_user_by_email, update_password_by_email

SECURITY_QUESTIONS = [
    "What is the title of your favorite Hymn or Worship song?",
    "What is your favorite Bible verse (e.g., John 8:32)?",
    "In what city or town were you born?",
    "What is the name of the first parish or church you ever attended?",
    "What is the name of the chapel where you usually pray?"
]

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
        .stTabs [data-baseweb="tab-list"] {{
            gap: 20px;
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
    if "role" not in st.session_state:         # NEW: Added Role initialization
        st.session_state.role = None
    if "users" not in st.session_state:
        st.session_state.users = {}
    if "reset_email_verified" not in st.session_state:
        st.session_state.reset_email_verified = False
    if "verified_email" not in st.session_state:
        st.session_state.verified_email = None
    if "security_answer_verified" not in st.session_state:
        st.session_state.security_answer_verified = False
    if "user_security_question" not in st.session_state:
        st.session_state.user_security_question = None
    if "user_security_answer" not in st.session_state:
        st.session_state.user_security_answer = None

def show_auth_screen():
    add_church_styling()
    st.title("Church Attendance Monitoring System (CAMS)")
    st.markdown("Welcome! Please log in, create an account, or recover your password below.")

    tab1, tab2, tab3 = st.tabs(["Log In", "Create Account", "Forgot Password"])

    with tab1:
        with st.form("login_form", clear_on_submit=False):
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
                    st.error("Invalid username or password.")

    with tab2:
        with st.form("create_account_form", clear_on_submit=True):
            full_name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            new_username = st.text_input("Create Username")
            new_password = st.text_input("Create Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            st.markdown("### Security Question")
            st.markdown("This will be used to recover your account if you forget your password.")
            sec_question = st.selectbox("Select a Security Question", SECURITY_QUESTIONS)
            sec_answer = st.text_input("Your Answer", type="password") 

            create_btn = st.form_submit_button("Create Account", use_container_width=True)

            if create_btn:
                if not full_name or not email or not new_username or not new_password or not confirm_password or not sec_answer:
                    st.warning("Please complete all fields.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    success, message = create_user(
                        full_name=full_name, email=email, username=new_username,
                        password=new_password, security_question=sec_question, security_answer=sec_answer
                    )
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

    with tab3:
        if not st.session_state.reset_email_verified:
            with st.form("forgot_password_form", clear_on_submit=True):
                st.markdown("Enter your registered email address to recover your account.")
                reset_email = st.text_input("Email Address")
                verify_btn = st.form_submit_button("Find Account", use_container_width=True)

                if verify_btn:
                    if not reset_email:
                        st.warning("Please enter your email address.")
                    else:
                        user = get_user_by_email(reset_email)
                        if user:
                            st.session_state.reset_email_verified = True
                            st.session_state.verified_email = reset_email
                            st.session_state.user_security_question = user.get("SecurityQuestion", "Question not found.")
                            st.session_state.user_security_answer = user.get("SecurityAnswer", "")
                            st.success("Account found!")
                            st.rerun()
                        else:
                            st.error("No active account found with that email address.")
                            
        elif not st.session_state.security_answer_verified:
            with st.form("security_question_form", clear_on_submit=True):
                st.markdown(f"Account found for: **{st.session_state.verified_email}**")
                st.markdown(f"### Security Question: \n**{st.session_state.user_security_question}**")
                
                answer_attempt = st.text_input("Answer")
                col1, col2 = st.columns(2)
                with col1:
                    verify_ans_btn = st.form_submit_button("Submit Answer", use_container_width=True)
                with col2:
                    cancel_ans_btn = st.form_submit_button("Cancel", use_container_width=True)

                if cancel_ans_btn:
                    st.session_state.reset_email_verified = False
                    st.session_state.verified_email = None
                    st.session_state.user_security_question = None
                    st.session_state.user_security_answer = None
                    st.rerun()

                if verify_ans_btn:
                    if not answer_attempt:
                        st.warning("Please provide an answer.")
                    elif answer_attempt.strip().lower() == st.session_state.user_security_answer.strip().lower():
                        st.session_state.security_answer_verified = True
                        st.success("Answer correct! Proceed to reset password.")
                        st.rerun()
                    else:
                        st.error("Incorrect answer. Please try again.")
        else:
            with st.form("new_password_form", clear_on_submit=True):
                st.markdown(f"Create a new password for **{st.session_state.verified_email}**")
                new_pw = st.text_input("New Password", type="password")
                confirm_new_pw = st.text_input("Confirm New Password", type="password")
                
                col1, col2 = st.columns(2)
                with col1:
                    update_btn = st.form_submit_button("Update Password", use_container_width=True)
                with col2:
                    cancel_btn = st.form_submit_button("Cancel", use_container_width=True)

                if cancel_btn:
                    st.session_state.reset_email_verified = False
                    st.session_state.security_answer_verified = False
                    st.session_state.verified_email = None
                    st.session_state.user_security_question = None
                    st.session_state.user_security_answer = None
                    st.rerun()

                if update_btn:
                    if not new_pw or not confirm_new_pw:
                        st.warning("Please fill out all fields.")
                    elif new_pw != confirm_new_pw:
                        st.error("Passwords do not match.")
                    else:
                        success = update_password_by_email(st.session_state.verified_email, new_pw)
                        if success:
                            st.success("Password updated successfully! You can now log in via the 'Log In' tab.")
                            st.session_state.reset_email_verified = False
                            st.session_state.security_answer_verified = False
                            st.session_state.verified_email = None
                            st.session_state.user_security_question = None
                            st.session_state.user_security_answer = None
                        else:
                            st.error("Database error: Could not update password.")