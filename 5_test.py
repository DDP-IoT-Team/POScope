import streamlit as st
from PIL import Image
import statsmodels.api as sm
import joblib
import pandas as pd
from pandas import DataFrame

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

#説明変数:n_day, n_people_1to5
#目的変数:supply

#process pos data
#@st.cache_data(show_spinner=False)
#def get_supply(df_items: DataFrame):
#    df_daily_sum = df_items.groupby(["アカウント名", pd.Grouper(key="開始日時", freq="1D")])["数量"].sum().reset_index()
#    return df_daily_sum

def check_uploaded_files() -> list[str]:
    not_uploaded = []
    if "df_customers" not in st.session_state:
        not_uploaded.append("POSデータ")
    if "df_syllabus_west" not in st.session_state or "df_syllabus_east" not in st.session_state:
        not_uploaded.append("履修者数データ")
    if "df_calendar" not in st.session_state:
        not_uploaded.append("カレンダー形式データ")
    return not_uploaded


def resample_cus_pos(df_cus: DataFrame):
    df_cus_resampled = df_cus.groupby(["アカウント名", pd.Grouper(key="開始日時", freq="1D")])["客数"].sum()
    return df_cus_resampled


def get_supply(df_items: DataFrame):
    df_daily_sum = df_items.groupby(["アカウント名", pd.Grouper(key="開始日時", freq="1D")])["数量"].sum().reset_index()
    return df_daily_sum


def check_available_data():
    return None



@st.cache_data(show_spinner=False)
def get_training_data(df_cus: pd.DataFrame, store: str, bsh: str):
    df_cus_target = df_cus[df_cus["アカウント名"] == store]
    df_cus_target.set_index("開始日時", inplace=True)
    if bsh == "昼（11:00～14:00）":
        df_cus_target = df_cus_target.between_time("11:00", "14:00")
    elif bsh == "夜（17:30～19:30）":
        df_cus_target = df_cus_target.between_time("17:30", "19:30")
    df_cus_target.reset_index(drop=False, inplace=True)
    if df_cus_target.empty:
        return pd.DataFrame()
    df_cus_target = df_cus_target.resample("1D", on="開始日時")["客数"].sum()
    return df_cus_target


def train_model():
    return None


def forecast_cus():
    return None


#process syllabus data
@st.cache_data(show_spinner=False)
def adding_up(df_syllabus: DataFrame, nums):
    daynames = ["月", "火", "水", "木", "金"]
    eng_daynames = ["MON", "TUE", "WED", "THU", "FRI"]
    df_result = pd.DataFrame()
    for dayname, eng_dayname in zip(daynames, eng_daynames):
        df_syllabus_tmp = df_syllabus.loc[dayname].loc[nums].sum()
        df_syllabus_tmp.name = eng_dayname
        df_result = pd.concat([df_result, df_syllabus_tmp], axis=1)
    return df_result.T

@st.cache_data(show_spinner=False)
def predict_supply(df_items, df_calendar, df_syllabus, analysis_method:str, store:str, time_span:int):
    today = pd.Timestamp.today().normalize()
    df_calendar = df_calendar.copy()
    df_calendar["date"] = pd.to_datetime(df_calendar["date"])
    future_dates = df_calendar[df_calendar["date"] >= today].sort_values("date").head(time_span)
    n_day_df = future_dates[["n_day", "academic_year", "term", "date"]].reset_index(drop=True)

    weekday_map = {0: "MON", 1: "TUE", 2: "WED", 3: "THU", 4: "FRI"}
    n_day_df["weekday_eng"] = n_day_df["date"].dt.dayofweek.map(weekday_map)

    # n_people_1to5をsyllabusから取得

    #predicting supply
    X_pred = n_day_df[["n_day", "n_people_1to5"]]

    model = joblib.load(f"models/{analysis_method}/{store}.pkl")
    predictions = model.predict(X_pred)

    result = n_day_df[["date", "n_day", "n_people_1to5"]].copy()
    result["prediction"] = predictions
    return result

#-----------------------------------------Contents-----------------------------------------

st.logo(favicon, size="large")

st.subheader("客数予測",divider="gray")

# Check if the necessary data for forecasting are uploaded
# If not, execution stops
not_uploaded_files = check_uploaded_files()
if not_uploaded_files != []:
    st.error(
        f"""
        :material/error: 以下のファイルがアップロードされていません。
        {" - POSデータ" if "POSデータ" in not_uploaded_files else ""}
        {" - 履修者数データ" if "履修者数データ" in not_uploaded_files else ""}
        {" - カレンダー形式データ" if "カレンダー形式データ" in not_uploaded_files else ""}
        """
    )
    st.stop()

with st.container(border=True):
    st.write("##### 1日当たりの総来客数の予測")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.selectbox(
            label=":material/storefront: 店舗", 
            options=["西食堂", "東カフェテリア"], 
            index=0, 
            key="area"
        )
    with col2:
        st.selectbox(
            label=":material/schedule: 営業時間", 
            options=["昼（11:00～14:00）", "夜（17:30～19:30）"], 
            index=0, 
            key="bsh"
        )
    st.button(label="条件を決定する", key="conditions")
    st.button(label="学習する", key="train")
    st.button(label="予測する", key="forecast")
    tmp = get_training_data(
        st.session_state["df_customers"], 
        st.session_state["area"], 
        st.session_state["bsh"]
    )