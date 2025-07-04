import streamlit as st
import pandas as pd
from pandas import DataFrame
import datetime
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go


#-----------------------------------------Settings-----------------------------------------

favicon = Image.open("static/favicon.ico")
sleeping = Image.open("static/sleeping_hamburger.png")
st.set_page_config(
    page_title="データ可視化", 
    layout="wide",
    initial_sidebar_state="expanded", 
    page_icon=favicon, 
    menu_items={
        'Get help': "https://www.example.com/help", # This will be replaced with GitHub Pages URL
        'Report a bug': st.secrets["google_forms"]["report_a_bug"], # Google Forms
        'About': "#### POScope \nv1.0.0"
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
    """
    Description
    """
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
    if df_cus.empty:
        return pd.DataFrame()
    else:
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
    if df_itm.empty:
        return pd.DataFrame()
    df_itm = df_itm.groupby("アカウント名").resample("1D", on="開始日時")[aggregation].sum()
    df_itm = df_itm.to_frame().unstack(level=0)
    df_itm.columns = df_itm.columns.droplevel(0)
    return df_itm


@st.cache_data
def candidates_itm1(df_itm: pd.DataFrame, date: tuple[datetime.date], business_hours: str, area: str, method: str):
    if len(date) != 2:
        return []
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
    if df_itm.empty:
        return pd.DataFrame()
    df_itm = df_itm.groupby("アカウント名").resample("1D", on="開始日時")[aggregation].sum()
    df_itm = df_itm.to_frame().unstack(level=0)
    df_itm.columns = df_itm.columns.droplevel(0)
    return df_itm


@st.cache_data
def candidates_itm2(df_itm: pd.DataFrame, date: tuple[datetime.date], business_hours: str, area: str):
    if len(date) != 2:
        return []
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
    st.error(":material/error: POSデータがアップロードされていません。")
    st.stop()

# Load data
df_cus = st.session_state["df_customers"]
df_itm = st.session_state["df_items"]
min_date = st.session_state["min_date"]
max_date = st.session_state["max_date"]

# visualization
st.subheader("客数の可視化", divider="gray")

# 1. number of customers by time of day
with st.container(border=True):
    st.write("##### 1日の時間帯ごとの客数の推移")
    # Options
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
                key="span1"
            )
        with col3:
            st.selectbox(
                label=":material/schedule: 営業時間", 
                options=["昼（11:00～14:00）", "夜（17:30～19:30）", "昼・夜"], 
                index=0, 
                accept_new_options=False, 
                key="bsh1"
            )
        with col4:
            st.selectbox(
                label=":material/storefront: 店舗", 
                options=["西食堂", "東カフェテリア"], # 両方の実装
                accept_new_options=False, 
                index=0, 
                key="area1"
            )
    # Data processing and visualization
    with st.container(border=True):
        if len(st.session_state["date1"]) == 2:
            df_cus_time = process_cus1(
                df_cus, 
                st.session_state["date1"], 
                st.session_state["span1"],
                st.session_state["bsh1"], 
                st.session_state["area1"]
            )
            #df_cus_time
            if not df_cus_time.empty:
                #if "df_calendar" in st.session_state:
                #    df_cal: DataFrame = st.session_state["df_calendar"]
                #    df_cal_target = df_cal[df_cal["date"].between(pd.Timestamp(st.session_state["date1"][0]), pd.Timestamp(st.session_state["date1"][1]))]
                #    exclude_dates = df_cal_target[~df_cal_target["class"].isin(["MON", "TUE", "WED", "THU", "FRI"])]["date"].dt.date.tolist()
                #else:
                #    exclude_dates = []
                df_cus_time_sum = df_cus_time.sum(axis="index")
                exclude_dates = df_cus_time_sum[df_cus_time_sum == 0].index.tolist()
                fig = go.Figure()
                for col in df_cus_time.columns:
                    if col.weekday() in [5, 6] or col in exclude_dates:  # Saturday and Sunday
                        continue
                    fig.add_trace(go.Scatter(
                        x=df_cus_time.index, 
                        y=df_cus_time[col], 
                        mode="lines+markers", 
                        name=col.strftime("%Y-%m-%d"), 
                        line=dict(color="rgba(0, 104, 201, 0.5)"), 
                        marker=dict(size=5), 
                        hovertemplate="日付: %{meta}<br>時間: %{x}<br>客数: %{y}人<extra></extra>", 
                        meta=col.strftime("%Y-%m-%d (%a)")
                    ))
                # Plot average if there are multiple columns
                if len(df_cus_time.columns) >= 2:
                    # Calculate the average for only weekdays (excluding weekends)
                    ave = df_cus_time[[col for col in df_cus_time.columns if col.weekday() not in [5, 6] and col not in exclude_dates]].mean(axis="columns")
                    fig.add_trace(go.Scatter(
                        x=df_cus_time.index, 
                        y=ave, 
                        mode="lines+markers", 
                        name="平均", 
                        line=dict(color="rgba(0, 0, 0, 1)", dash="dot"), 
                        marker=dict(size=5), 
                        hovertemplate="平均<br>時間: %{x}<br>客数: %{y:.1f}人<extra></extra>"
                    ))
                st.plotly_chart(fig)
            else:
                st.image(sleeping)
    # Data
    with st.expander("データを見る", expanded=False):
        if len(st.session_state["date1"]) == 2:
            st.dataframe(df_cus_time)
            st.download_button(
                label=":material/download: `.csv`でダウンロード", 
                data=convert_for_download(df_cus_time, index=True), 
                file_name=f"customers_by_time_{st.session_state['date1'][0]}-{st.session_state['date1'][1]}.csv", 
                mime="text/csv"
            )

# space
st.write("")

# 2. total number of customers per day
with st.container(border=True):
    st.write("##### 1日の合計客数の推移")
    # Options
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
                key="bsh2"
            )
        with col3:
            st.selectbox(
                label=":material/storefront: 店舗", 
                options=["西食堂", "東カフェテリア", "両方"], 
                accept_new_options=False, 
                index=0, 
                key="area2", 
                help="「両方」を選択すると、東西店舗の各グラフを重ね合わせて可視化します。"
            )
    # Data processing and visualization
    with st.container(border=True):
        if len(st.session_state["date2"]) == 2:
            df_cus_day = process_cus2(
                df_cus, 
                st.session_state["date2"], 
                st.session_state["bsh2"], 
                st.session_state["area2"]
            )
            if not df_cus_day.empty:
                stores = df_cus_day.columns
                # Add more information from the calendar data if available
                if "df_calendar" in st.session_state:
                    df_cus_day = pd.merge(
                        df_cus_day, 
                        st.session_state["df_calendar"], 
                        left_on="開始日時", 
                        right_on="date", 
                        how="left"
                    )
                    fig = go.Figure()
                    for store in stores:
                        fig.add_trace(go.Scatter(
                            x=df_cus_day["date"], 
                            y=df_cus_day[store], 
                            mode="lines+markers", 
                            marker=dict(size=5), 
                            name=store, 
                            hovertemplate="日付: %{x}<br>客数: %{y}人<br>学期: %{meta[0]}年度%{meta[1]}<br>講義情報: %{meta[2]}<br>その他情報: %{meta[3]}<extra></extra>", 
                            meta=df_cus_day[["academic_year", "term", "class", "info"]].values.tolist()
                        ))
                    st.plotly_chart(fig)
                else:
                    fig = go.Figure()
                    for store in stores:
                        fig.add_trace(go.Scatter(
                            x=df_cus_day.index, 
                            y=df_cus_day[store], 
                            mode="lines+markers", 
                            marker=dict(size=5), 
                            name=store, 
                            hovertemplate="日付: %{x}<br>客数: %{y}人<extra></extra>"
                        ))
                    st.plotly_chart(fig)
            else:
                st.image(sleeping)
    # Data
    with st.expander("データを見る", expanded=False):
        if len(st.session_state["date2"]) == 2:
            st.dataframe(df_cus_day)
            st.download_button(
                label=":material/download: `.csv`でダウンロード", 
                data=convert_for_download(df_cus_day, index=True), 
                file_name=f"customers_per_day_{st.session_state['date2'][0]}-{st.session_state['date2'][1]}.csv", 
                mime="text/csv"
            )
        
# space
st.write("")

# 3. ratio of payment methods
with st.container(border=True):
    st.write("##### 支払い方法の割合")
    # Options
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
                key="bsh3"
            )
        with col3:
            st.selectbox(
                label=":material/storefront: 店舗", 
                options=["西食堂", "東カフェテリア", "両方"], 
                accept_new_options=False, 
                index=0, 
                key="area3", 
                help="「両方」を選択すると、東西両店舗のデータを合算して可視化します。"
            )
    # Data processing and visualization
    with st.container(border=True):
        if len(st.session_state["date3"]) == 2:
            df_pm = filter_pm(
                df_cus, 
                st.session_state["date3"], 
                st.session_state["bsh3"], 
                st.session_state["area3"]
            )
            if df_pm["カウント"].sum() != 0:
                fig = go.Figure()
                fig.add_trace(go.Pie(
                    values=df_pm["カウント"], 
                    labels=df_pm["支払い方法"], 
                    hovertemplate="支払い方法: %{label}<br>カウント: %{value}人<extra></extra>"
                ))
                st.plotly_chart(fig)
            else:
                st.image(sleeping)
    # Data
    with st.expander("データを見る", expanded=False):
        if len(st.session_state["date3"]) == 2:
            st.dataframe(df_pm, hide_index=True)
            st.download_button(
                label=":material/download: `.csv`でダウンロード", 
                data=convert_for_download(df_pm, index=False), 
                file_name=f"payments_{st.session_state['date3'][0]}-{st.session_state['date3'][1]}.csv", 
                mime="text/csv"
            )

# space
st.write("")

st.subheader("売上の可視化", divider="gray")

# 4. sales by item
with st.container(border=True):
    st.write("##### 各商品ごとの売上推移")
    # Options
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
                key="bsh4"
            )
        with col3:
            st.selectbox(
                label=":material/storefront: 店舗", 
                options=["西食堂", "東カフェテリア", "両方"], 
                accept_new_options=False, 
                index=0, 
                key="area4", 
                help="「両方」を選択すると、東西店舗の各グラフを重ね合わせて可視化します。"
            )
        with col4:
            st.selectbox(
                label=":material/calculate: 集計方法", 
                options=["数量", "金額"], 
                index=0, 
                accept_new_options=False,
                key="aggr4"
            )
        with col1:
            st.selectbox(
                label=":material/filter_alt: 商品の指定方法", 
                options=["名前", "バーコード", "SKU"], 
                index=0, 
                accept_new_options=False,
                key="mthd4"
            )
        with col2:
            candidates = candidates_itm1(
                df_itm, 
                st.session_state["date4"], 
                st.session_state["bsh4"], 
                st.session_state["area4"], 
                st.session_state["mthd4"]
            )
            st.selectbox(
                label=f":material/lunch_dining: {st.session_state['mthd4']}", 
                options=candidates, 
                index=0, 
                accept_new_options=False,
                key="item4"
            )
    # Data processing and visualization
    with st.container(border=True):
        if len(st.session_state["date4"]) == 2:
            df_sales_itm = process_itm1(
                df_itm, 
                st.session_state["date4"], 
                st.session_state["bsh4"], 
                st.session_state["area4"], 
                st.session_state["aggr4"], 
                st.session_state["mthd4"], 
                st.session_state["item4"]
            )
            if not df_sales_itm.empty:
                stores = df_sales_itm.columns
                # Add more information from the calendar data if available
                if "df_calendar" in st.session_state:
                    df_sales_itm = pd.merge(
                        df_sales_itm, 
                        st.session_state["df_calendar"], 
                        left_on = "開始日時", 
                        right_on="date", 
                        how="left"
                    )
                    fig = go.Figure()
                    for store in stores:
                        fig.add_trace(go.Scatter(
                            x=df_sales_itm["date"], 
                            y=df_sales_itm[store], 
                            mode="lines+markers", 
                            marker=dict(size=5), 
                            name=store, 
                            hovertemplate="日付: %{x}<br>売上: "
                                 + ("%{y}個" if st.session_state["aggr4"] == "数量" else "%{y:,}円")
                                 + "<br>学期: %{meta[0]}年度%{meta[1]}<br>講義情報: %{meta[2]}<br>その他情報: %{meta[3]}<extra></extra>", 
                            meta=df_sales_itm[["academic_year", "term", "class", "info"]].values.tolist()
                        ))
                    st.plotly_chart(fig)
                else:
                    fig = go.Figure()
                    for store in stores:
                        fig.add_trace(go.Scatter(
                            x=df_sales_itm.index, 
                            y=df_sales_itm[store], 
                            mode="lines+markers", 
                            marker=dict(size=5), 
                            name=store, 
                            hovertemplate="日付: %{x}<br>売上: "
                                 + ("%{y}個" if st.session_state["aggr4"] == "数量" else "%{y:,}円")
                                 + "<extra></extra>"
                        ))
                    st.plotly_chart(fig)
            else:
                st.image(sleeping)
    # Data
    with st.expander("データを見る", expanded=False):
        if len(st.session_state["date4"]) == 2:
            st.dataframe(df_sales_itm)
            st.download_button(
                label=":material/download: `.csv`でダウンロード", 
                data=convert_for_download(df_sales_itm, index=True), 
                file_name=f"sales_items_{st.session_state['date4'][0]}-{st.session_state['date4'][1]}.csv", 
                mime="text/csv"
            )

# space
st.write("")

# 5. sales by department
with st.container(border=True):
    st.write("##### 各部門ごとの売上推移")
    # Options
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.date_input(
                label=":material/calendar_month: 日付", 
                value=(min_date, max_date), 
                min_value=min_date, 
                max_value=max_date, 
                key="date5"
            )
        with col2:
            st.selectbox(
                label=":material/schedule: 営業時間", 
                options=["昼（11:00～14:00）", "夜（17:30～19:30）", "昼・夜"], 
                index=0, 
                accept_new_options=False, 
                key="bsh5"
            )
        with col3:
            st.selectbox(
                label=":material/storefront: 店舗", 
                options=["西食堂", "東カフェテリア", "両方"], 
                accept_new_options=False, 
                index=0, 
                key="area5"
            )
        with col4:
            st.selectbox(
                label=":material/calculate: 集計方法", 
                options=["数量", "金額"], 
                index=0, 
                accept_new_options=False,
                key="aggr5"
            )
        with col1:
            candidates = candidates_itm2(
                df_itm, 
                st.session_state["date5"], 
                st.session_state["bsh5"], 
                st.session_state["area5"]
            )
            st.selectbox(
                label=":material/category: 部門", 
                options=candidates, 
                index=0, 
                accept_new_options=False,
                key="dpmt5"
            )
    # Data processing and visualization
    with st.container(border=True):
        if len(st.session_state["date5"]) == 2:
            df_sales_dep = process_itm2(
                df_itm, 
                st.session_state["date5"], 
                st.session_state["bsh5"], 
                st.session_state["area5"], 
                st.session_state["aggr5"], 
                st.session_state["dpmt5"]
            )
            if not df_sales_dep.empty:
                stores = df_sales_dep.columns
                # Add more information from the calendar data if available
                if "df_calendar" in st.session_state:
                    df_sales_dep = pd.merge(
                        df_sales_dep, 
                        st.session_state["df_calendar"], 
                        left_on = "開始日時", 
                        right_on="date", 
                        how="left"
                    )
                    fig = go.Figure()
                    for store in stores:
                        fig.add_trace(go.Scatter(
                            x=df_sales_dep["date"], 
                            y=df_sales_dep[store], 
                            mode="lines+markers", 
                            marker=dict(size=5), 
                            name=store, 
                            hovertemplate="日付: %{x}<br>売上: "
                                 + ("%{y}個" if st.session_state["aggr5"] == "数量" else "%{y:,}円")
                                 + "<br>学期: %{meta[0]}年度%{meta[1]}<br>講義情報: %{meta[2]}<br>その他情報: %{meta[3]}<extra></extra>", 
                            meta=df_sales_dep[["academic_year", "term", "class", "info"]].values.tolist()
                        ))
                    st.plotly_chart(fig)
                else:
                    fig = go.Figure()
                    for store in stores:
                        fig.add_trace(go.Scatter(
                            x=df_sales_dep.index, 
                            y=df_sales_dep[store], 
                            mode="lines+markers", 
                            marker=dict(size=5), 
                            name=store, 
                            hovertemplate="日付: %{x}<br>売上: "
                                 + ("%{y}個" if st.session_state["aggr5"] == "数量" else "%{y:,}円")
                                 + "<extra></extra>"
                        ))
                    st.plotly_chart(fig)
            else:
                st.image(sleeping)
    # Data
    with st.expander("データを見る", expanded=False):
        if len(st.session_state["date5"]) == 2:
            st.dataframe(df_sales_dep)
            st.download_button(
                label=":material/download: `.csv`でダウンロード", 
                data=convert_for_download(df_sales_dep, index=True), 
                file_name=f"sales_department_{st.session_state['date5'][0]}-{st.session_state['date5'][1]}.csv", 
                mime="text/csv"
            )

