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
#客数と商品(合計提供数量)の提供数量の予測数値を提供
#線形回帰がベースで、リッジ・ラッソ回帰もできたらいいな
#resampleメソッドを使うとよい

#-----------------------------------------Contents-----------------------------------------

st.logo(favicon, size="large")

st.subheader("客数予測")

if "df_customers" in st.session_state:
    st.write("#### df_customers")
    st.session_state["df_customers"]
if "df_items" in st.session_state:
    st.write("#### df_items")
    st.session_state["df_items"]
if "df_syllabus_west" in st.session_state:
    st.write("#### df_syllabus_west")
    st.session_state["df_syllabus_west"]
if "df_syllabus_east" in st.session_state:
    st.write("#### df_syllabus_east")
    st.session_state["df_syllabus_east"]
if "df_calendar" in st.session_state:
    st.write("#### df_calendar")
    st.session_state["df_calendar"]

