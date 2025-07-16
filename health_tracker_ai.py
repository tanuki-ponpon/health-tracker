# health_tracker_ai.py
import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="健康・生活記録AI", layout="wide")
st.title("🌿 健康・生活記録 AI アシスタント")

CSV_FILE = "health_log.csv"
REQUIRED_COLUMNS = [
    "日付", "体重", "睡眠時間", "気分", "支出", "支出カテゴリ",
    "朝食時間", "朝食内容", "昼食時間", "昼食内容",
    "夕食時間", "夕食内容", "就寝時間", "起床時間", "メモ"
]

# 入力フォーム
with st.form(key="record_form"):
    col1, col2 = st.columns(2)
    with col1:
        weight = st.number_input("体重 (kg)", step=0.1)
        sleep_hours = st.number_input("睡眠時間 (時間)", step=0.1)
        mood = st.slider("気分（1=悪い ～ 5=良い）", 1, 5, 3)
        spend = st.number_input("支出 (円)", step=100)
        spend_cat = st.selectbox("支出カテゴリ", ["食費", "趣味", "交通", "日用品", "医療", "その他"])
    with col2:
        st.markdown("### 🥣 食事記録")
        b_time = st.time_input("朝食の時間")
        b_menu = st.text_input("朝食の内容")
        l_time = st.time_input("昼食の時間")
        l_menu = st.text_input("昼食の内容")
        d_time = st.time_input("夕食の時間")
        d_menu = st.text_input("夕食の内容")

    st.markdown("### 😴 睡眠記録")
    sleep_start = st.time_input("就寝時間")
    sleep_end = st.time_input("起床時間")

    memo = st.text_area("📝 メモ")
    submit = st.form_submit_button("保存")

# 保存処理
if submit:
    new_record = {
        "日付": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "体重": weight,
        "睡眠時間": sleep_hours,
        "気分": mood,
        "支出": spend,
        "支出カテゴリ": spend_cat,
        "朝食時間": b_time,
        "朝食内容": b_menu,
        "昼食時間": l_time,
        "昼食内容": l_menu,
        "夕食時間": d_time,
        "夕食内容": d_menu,
        "就寝時間": sleep_start,
        "起床時間": sleep_end,
        "メモ": memo
    }

    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
    else:
        df = pd.DataFrame()

    # 必要な列を強制的に確保
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = None

    df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)
    st.success("✅ 記録を保存しました")

# データ読み込み
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)

    # 必要な列がない場合は補完
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = None

    df["日付_dt"] = pd.to_datetime(df["日付"], errors='coerce')
    df["月"] = df["日付_dt"].dt.to_period("M")

    # データ型安全化
    df["体重"] = pd.to_numeric(df["体重"], errors="coerce")
    df["気分"] = pd.to_numeric(df["気分"], errors="coerce")
    df["睡眠時間"] = pd.to_numeric(df["睡眠時間"], errors="coerce")
    df["支出"] = pd.to_numeric(df["支出"], errors="coerce")

    st.subheader("📊 月ごとの平均体重・気分")
    monthly_avg = df.groupby("月")[["体重", "気分"]].mean().round(2)
    st.dataframe(monthly_avg)

    st.subheader("😴 睡眠と気分の関係（直近7日）")
    recent = df.sort_values("日付_dt").tail(7)
    if len(recent) >= 2:
        st.line_chart(recent.set_index("日付_dt")[["睡眠時間", "気分"]])

    st.subheader("💸 支出カテゴリ別分析")
    spending = df.groupby("支出カテゴリ")["支出"].sum()
    st.bar_chart(spending)

    st.subheader("🧠 AI コメントとアラート")
    comments = []

    sleep_short_days = df[df["睡眠時間"] < 6]
    if len(sleep_short_days) >= 3 and (sleep_short_days["日付_dt"].max() - sleep_short_days["日付_dt"].min()).days <= 5:
        comments.append("🛌 睡眠が3日以上短めです。早めの就寝を意識しましょう。")

    if df["気分"].tail(3).mean() <= 2:
        comments.append("😟 最近気分が落ち込みがちです。小さな楽しみを取り入れてみましょう。")

    if len(df) >= 2 and abs(df["体重"].iloc[-1] - df["体重"].iloc[-2]) > 1.5:
        comments.append("⚠️ 体重が急激に変化しています。体調の変化に注意を。")

    if df["支出"].tail(7).sum() > 15000:
        comments.append("💸 最近1週間の支出が多めです。無駄遣いがないか見直してみましょう。")

    if df["昼食内容"].str.contains("カップラーメン|ラーメン|揚げ物", na=False).sum() >= 3:
        comments.append("🍜 最近昼食が偏っています。栄養バランスを意識しましょう。")

    if not comments:
        comments.append("✅ 特に問題なし。良い習慣を続けましょう！")

    for c in comments:
        st.write(c)
else:
    st.info("まだ記録がありません。今日のデータを入力してみましょう！")
