import streamlit as st
import pandas as pd
import datetime
from PIL import Image
import plotly.express as px


#-----------------------------------------Settings-----------------------------------------

favicon = Image.open("static/favicon.ico")

st.set_page_config(
    page_title="データ可視化", 
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

@st.cache_data
def convert_for_download(df: pd.DataFrame, index: bool) -> bytes:
    """
    Convert the DataFrame to a CSV format encoded in Shift-JIS for download.\\
    The `index` parameter determines whether to include the index in the CSV.\\
    The option of `encoding` in `to_csv()` is not supported when `path_or_buf` is `None`.
    """
    return df.to_csv(index=index).encode("shift-jis")


@st.cache_data
def process_cus1(df_cus: pd.DataFrame, date: tuple[datetime.date], time_span: str, business_hours: str, area: str):
    left_date = pd.Timestamp(date[0])
    right_date = pd.Timestamp(date[1]) + pd.Timedelta("1D")
    df_cus = df_cus[(left_date <= df_cus["開始日時"]) & (df_cus["開始日時"] < right_date)]
    df_cus = df_cus.query(f'アカウント名 == "{area}"')
    df_cus = df_cus.resample(time_span, on="開始日時")["客数"].sum()
    if business_hours == "昼（11:00～14:00）":
        df_cus = df_cus.between_time("11:00", "14:00")
    elif business_hours == "夜（17:30～19:30）":
        df_cus = df_cus.between_time("17:30", "19:30")
    else:
        df_cus = df_cus.between_time("11:00", "19:30")
    df_cus = df_cus.to_frame()
    df_cus["日付"] = df_cus.index.date
    df_cus["時間"] = df_cus.index.time
    df_cus = df_cus.set_index(["日付", "時間"])
    df_cus = df_cus.unstack(level=0)
    df_cus.index = list(map(lambda x: x.strftime("%H:%M"), df_cus.index))
    df_cus.columns = df_cus.columns.droplevel(0)
    #if date[0] != date[1]:
    #    df_cus["平均"] = df_cus.mean(axis="columns")
    return df_cus


@st.cache_data
def process_cus2(df_cus: pd.DataFrame, date: tuple[datetime.date], business_hours: str, area: str):
    left_date = pd.Timestamp(date[0])
    right_date = pd.Timestamp(date[1]) + pd.Timedelta("1D")
    df_cus = df_cus[(left_date <= df_cus["開始日時"]) & (df_cus["開始日時"] < right_date)]
    if area == "西食堂" or area == "東カフェテリア":
        df_cus = df_cus.query(f'アカウント名 == "{area}"')
    df_cus = df_cus.set_index("開始日時")
    if business_hours == "昼（11:00～14:00）":
        df_cus = df_cus.between_time("11:00", "14:00")
    elif business_hours == "夜（17:30～19:30）":
        df_cus = df_cus.between_time("17:30", "19:30")
    else:
        df_cus = df_cus.between_time("11:00", "19:30")
    df_cus = df_cus.reset_index(drop=False)
    df_cus = df_cus.groupby("アカウント名").resample("1D", on="開始日時")["客数"].sum()
    df_cus = df_cus.to_frame().unstack(level=0)
    df_cus.columns = df_cus.columns.droplevel(0)
    return df_cus


@st.cache_data
def filter_pm(df_cus: pd.DataFrame, date: tuple[datetime.date], business_hours: str, area: str) -> pd.DataFrame:
    """
    Filter the DataFrame and return a DataFrame for visualization of the ratio of payment methods.
    It does not exclude records with multiple payment methods, 
    so the sum of the total counts is not necessarily equal to the total number of customers.
    """
    left_date = pd.Timestamp(date[0])
    right_date = pd.Timestamp(date[1]) + pd.Timedelta("1D")
    df_cus = df_cus[(left_date <= df_cus["開始日時"]) & (df_cus["開始日時"] < right_date)]
    if area == "西食堂" or area == "東カフェテリア":
        df_cus = df_cus.query(f'アカウント名 == "{area}"')
    df_cus = df_cus.set_index("開始日時")
    if business_hours == "昼（11:00～14:00）":
        df_cus = df_cus.between_time("11:00", "14:00")
    elif business_hours == "夜（17:30～19:30）":
        df_cus = df_cus.between_time("17:30", "19:30")
    else:
        df_cus = df_cus.between_time("11:00", "19:30")
    df_cus = df_cus.reset_index(drop=False)
    pms = list(set(df_cus.columns) - set(["アカウント名", "会計ID", "開始日時", "会計日時", "金額", "客数"]))
    df_pm = df_cus[pms] * df_cus["客数"].values.reshape(-1, 1)
    df_pm = df_pm.sum(axis="index").to_frame(name="カウント").reset_index(names=["支払い方法"])
    return df_pm


@st.cache_data
def process_itm1(df_itm: pd.DataFrame, date: tuple[datetime.date], business_hours: str, area: str, aggregation: str, method: str, item: str):
    left_date = pd.Timestamp(date[0])
    right_date = pd.Timestamp(date[1]) + pd.Timedelta("1D")
    df_itm = df_itm[(left_date <= df_itm["開始日時"]) & (df_itm["開始日時"] < right_date)]
    if area == "西食堂" or area == "東カフェテリア":
        df_itm = df_itm.query(f'アカウント名 == "{area}"')
    if method == "名前":
        df_itm = df_itm[df_itm["名前"] == item]
    elif method == "バーコード":
        df_itm = df_itm[df_itm["バーコード"] == item]
    elif method == "SKU":
        df_itm = df_itm[df_itm["SKU"] == item]
    df_itm = df_itm.set_index("開始日時")
    if business_hours == "昼（11:00～14:00）":
        df_itm = df_itm.between_time("11:00", "14:00")
    elif business_hours == "夜（17:30～19:30）":
        df_itm = df_itm.between_time("17:30", "19:30")
    else:
        df_itm = df_itm.between_time("11:00", "19:30")
    df_itm = df_itm.reset_index(drop=False)
    df_itm = df_itm.groupby("アカウント名").resample("1D", on="開始日時")[aggregation].sum()
    df_itm = df_itm.to_frame().unstack(level=0)
    df_itm.columns = df_itm.columns.droplevel(0)
    return df_itm


@st.cache_data
def candidates_itm1(df_itm: pd.DataFrame, date: tuple[datetime.date], business_hours: str, area: str, method: str):
    left_date = pd.Timestamp(date[0])
    right_date = pd.Timestamp(date[1]) + pd.Timedelta("1D")
    df_itm = df_itm[(left_date <= df_itm["開始日時"]) & (df_itm["開始日時"] < right_date)]
    if area == "西食堂" or area == "東カフェテリア":
        df_itm = df_itm.query(f'アカウント名 == "{area}"')
    df_itm = df_itm.set_index("開始日時")
    if business_hours == "昼（11:00～14:00）":
        df_itm = df_itm.between_time("11:00", "14:00")
    elif business_hours == "夜（17:30～19:30）":
        df_itm = df_itm.between_time("17:30", "19:30")
    else:
        df_itm = df_itm.between_time("11:00", "19:30")
    df_itm = df_itm.reset_index(drop=False)
    if method == "名前":
        candidates = df_itm["名前"].unique().tolist()
    elif method == "バーコード":
        candidates = df_itm["バーコード"].unique().tolist()
    elif method == "SKU":
        candidates = df_itm["SKU"].unique().tolist()
    return candidates


@st.cache_data
def process_itm2(df_itm: pd.DataFrame, date: tuple[datetime.date], business_hours: str, area: str, aggregation: str, department: str):
    left_date = pd.Timestamp(date[0])
    right_date = pd.Timestamp(date[1]) + pd.Timedelta("1D")
    df_itm = df_itm[(left_date <= df_itm["開始日時"]) & (df_itm["開始日時"] < right_date)]
    if area == "西食堂" or area == "東カフェテリア":
        df_itm = df_itm.query(f'アカウント名 == "{area}"')
    df_itm = df_itm[df_itm["部門"] == department]
    df_itm = df_itm.set_index("開始日時")
    if business_hours == "昼（11:00～14:00）":
        df_itm = df_itm.between_time("11:00", "14:00")
    elif business_hours == "夜（17:30～19:30）":
        df_itm = df_itm.between_time("17:30", "19:30")
    else:
        df_itm = df_itm.between_time("11:00", "19:30")
    df_itm = df_itm.reset_index(drop=False)
    df_itm = df_itm.groupby("アカウント名").resample("1D", on="開始日時")[aggregation].sum()
    df_itm = df_itm.to_frame().unstack(level=0)
    df_itm.columns = df_itm.columns.droplevel(0)
    return df_itm


@st.cache_data
def candidates_itm2(df_itm: pd.DataFrame, date: tuple[datetime.date], business_hours: str, area: str):
    left_date = pd.Timestamp(date[0])
    right_date = pd.Timestamp(date[1]) + pd.Timedelta("1D")
    df_itm = df_itm[(left_date <= df_itm["開始日時"]) & (df_itm["開始日時"] < right_date)]
    if area == "西食堂" or area == "東カフェテリア":
        df_itm = df_itm.query(f'アカウント名 == "{area}"')
    df_itm = df_itm.set_index("開始日時")
    if business_hours == "昼（11:00～14:00）":
        df_itm = df_itm.between_time("11:00", "14:00")
    elif business_hours == "夜（17:30～19:30）":
        df_itm = df_itm.between_time("17:30", "19:30")
    else:
        df_itm = df_itm.between_time("11:00", "19:30")
    df_itm = df_itm.reset_index(drop=False)
    candidates = df_itm["部門"].unique().tolist()
    return candidates


#-----------------------------------------Contents-----------------------------------------

st.logo(favicon, size="large")

st.title("データの可視化")

# Check if the data has been uploaded
if "df_customers" not in st.session_state:
    st.error("データがアップロードされていません。最初のページでデータをアップロードしてください。")
    st.stop()

# Load the data from session state
df_cus: pd.DataFrame = st.session_state["df_customers"]
df_itm: pd.DataFrame = st.session_state["df_items"]

if st.session_state["west_pos"]:
    if st.session_state["east_pos"]:
        min_date = min(st.session_state["west_date_min"], 
                       st.session_state["east_date_min"])
        max_date = max(st.session_state["west_date_max"], 
                       st.session_state["east_date_max"])
    else:
        min_date = st.session_state["west_date_min"]
        max_date = st.session_state["west_date_max"]
else:
    min_date = st.session_state["east_date_min"]
    max_date = st.session_state["east_date_max"]

# visualization
st.subheader("客数の可視化", divider="gray")

# number of customers by time of day
with st.container(border=True):
    st.write("##### 1日の時間帯ごとの客数の推移")
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.date_input(
                label=":material/calendar_month: 日付", 
                value=(min_date, min_date), 
                min_value=min_date, 
                max_value=max_date, 
                key="date1"
            )
        with col2:
            st.selectbox(
                label=":material/timer: 集計スパン", 
                options=["5min", "10min", "30min"], 
                index=0, 
                accept_new_options=False, 
                key="time_span1"
            )
        with col3:
            st.selectbox(
                label=":material/schedule: 営業時間", 
                options=["昼（11:00～14:00）", "夜（17:30～19:30）", "昼・夜"], 
                index=0, 
                accept_new_options=False, 
                key="business_hours1"
            )
        with col4:
            st.selectbox(
                label=":material/storefront: 店舗", 
                options=["西食堂", "東カフェテリア"], 
                accept_new_options=False, 
                index=0, 
                key="area1"
            )
    with st.container(border=True):
        if len(st.session_state["date1"]) == 2:
            df_cust_time = process_cus1(df_cus, 
                                        st.session_state["date1"], 
                                        st.session_state["time_span1"],
                                        st.session_state["business_hours1"], 
                                        st.session_state["area1"])
            st.line_chart(data=df_cust_time) # st.line_chart() might be replaced with st.plotly_chart() for more customization
    with st.expander("データを見る", expanded=False):
        if len(st.session_state["date1"]) == 2:
            st.dataframe(df_cust_time)
            st.download_button(
                label=":material/download: `.csv`でダウンロード", 
                data=convert_for_download(df_cust_time, index=True), 
                file_name=f"customers_by_time_{st.session_state['date1'][0]}-{st.session_state['date1'][1]}.csv", 
                mime="text/csv"
            )

# space
st.write("")

# total number of customers per day
with st.container(border=True):
    st.write("##### 1日の合計客数の推移")
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.date_input(
                label=":material/calendar_month: 日付", 
                value=(min_date, max_date), 
                min_value=min_date, 
                max_value=max_date, 
                key="date2"
            )
        with col2:
            st.selectbox(
                label=":material/schedule: 営業時間", 
                options=["昼（11:00～14:00）", "夜（17:30～19:30）", "昼・夜"], 
                index=0, 
                accept_new_options=False, 
                key="business_hours2"
            )
        with col3:
            st.selectbox(
                label=":material/storefront: 店舗", 
                options=["西食堂", "東カフェテリア", "両方"], 
                accept_new_options=False, 
                index=0, 
                key="area2"
            )
    with st.container(border=True):
        if len(st.session_state["date2"]) == 2:
            df_cust_day = process_cus2(
                df_cus, 
                st.session_state["date2"], 
                st.session_state["business_hours2"], 
                st.session_state["area2"]
            )
            st.line_chart(data=df_cust_day) # st.line_chart() might be replaced with st.plotly_chart() for more customization
    with st.expander("データを見る", expanded=False):
        if len(st.session_state["date2"]) == 2:
            st.dataframe(df_cust_day)
            st.download_button(
                label=":material/download: `.csv`でダウンロード", 
                data=convert_for_download(df_cust_day, index=True), 
                file_name=f"customers_per_day_{st.session_state['date1'][0]}-{st.session_state['date1'][1]}.csv", 
                mime="text/csv"
            )
        
# space
st.write("")

# ratio of payment methods
with st.container(border=True):
    st.write("##### 支払い方法の割合")
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.date_input(
                label=":material/calendar_month: 日付", 
                value=(min_date, max_date), 
                min_value=min_date, 
                max_value=max_date, 
                key="date_pm"
            )
        with col2:
            st.selectbox(
                label=":material/schedule: 営業時間", 
                options=["昼（11:00～14:00）", "夜（17:30～19:30）", "昼・夜"], 
                index=0, 
                accept_new_options=False, 
                key="business_hours_pm"
            )
        with col3:
            st.selectbox(
                label=":material/storefront: 店舗", 
                options=["西食堂", "東カフェテリア", "両方"], 
                accept_new_options=False, 
                index=0, 
                key="area_pm"
            )
    with st.container(border=True):
        if len(st.session_state["date_pm"]) == 2:
            df_pm = filter_pm(
                df_cus, 
                st.session_state["date_pm"], 
                st.session_state["business_hours_pm"], 
                st.session_state["area_pm"]
            )
            fig = px.pie(
                df_pm, 
                names="支払い方法", 
                values="カウント"
            )
            st.plotly_chart(
                fig, 
                use_container_width=True
            )
    with st.expander("データを見る", expanded=False):
        if len(st.session_state["date_pm"]) == 2:
            st.dataframe(df_pm, hide_index=True)
            st.download_button(
                label=":material/download: `.csv`でダウンロード", 
                data=convert_for_download(df_pm, index=False), 
                file_name=f"payments_{st.session_state['date1'][0]}-{st.session_state['date1'][1]}.csv", 
                mime="text/csv"
            )

# space
st.write("")

st.subheader("売上の可視化", divider="gray")

# sales by item
with st.container(border=True):
    st.write("##### 各商品ごとの売上推移")
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.date_input(
                label=":material/calendar_month: 日付", 
                value=(min_date, max_date), 
                min_value=min_date, 
                max_value=max_date, 
                key="date3"
            )
        with col2:
            st.selectbox(
                label=":material/schedule: 営業時間", 
                options=["昼（11:00～14:00）", "夜（17:30～19:30）", "昼・夜"], 
                index=0, 
                accept_new_options=False, 
                key="business_hours3"
            )
        with col3:
            st.selectbox(
                label=":material/storefront: 店舗", 
                options=["西食堂", "東カフェテリア", "両方"], 
                accept_new_options=False, 
                index=0, 
                key="area3"
            )
        with col4:
            st.selectbox(
                label=":material/calculate: 集計方法", 
                options=["数量", "金額"], 
                index=0, 
                accept_new_options=False,
                key="aggregation3"
            )
        with col1:
            st.selectbox(
                label=":material/filter_alt: 商品の指定方法", 
                options=["名前", "バーコード", "SKU"], 
                index=0, 
                accept_new_options=False,
                key="method3"
            )
        with col2:
            candidates = candidates_itm1(
                df_itm, 
                st.session_state["date3"], 
                st.session_state["business_hours3"], 
                st.session_state["area3"], 
                st.session_state["method3"]
            )
            st.selectbox(
                label=f":material/lunch_dining: {st.session_state['method3']}", 
                options=candidates, 
                index=0, 
                accept_new_options=False,
                key="item3"
            )
    with st.container(border=True):
        if len(st.session_state["date3"]) == 2:
            df_sales_itm = process_itm1(
                df_itm, 
                st.session_state["date3"], 
                st.session_state["business_hours3"], 
                st.session_state["area3"], 
                st.session_state["aggregation3"], 
                st.session_state["method3"], 
                st.session_state["item3"]
            )
            st.line_chart(data=df_sales_itm)
    with st.expander("データを見る", expanded=False):
        if len(st.session_state["date3"]) == 2:
            st.dataframe(df_sales_itm)
            st.download_button(
                label=":material/download: `.csv`でダウンロード", 
                data=convert_for_download(df_sales_itm, index=True), 
                file_name=f"sales_items_{st.session_state['date3'][0]}-{st.session_state['date3'][1]}.csv", 
                mime="text/csv"
            )

# space
st.write("")

# sales by department
with st.container(border=True):
    st.write("##### 各部門ごとの売上推移")
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.date_input(
                label=":material/calendar_month: 日付", 
                value=(min_date, max_date), 
                min_value=min_date, 
                max_value=max_date, 
                key="date4"
            )
        with col2:
            st.selectbox(
                label=":material/schedule: 営業時間", 
                options=["昼（11:00～14:00）", "夜（17:30～19:30）", "昼・夜"], 
                index=0, 
                accept_new_options=False, 
                key="business_hours4"
            )
        with col3:
            st.selectbox(
                label=":material/storefront: 店舗", 
                options=["西食堂", "東カフェテリア", "両方"], 
                accept_new_options=False, 
                index=0, 
                key="area4"
            )
        with col4:
            st.selectbox(
                label=":material/calculate: 集計方法", 
                options=["数量", "金額"], 
                index=0, 
                accept_new_options=False,
                key="aggregation4"
            )
        with col1:
            candidates = candidates_itm2(
                df_itm, 
                st.session_state["date4"], 
                st.session_state["business_hours4"], 
                st.session_state["area4"]
            )
            st.selectbox(
                label=":material/category: 部門", 
                options=candidates, 
                index=0, 
                accept_new_options=False,
                key="department4"
            )
    with st.container(border=True):
        if len(st.session_state["date4"]) == 2:
            df_sales_dep = process_itm2(
                df_itm, 
                st.session_state["date4"], 
                st.session_state["business_hours4"], 
                st.session_state["area4"], 
                st.session_state["aggregation4"], 
                st.session_state["department4"]
            )
            st.line_chart(data=df_sales_dep)
    with st.expander("データを見る", expanded=False):
        if len(st.session_state["date4"]) == 2:
            st.dataframe(df_sales_dep)
            st.download_button(
                label=":material/download: `.csv`でダウンロード", 
                data=convert_for_download(df_sales_dep, index=True), 
                file_name=f"sales_department_{st.session_state['date4'][0]}-{st.session_state['date4'][1]}.csv", 
                mime="text/csv"
            )



