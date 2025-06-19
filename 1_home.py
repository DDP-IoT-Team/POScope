import streamlit as st
from PIL import Image


#-----------------------------------------Settings-----------------------------------------

#favicon = Image.open("static/favicon.ico")
favicon = Image.open("static/favicon.ico")

st.set_page_config(
    page_title="ホーム", 
    layout="centered",
    initial_sidebar_state="expanded", 
    page_icon=favicon, 
    menu_items={
        'Get help': "https://www.example.com/help", # This will be replaced with GitHub Pages URL
        'Report a bug': "https://forms.gle/ARs9Md4jqjHxJwAW9", # Google Forms
        'About': "#### POScope \nv1.0.0"
    }
)


#-----------------------------------------Functions-----------------------------------------


#-----------------------------------------Contents-----------------------------------------

st.logo(favicon, 
        size="large", 
        link=None, 
        icon_image=favicon)

col1, col2 = st.columns(spec=[0.2, 0.8], vertical_alignment="top")
with col1:
    st.image(favicon, use_container_width=True)
with col2:
    st.write("# POScope")
    st.write("###### POS × Scope × Co-op")

st.header("ホーム")

with st.container(border=True):
    st.write("##### :material/notifications: おしらせ")
    st.markdown(
        """
         - おしらせはまだありません。
        """
    )

# space
st.text("")

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.write("##### :material/menu_book: アプリの使い方について")
        st.markdown(
            """
             - [https://example.com](https://example.com)
            """
        )
with col2:
    with st.container(border=True):
        st.write("##### :material/lightbulb: 機能改善の要望")
        st.markdown(
            """
             - https://example.com/feature-request
            """
        )

# space
st.text("")

with st.container(border=True):
    st.write("##### :material/bug_report: Known Issues")
    st.markdown(
        """
         - 期間が連続していないPOSデータ（4月分と6月分など）をアップロードした際に、min_dateとmax_dateの間に
         含まれる、存在しない日付が選択された際の挙動
        """
    )

