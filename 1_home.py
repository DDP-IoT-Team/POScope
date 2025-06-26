import streamlit as st
from PIL import Image


#-----------------------------------------Settings-----------------------------------------

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


#-----------------------------------------Contents-----------------------------------------

# App name and logo
logo = Image.open("static/logo.png")
st.image(logo)

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
             - [https://example.com](https://example.com)
            """
        )
# Feature requests
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

# Known issues
with st.container(border=True):
    st.write("##### :material/bug_report: Known Issues")
    st.markdown(
        """
         - 期間が連続していないPOSデータ（4月分と6月分など）をアップロードした際に、min_dateとmax_dateの間に
         含まれる、存在しない日付が選択された際の挙動
         - データ可視化のセクションにて、夜営業 + 東カフェテリアでのエラー
         - 夜学食の客数が、客数供給高のデータと比べて妙に少ない（処理はミスってない）
        """
    )

# space
st.text("")

# Future implementations
with st.container(border=True):
    st.write("##### :material/event_upcoming: Future Implementations")
    st.markdown(
        """
         - データの日本語化
         - サンプルデータの追加（カレンダーデータはアプリ内に組み込む？）
         - 効果測定の機能
        """
    )

