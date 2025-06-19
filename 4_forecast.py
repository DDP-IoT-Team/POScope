import streamlit as st
from PIL import Image
import pickle
import statsmodels.api as sm

#-----------------------------------------Settings-----------------------------------------

favicon = Image.open("static/favicon.ico")

st.set_page_config(
    page_title="予測", 
    layout="wide",
    initial_sidebar_state="expanded", 
    page_icon=favicon, 
    menu_items={
        'Get help': "https://www.example.com/help", # This will be replaced with GitHub Pages URL
        'Report a bug': "https://forms.gle/ARs9Md4jqjHxJwAW9", # Google Forms
        'About': "#### [App_name]"
    }
)


#-----------------------------------------Functions-----------------------------------------

#-----------------------------------------Contents-----------------------------------------

st.logo(favicon, size="large")

st.subheader("客数予測")



