import streamlit as st
from PIL import Image
import statsmodels.api as sm
import pandas as pd
from pandas import DataFrame
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
from sklearn.metrics import root_mean_squared_error, mean_absolute_percentage_error
# from sklearn.preprocessing import MinMaxScaler
import numpy as np

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
        'About': "#### POScope \nv1.0.0"
    }
)


#-----------------------------------------Functions-----------------------------------------

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


def get_y(df_cus: DataFrame, store: str, bsh: str):
    """
    Get explained variable.
    """
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


def calculate_nweek(df_cal: DataFrame):
    r, _ = df_cal.shape
    current_term = ""
    first_mon_date = None
    nweeks = []
    daynames = ["MON", "TUE", "WED", "THU", "FRI"]
    for i in range(r):
        term = df_cal.loc[i, "term"]
        class_info = df_cal.loc[i, "class"]
        _date = df_cal.loc[i, "date"]
        dayname = _date.day_name()[:3].upper()
        if term in ["SPR", "SMR", "AUT", "WTR", "SMRINT", "WTRINT1to3", "WTRINT4"] and class_info != "NoClass":
            if current_term != term:
                # SPR->SMRとAUT->WTRのときは、first_mon_dateを変更しない
                if term == "SMR" or term == "WTR":
                    current_term = term
                else:
                    current_term = term
                    first_mon_date = _date - pd.Timedelta(days=daynames.index(dayname))
            nweeks.append((_date - first_mon_date).days // 7 + 1)
        else:
            nweeks.append(float("nan"))
    return nweeks


def get_holiday_dummy(df_cal: DataFrame):
    r, _ = df_cal.shape
    holidays = []
    for i in range(r):
        info = df_cal.loc[i, "info"]
        if pd.notna(info) and "Holiday" in info:
            holidays.append(1)
        else:
            holidays.append(0)
    return holidays


def get_replaced_dummy(df_cal: DataFrame):
    r, _ = df_cal.shape
    replaced = []
    for i in range(r):
        info = df_cal.loc[i, "info"]
        if pd.notna(info) and "Replaced" in info:
            replaced.append(1)
        else:
            replaced.append(0)
    return replaced


def get_first_week_dummy(df_cal: DataFrame):
    r, _ = df_cal.shape
    first_week = []
    for i in range(r):
        nweek = df_cal.loc[i, "nweek"]
        if nweek == 1:
            first_week.append(1)
        else:
            first_week.append(0)
    return first_week


# This function only works when the maximum number of week is 15.
# To cope with exceptions, more complicated logic is needed (future inplementation).
def get_last_week_dummy(df_cal: DataFrame):
    r, _ = df_cal.shape
    last_week = []
    for i in range(r):
        nweek = df_cal.loc[i, "nweek"]
        if nweek == 15:
            last_week.append(1)
        else:
            last_week.append(0)
    return last_week


def map_syllabus_data(df_syl: DataFrame, df_cal: DataFrame):
    r, _ = df_cal.shape
    jp_daynames = ["月", "火", "水", "木", "金"]
    en_daynames = ["MON", "TUE", "WED", "THU", "FRI"]
    main_terms = ["SPR", "SMR", "AUT", "WTR"]
    syllabus = []
    for i in range(r):
        academic_year = df_cal.loc[i, "academic_year"]
        term = df_cal.loc[i, "term"]
        class_dayname = df_cal.loc[i, "class"]
        if term in main_terms and class_dayname in en_daynames:
            jp_dayname = jp_daynames[en_daynames.index(class_dayname)]
            try:
                syl = df_syl.loc[(jp_dayname, [1, 2, 3]), str(academic_year)+term].sum()
            except KeyError:
                syl = float("nan")
        else:
            syl = float("nan")
        syllabus.append(syl)
    return syllabus


def get_X(df_cal: DataFrame, store: str):
    """
    Get explanatory valiables.
    """
    X = df_cal
    X["nweek"] = calculate_nweek(X)
    X["holiday"] = get_holiday_dummy(X)
    X["replaced"] = get_replaced_dummy(X)
    X["first_week"] = get_first_week_dummy(X)
    X["last_week"] = get_last_week_dummy(X)
    if store == "西食堂":
        X["syllabus"] = map_syllabus_data(
            st.session_state["df_syllabus_west"], 
            X
        )
    else:
        X["syllabus"] = map_syllabus_data(
            st.session_state["df_syllabus_east"], 
            X
        )
    # X can be empty when calendar data and syllabus data have no common dates
    X = X[(X["class"].isin(["MON", "TUE", "WED", "THU", "FRI"])) & (X["syllabus"].notna())]
    return X


def get_train_data(yX: DataFrame):
    y = yX["客数"]
    X = yX[["syllabus", "nweek", "holiday", "replaced", "first_week", "last_week"]]
    #scaler = MinMaxScaler()
    #X.loc[:, "syllabus"] = scaler.fit_transform(X[["syllabus"]])
    #X.loc[:, "nweek"] = scaler.fit_transform(X[["nweek"]])
    X_tr, X_va, y_tr, y_va = train_test_split(X, y, test_size=0.2, shuffle=False)
    return X_tr, X_va, y_tr, y_va


def train_model(y, X):
    model = sm.OLS(y, sm.add_constant(X))
    result = model.fit()
    return result


def forecast_button_controller():
    if "trained_model" in st.session_state:
        if st.session_state["predictable"] and not st.session_state["options_changed"]:
            return False # enable the butto
    return True # disable the button


def train_model_button_controller():
    if "trained_model" in st.session_state:
        if st.session_state["options_changed"]:
            return False # enable the button
        else:
            return True # disable the button
    return False # enable the button


def callback_on_change():
    st.session_state["options_changed"] = True
    del st.session_state["y_pred"]


#-----------------------------------------Contents-----------------------------------------

st.logo(favicon, size="large")

st.subheader("1日当たりの客数予測",divider="gray")

not_uploaded_files = check_uploaded_files()

# Initialize session state
if "options_changed" not in st.session_state:
    st.session_state["options_changed"] = False

with st.container(border=True):
    st.write("##### :material/model_training: 新たにモデルを構築する")

    # If one of the following files is not uploaded, stop the process
    if not_uploaded_files != []:
        st.error(
            f"""
            :material/error: 以下のファイルがアップロードされていません。
            {" - POSデータ" if "POSデータ" in not_uploaded_files else ""}
            {" - 履修者数データ" if "履修者数データ" in not_uploaded_files else ""}
            {" - カレンダー形式データ" if "カレンダー形式データ" in not_uploaded_files else ""}
            """
        )

    # If all files (POS, syllabus, and calendar) are uploaded
    else:
        # Options
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.selectbox(
                    label=":material/storefront: 店舗", 
                    options=["西食堂", "東カフェテリア"], 
                    index=0, 
                    key="forecast_store", 
                    on_change=callback_on_change
                )
            with col2:
                st.selectbox(
                    label=":material/schedule: 営業時間", 
                    options=["昼（11:00～14:00）", "夜（17:30～19:30）"], 
                    index=0, 
                    key="forecast_bsh", 
                    on_change=callback_on_change
                )
        # Deta preparation
        with st.container(border=True):
            if st.session_state["forecast_store"] == "西食堂":
                if "df_syllabus_west" not in st.session_state:
                    st.error("西食堂の履修者数データがアップロードされていません。")
                    st.stop()
            elif st.session_state["forecast_store"] == "東カフェテリア":
                if "df_syllabus_east" not in st.session_state:
                    st.error("東カフェテリアの履修者数データがアップロードされていません。")
                    st.stop()

            # Explained variable
            y = get_y(
                st.session_state["df_customers"], 
                st.session_state["forecast_store"], 
                st.session_state["forecast_bsh"]
            )
            # y can be empty when 東カフェテリア and 夜（17:30～19:30） are selected
            if y.empty:
                st.error("選択された条件のデータがありません。")
                st.stop()

            # Explanatory variables
            X = get_X(
                st.session_state["df_calendar"], 
                st.session_state["forecast_store"]
            )
            
            yX = pd.merge(y, X, left_on="開始日時", right_on="date", how="inner")

            # yX can be empty when
            # 1. at least one of y and X is empty
            # 2. y (POS) and X (calendar) have no common dates
            if yX.empty:
                st.error("アップロードされたファイルからは学習データを構成できません。")
                st.stop()
            
            predictable = list(set(X["date"]) - set(yX["date"]))
            predictable = sorted([_date for _date in predictable if _date > yX["date"].max()])
            X_for_pred = X[X["date"].isin(predictable)]
        
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=yX["date"], 
                y=[""] * len(yX), 
                mode="markers", 
                name="学習範囲", 
                marker=dict(color="red")
            ))
            fig.add_trace(go.Scatter(
                x=predictable, 
                y=[""] * len(predictable), 
                mode="markers", 
                name="予測範囲", 
                marker=dict(color="blue")
            ))
            fig.update_layout(
                showlegend=True, 
                margin=dict(l=20, r=20, t=20, b=20), 
                height=100, 
                width=550
            )
            fig.update_traces(marker=dict(size=5))
            st.write("###### 学習範囲と予測範囲")
            st.plotly_chart(fig)
        
        st.button(label="モデルを構築する", key="train_model_button", disabled=train_model_button_controller())

        if st.session_state["train_model_button"]:
            with st.spinner("モデルを構築中...", show_time=True):
                X_tr, X_va, y_tr, y_va = get_train_data(yX)
                result = train_model(np.log(y_tr), X_tr)
                y_tr_pred = np.exp(result.predict(sm.add_constant(X_tr)))
                y_va_pred = np.exp(result.predict(sm.add_constant(X_va)))
                tr_rmse = root_mean_squared_error(y_tr, y_tr_pred)
                va_rmse = root_mean_squared_error(y_va, y_va_pred)
                tr_mape = mean_absolute_percentage_error(y_tr, y_tr_pred)
                va_mape = mean_absolute_percentage_error(y_va, y_va_pred)

                st.session_state["yX"] = yX
                st.session_state["predictable"] = predictable
                st.session_state["trained_model"] = result
                st.session_state["y_tr_pred"] = y_tr_pred
                st.session_state["y_va_pred"] = y_va_pred
                st.session_state["tr_rmse"] = tr_rmse
                st.session_state["va_rmse"] = va_rmse
                st.session_state["tr_mape"] = tr_mape
                st.session_state["va_mape"] = va_mape
                st.session_state["options_changed"] = False
                st.session_state["X_for_pred"] = X_for_pred

                st.success(
                    f"""
                    :material/check_circle: モデルの構築が完了しました。

                    ＜予測精度＞
                     - 学習データのMAPE: {tr_mape:.2%}
                     - 学習データのRMSE: {tr_rmse:.2f}
                     - バリデーションデータのMAPE: {va_mape:.2%}
                     - バリデーションデータのRMSE: {va_rmse:.2f}
                    """
                )

                # Figure
                with st.container(border=True):
                    st.write("###### 学習結果")
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=yX["date"], 
                        y=yX["客数"], 
                        mode="lines+markers", 
                        name="観測値"
                    ))
                    fig.add_trace(go.Scatter(
                        x=yX["date"], 
                        y=y_tr_pred.tolist() + y_va_pred.tolist(), 
                        mode="lines+markers", 
                        name="予測値"
                    ))
                    st.plotly_chart(fig)
        # When the model exists and options are not changed
        else:
            if "trained_model" in st.session_state and not st.session_state["options_changed"]:
                st.success(
                    f"""
                    :material/check_circle: 以下のモデルの構築が完了しています。

                    ＜予測精度＞
                     - 学習データのMAPE: {st.session_state["tr_mape"]:.2%}
                     - 学習データのRMSE: {st.session_state["tr_rmse"]:.2f}
                     - バリデーションデータのMAPE: {st.session_state["va_mape"]:.2%}
                     - バリデーションデータのRMSE: {st.session_state["va_rmse"]:.2f}
                    """
                )
                # Figure
                with st.container(border=True):
                    st.write("###### 学習結果")
                    yX = st.session_state["yX"]
                    y_tr_pred = st.session_state["y_tr_pred"]
                    y_va_pred = st.session_state["y_va_pred"]
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=yX["date"], 
                        y=yX["客数"], 
                        mode="lines+markers", 
                        name="観測値"
                    ))
                    fig.add_trace(go.Scatter(
                        x=yX["date"], 
                        y=y_tr_pred.tolist() + y_va_pred.tolist(), 
                        mode="lines+markers", 
                        name="予測値"
                    ))
                    st.plotly_chart(fig)
        
        st.button(label="予測する", key="forecast_button", disabled=forecast_button_controller())

        if st.session_state["forecast_button"]:
            result = st.session_state["trained_model"]
            X_for_pred = st.session_state["X_for_pred"]
            yX = st.session_state["yX"]
            y_tr_pred = st.session_state["y_tr_pred"]
            y_va_pred = st.session_state["y_va_pred"]
            y_pred = np.exp(result.predict(sm.add_constant(X_for_pred[["syllabus", "nweek", "holiday", "replaced", "first_week", "last_week"]])))
            st.success(":material/check_circle: 予測が完了しました。")
            with st.container(border=True):
                st.write("###### 予測結果")
                fig = go.Figure()
                fig.add_traces(go.Scatter(
                    x=X_for_pred["date"], 
                    y=y_pred, 
                    mode="lines+markers", 
                    name="予測値", 
                    line=dict(color="lightgreen", width=2)
                ))
                fig.add_traces(go.Scatter(
                    x=yX["date"], 
                    y=yX["客数"], 
                    mode="lines+markers", 
                    name="観測値", 
                    line=dict(color="blue", width=2)
                ))
                fig.add_traces(go.Scatter(
                    x=yX["date"], 
                    y=y_tr_pred.tolist() + y_va_pred.tolist(), 
                    mode="lines+markers", 
                    name="学習済み予測値", 
                    line=dict(color="skyblue", width=2)
                ))
                st.plotly_chart(fig)
                st.session_state["y_pred"] = y_pred
            with st.expander("データを見る", expanded=False):
                df_pred = pd.DataFrame({
                    "date": X_for_pred["date"], 
                    "客数": y_pred
                })
                st.dataframe(df_pred)
        else:
            if "y_pred" in st.session_state and not st.session_state["options_changed"]:
                st.success(":material/check_circle: 以下の予測が完了しています。")
                # Figure
                with st.container(border=True):
                    st.write("###### 予測結果")
                    y_pred = st.session_state["y_pred"]
                    X_for_pred = st.session_state["X_for_pred"]
                    yX = st.session_state["yX"]
                    y_tr_pred = st.session_state["y_tr_pred"]
                    y_va_pred = st.session_state["y_va_pred"]
                    fig = go.Figure()
                    fig.add_traces(go.Scatter(
                        x=X_for_pred["date"], 
                        y=y_pred, 
                        mode="lines+markers", 
                        name="予測値", 
                        line=dict(color="lightgreen", width=2)
                    ))
                    fig.add_traces(go.Scatter(
                        x=yX["date"], 
                        y=yX["客数"], 
                        mode="lines+markers", 
                        name="観測値", 
                        line=dict(color="blue", width=2)
                    ))
                    fig.add_traces(go.Scatter(
                        x=yX["date"], 
                        y=y_tr_pred.tolist() + y_va_pred.tolist(), 
                        mode="lines+markers", 
                        name="学習済み予測値", 
                        line=dict(color="skyblue", width=2)
                    ))
                    st.plotly_chart(fig)
                # Data
                with st.expander("データを見る", expanded=False):
                    df_pred = pd.DataFrame({
                        "date": X_for_pred["date"], 
                        "客数": y_pred
                    })
                    st.dataframe(df_pred)
        
            

# space
st.write("")

with st.container(border=True):
    st.write("##### :material/line_axis: 既存のモデルから予測する")
    if "履修者数データ" in not_uploaded_files or "カレンダー形式データ" in not_uploaded_files:
        st.error(
            f"""
            :material/error: 以下のファイルがアップロードされていません。
            {" - 履修者数データ" if "履修者数データ" in not_uploaded_files else ""}
            {" - カレンダー形式データ" if "カレンダー形式データ" in not_uploaded_files else ""}
            """
        )
    else:
        st.file_uploader(
            label="学習済みモデルをアップロードしてください。",
            type=["pkl", "pickle"], 
            key="uploaded_model", 
            accept_multiple_files=False
        )
        if st.session_state["uploaded_model"]:
            st.session_state["uploaded_model"]
            st.write("pickleに学習データの期間、店舗、時間帯なども含まれているので、それを表示")


