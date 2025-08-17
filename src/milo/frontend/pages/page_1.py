import streamlit as st
import yaml

st.set_page_config(page_title="Page 1")
st.title("Page 1")


if st.session_state.get("authentication_status"):
    authenticator = st.session_state.get("authenticator")
    authenticator.logout(location="sidebar", key="logout-milo-page-1")
    authenticator.login(location="unrendered", key="authenticator-page-1")
    # Put the main code and logic for your page here.
    st.success("You are logged in!")

elif st.session_state == {} or st.session_state["authentication_status"] is None:
    st.warning("Please use the button below to navigate to Home and log in.")
    st.page_link("Home.py", label="Home")
    st.stop()
