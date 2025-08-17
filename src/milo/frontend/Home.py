import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import LoginError
import yaml
from yaml.loader import SafeLoader

st.title("Streamlit-Authenticator")

# Load credentials from the YAML file
with open("src/milo/frontend/creds.yaml") as file:
    creds = yaml.load(file, Loader=SafeLoader)

# Initialize the authenticator
authenticator = stauth.Authenticate(
    creds["credentials"],
    creds["cookie"]["name"],
    creds["cookie"]["key"],
    creds["cookie"]["expiry_days"],
)

# Store the authenticator object in the session state
st.session_state["authenticator"] = authenticator
# Store the config in the session state so it can be updated later
st.session_state["config"] = creds


# Authentication logic
try:
    authenticator.login(location="main", key="login-milo-home")
except LoginError as e:
    st.error(e)

if st.session_state["authentication_status"]:
    authenticator.logout(location="sidebar", key="logout-milo-home")
    authenticator.login(location="unrendered", key="authenticator-home")
    st.write(f"Welcome {st.session_state['name']}")
    st.page_link("pages/page_1.py", label="Page 1")
elif st.session_state["authentication_status"] is False:
    st.error("Username/password is incorrect")
elif st.session_state["authentication_status"] is None:
    st.caption("Please enter your username and password")
