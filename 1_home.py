import streamlit as st
from PIL import Image


#-----------------------------------------Settings-----------------------------------------

# Load an image
favicon = Image.open("static/favicon.ico")
logo = Image.open("static/logo.png")

# Page configuration
st.set_page_config(
    page_title="ホーム", 
    layout="centered",
    initial_sidebar_state="expanded", 
    page_icon=favicon, 
    menu_items={
        'Get help': "https://ddp-iot-team.github.io/POScope/", # Documentation
        'Report a bug': st.secrets["google_forms"]["report_a_bug"], # Google Forms
        'About': "#### POScope \nv1.0.0"
    }
)


#-----------------------------------------Contents-----------------------------------------

# App name and logo
st.image(logo)

# Logo in the sidebar
st.logo(
    favicon, 
    size="large", 
    link=None, 
    icon_image=favicon
)

st.header("ホーム")

# notifications
with st.container(border=True):
    st.write("##### :material/notifications: おしらせ")
    st.markdown(
        """
         - おしらせはまだありません。
        """
    )

# space
st.text("")

# Links
col1, col2 = st.columns(2)
# Documentation
with col1:
    with st.container(border=True):
        st.write("##### :material/menu_book: アプリの使い方について")
        st.markdown(
            """
             - [https://ddp-iot-team.github.io/POScope/](https://ddp-iot-team.github.io/POScope/)
            """
        )
# Feature requests
with col2:
    with st.container(border=True):
        st.write("##### :material/lightbulb: 機能改善の要望")
        st.markdown(
            f"""
             - {st.secrets["google_forms"]["feature_request"]}
            """
        )

# space
st.text("")

# Links
col1, col2 = st.columns(2)
# Report a bug
with col1:
    with st.container(border=True):
        st.write("##### :material/bug_report: バグ報告")
        st.markdown(
            f"""
             - {st.secrets["google_forms"]["report_a_bug"]}
            """
        )
# Hamburger on island
with col2:
    with st.container(border=True):
        hamburger = Image.open("static/hamburger_on_island.png")
        st.image(hamburger)

