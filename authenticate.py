import streamlit as st
from settings import check_password

def login_function():
    with st.form("Student login"):
        username = st.text_input("Enter Username:", max_chars=20)
        password = st.text_input("Enter Password:", type="password", max_chars=16)
        submit_button = st.form_submit_button("Login")
         # On submit, check if new passwords match and then update the password.
        if submit_button:
            if st.session_state.api_key == False:
                st.error("Please enter a valid OpenAI API key")
                return False
            if check_password(username, password):
                return True
            else:
                st.error("Username and Password is incorrect")
                return False
    pass