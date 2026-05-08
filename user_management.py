import streamlit as st
import pandas as pd
from db_connection import get_all_users, toggle_user_status, admin_reset_password, create_user, get_user_logs 

def show_user_management_page():
    st.title("User Management Control Panel")
    st.markdown("Manage church staff accounts, system access, and security credentials.")

    users = get_all_users()
    df_users = pd.DataFrame(users) if users else pd.DataFrame()

    tab1, tab2, tab3, tab4 = st.tabs(["Manage Accounts", "Add New Staff", "Reset Passwords", "Login Logs"])

    with tab1:
        st.subheader("Current System Users")
        if not df_users.empty:
            # Display user table 
            display_df = df_users[["FullName", "Username", "Email", "Role", "IsActive"]].copy()
            display_df["Status"] = display_df["IsActive"].apply(lambda x: "🟢 Active" if x else "🔴 Inactive")
            st.dataframe(display_df.drop(columns=["IsActive"]), width='stretch')
            
            st.divider()
            st.subheader("Account Status Control")
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_user = st.selectbox("Select a username to modify:", df_users["Username"].tolist())
            
            # Check current status of selected user
            current_status = df_users.loc[df_users["Username"] == selected_user, "IsActive"].values[0]
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True) # alignment spacing
                if current_status == 1:
                    if st.button("Deactivate Account", type="primary", width='stretch'):
                        if toggle_user_status(selected_user, 0):
                            st.success(f"Account '{selected_user}' has been deactivated. They can no longer log in.")
                            st.rerun()
                        else:
                            st.error("Failed to update SSMS database.")
                else:
                    if st.button("Reactivate Account", width='stretch'):
                        if toggle_user_status(selected_user, 1):
                            st.success(f"Account '{selected_user}' is now active again.")
                            st.rerun()
        else:
            st.info("No users found in the database.")

    with tab2:
        st.subheader("Register New Staff Account")
        with st.form("admin_create_user_form", clear_on_submit=True):
            full_name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            new_username = st.text_input("Assign Username")
            new_password = st.text_input("Assign Temporary Password", type="password")
            
            st.markdown("*(Note: Security questions can be filled with defaults by the admin, and updated by the user later).*")
            sec_question = "What is the title of your favorite Hymn or Worship song?"
            sec_answer = st.text_input("Default Security Answer", value="AdminCreated")
            
            submit_btn = st.form_submit_button("Create Account")
            
            if submit_btn:
                if full_name and email and new_username and new_password:
                    # Uses the existing create_user function from db_connection
                    success, msg = create_user(full_name, email, new_username, new_password, sec_question, sec_answer)
                    if success:
                        st.success(f"Staff account for {full_name} created successfully!")
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill out all essential fields.")

    with tab3:
        st.subheader("Force Password Reset")
        st.warning("This will immediately overwrite the user's current password in the database.")
        if not df_users.empty:
            with st.form("admin_reset_password_form", clear_on_submit=True):
                user_to_reset = st.selectbox("Select User", df_users["Username"].tolist())
                new_pw = st.text_input("New Password", type="password")
                confirm_pw = st.text_input("Confirm New Password", type="password")
                
                reset_btn = st.form_submit_button("Update Password")
                
                if reset_btn:
                    if new_pw == confirm_pw and len(new_pw) > 0:
                        if admin_reset_password(user_to_reset, new_pw):
                            st.success(f"Password for '{user_to_reset}' has been successfully changed.")
                        else:
                            st.error("Database error occurred.")
                    else:
                        st.error("Passwords do not match or are empty.")

    with tab4:
        st.subheader("Staff Login History")
        st.caption("Click on a staff member's name to drop down and view their recent login activity.")
        
        if not df_users.empty:
            for index, row in df_users.iterrows():
                username = row["Username"]
                full_name = row["FullName"]
                
                with st.expander(f"View logs for {full_name} (@{username})"):
                    user_logs = get_user_logs(username) 
                    
                    if user_logs:
                        df_logs = pd.DataFrame(user_logs)
                        # Sorting so the most recent login is at the top
                        df_logs = df_logs.sort_values(by="LoginTime", ascending=False)
                        st.dataframe(df_logs, width='stretch', hide_index=True)
                    else:
                        st.info(f"No login records found for {username}.")
        else:
            st.info("No users found in the database.")