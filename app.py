import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import time
from languages import translations

# ==========================================
# ⚙️ إعدادات الصفحة
# ==========================================
st.set_page_config(page_title="Mr.Ali Pro", layout="wide", page_icon="🔢")
GOLD_SYMBOL = "GC=F"

# ==========================================
# 🔄 تهيئة الجلسة
# ==========================================
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

# ==========================================
# 🎨 الستايل (CSS)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    .mini-card {
        border-radius: 10px; padding: 15px 5px; text-align: center; margin-bottom: 10px;
        height: 100%; transition: transform 0.3s; display: flex; flex-direction: column;
        justify-content: center; align-items: center;
    }
    .buy-box { background: linear-gradient(145deg, rgba(0, 255, 127, 0.05), #0E1117); border: 1px solid #00FF7F; }
    .sell-box { background: linear-gradient(145deg, rgba(255, 68, 68, 0.05), #0E1117); border: 1px solid #FF4444; }
    
    .active-buy { box-shadow: 0 0 15px rgba(0, 255, 127, 0.6) !important; border: 2px solid #00FF7F !important; transform: scale(1.05); }
    .active-sell { box-shadow: 0 0 15px rgba(255, 68, 68, 0.6) !important; border: 2px solid #FF4444 !important; transform: scale(1.05); }
    
    .card-title { font-size: 0.9rem; color: #aaa; margin-bottom: 5px; }
    .card-value { font-size: 1.4rem; font-weight: bold; color: #fff; direction: ltr; }
    .zone-title { text-align: center; font-weight: bold; font-size: 1.5rem; margin-bottom: 15px; }
    .order-alert { padding: 20px; background-color: #FFD700; color: #000; border-radius: 10px; text-align: center; font-weight: 900; font-size: 1.5rem; margin-bottom: 20px; animation: pulse 1s infinite; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🎛️ القائمة الجانبية (الإعدادات)
# ==========================================
with st.sidebar:
    st.header("⚙️ الإعدادات / Settings")
    language_sel = st.selectbox("اللغة / Language", ["العربية", "English"])
    
    st.divider()
    
    # خيار التبديل بين الوضع اليدوي والآلي
    mode_type = st.radio("وضع التشغيل / Mode", ["تحليل السوق المباشر (Auto)", "حاسبة يدوية (Manual Calc)"])
    
    if mode_type == "تحليل السوق المباشر (Auto)":
        selected_tf_display = st.selectbox(
            "اختر الفريم / Timeframe", 
            ["1 Minute", "15 Minutes", "30 Minutes", "1 Hour", "4 Hours", "Daily", "Weekly"],
            index=3
        )
        auto_refresh = st.checkbox("تحديث تلقائي / Auto Refresh", value=True)
    else:
        auto_refresh = False # لا نحتاج تحديث في الوضع اليدوي

lang_code = "ar" if language_sel == "العربية" else "en"
t = translations[lang_code]

# ==========================================
# 🔢 مدخلات المعادلة (تظهر في الأعلى دائماً)
# ==========================================
with st.expander("🔢 إعدادات المعادلة (Variables)", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1: USER_SERIAL_UP = st.number_input("Serial UP", value=852.0, step=1.0)
    with c2: USER_SERIAL_DOWN = st.number_input("Serial DOWN", value=258.0, step=1.0)
    with c3: USER_POWER = st.number_input("Power (الأس)", value=2.0, step=0.1)

# مدخلات خاصة بالوضع اليدوي فقط
user_high = 0.0
user_low = 0.0
user_close = 0.0 # لتحديد الاتجاه

if mode_type == "حاسبة يدوية (Manual Calc)":
    st.markdown("### ✍️ أدخل بيانات الشمعة يدوياً")
    mc1, mc2, mc3 = st.columns(3)
    with mc1: user_high = st.number_input("القمة (High)", value=2000.0, step=0.1, format="%.2f")
    with mc2: user_low = st.number_input("القاع (Low)", value=1980.0, step=0.1, format="%.2f")
    with mc3: 
        # نستخدم checkbox لتحديد الاتجاه بدلاً من إدخال Close
        is_manual_bullish = st.checkbox("اتجاه صاعد (Bullish)؟", value=True)

# ==========================================
# 📡 دالة جلب البيانات (Yahoo Finance)
# ==========================================
@st.cache_data(ttl=60) 
def get_data():
    data = {}
    try:
        ticker = yf.Ticker(GOLD_SYMBOL)
        def fetch(period, interval):
            df = ticker.history(period=period, interval=interval)
            if df.empty: return pd.DataFrame()
            df.index = df.index.tz_localize(None) 
            df['Date'] = df.index
            return df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]

        data["M1"] = fetch("5d", "1m") 
        data["M15"] = fetch("5d", "15m")
        data["M30"] = fetch("5d", "30m")
        data["H1"] = fetch("1mo", "1h") 
        if not data["H1"].empty:
            df_4h = data["H1"].resample('4h', on='Date').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()
            df_4h['Date'] = df_4h.index
            data["H4"] = df_4h
        else: data["H4"] = pd.DataFrame()
        data["D1"] = fetch("1y", "1d")
        data["W1"] = fetch("2y", "1wk")
        return data, None
    except Exception as e: return None, str(e)

# ==========================================
# 🧮 المنطق الحسابي (الموحد)
# ==========================================
def calculate_logic(high, low, is_bullish):
    # استخدام مدخلات المستخدم للمعادلة
    calc_up_val = (high / USER_SERIAL_UP) ** USER_POWER
    calc_down_val = (low / USER_SERIAL_DOWN) ** USER_POWER

    # 🟢 شراء
    buy_entry = high + calc_up_val
    buy_sl = buy_entry - 7.0 
    buy_tp = buy_entry + 7.0 

    # 🔴 بيع
    sell_entry = low + calc_down_val
    sell_sl = sell_entry + 7.0 
    sell_tp = sell_entry - 7.0 

    return {
        "is_bullish": is_bullish,
        "calc_val": calc_up_val if is_bullish else calc_down_val,
        "trend_str": "صاعد (Buy)" if is_bullish else "هابط (Sell)",
        "trend_color": "🟢" if is_bullish else "🔴",
        "buy_scenario": {"entry": buy_entry, "sl": buy_sl, "tp": buy_tp},
        "sell_scenario": {"entry": sell_entry, "sl": sell_sl, "tp": sell_tp}
    }

# ==========================================
# 📟 تنفيذ البرنامج
# ==========================================
st.markdown(f"""
<div style="text-align: center; margin-bottom: 20px;">
    <h1 style="font-size: 3.5rem; font-weight: 900; color: #FFD700;">{t['app_name']}</h1>
    <p style="color: #888;">{t['slogan']}</p>
</div>
""", unsafe_allow_html=True)

# 🅰️ السيناريو الأول: الوضع اليدوي
if mode_type == "حاسبة يدوية (Manual Calc)":
    # الحساب مباشرة من أرقامك
    res = calculate_logic(user_high, user_low, is_manual_bullish)
    
    # عرض النتائج
    st.divider()
    bs, ss = res["buy_scenario"], res["sell_scenario"]
    
    # تحديد أيهما النشط بناء على اختيارك للاتجاه
    c_buy = "active-buy" if is_manual_bullish else ""
    c_sell = "active-sell" if not is_manual_bullish else ""

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="zone-title" style="color:#00FF7F;">{t["buy_zone_title"]}</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="mini-card buy-box {c_buy}"><div class="card-title">{t["entry_point"]}</div><div class="card-value">${bs["entry"]:,.2f}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="mini-card buy-box {c_buy}"><div class="card-title" style="color:#FF4444;">{t["stop_loss"]}</div><div class="card-value">${bs["sl"]:,.2f}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="mini-card buy-box {c_buy}"><div class="card-title" style="color:#00FF7F;">{t["take_profit"]}</div><div class="card-value">${bs["tp"]:,.2f}</div></div>', unsafe_allow_html=True)

    with col2:
        st.markdown(f'<div class="zone-title" style="color:#FF4444;">{t["sell_zone_title"]}</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="mini-card sell-box {c_sell}"><div class="card-title">{t["entry_point"]}</div><div class="card-value">${ss["entry"]:,.2f}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="mini-card sell-box {c_sell}"><div class="card-title" style="color:#FF4444;">{t["stop_loss"]}</div><div class="card-value">${ss["sl"]:,.2f}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="mini-card sell-box {c_sell}"><div class="card-title" style="color:#00FF7F;">{t["take_profit"]}</div><div class="card-value">${ss["tp"]:,.2f}</div></div>', unsafe_allow_html=True)

# 🅱️ السيناريو الثاني: الوضع الآلي (سوق مباشر)
else:
    data_dict, error_msg = get_data()
    if error_msg: st.error(error_msg); st.stop()
    if not data_dict: st.warning("No Data"); st.stop()

    tf_keys_map = {"1 Minute": "M1", "15 Minutes": "M15", "30 Minutes": "M30", "1 Hour": "H1", "4 Hours": "H4", "Daily": "D1", "Weekly": "W1"}
    df_active = data_dict.get(tf_keys_map[selected_tf_display], pd.DataFrame())

    if not df_active.empty:
        # استخراج البيانات آلياً
        h = df_active['High'].iloc[-1] # الشمعة الحالية
        l = df_active['Low'].iloc[-1]
        c = df_active['Close'].iloc[-1]
        pc = df_active['Close'].iloc[-2]
        is_bull = c >= pc
        
        res = calculate_logic(h, l, is_bull)
        
        # ... (نفس كود العرض السابق للكروت والشارت) ...
        # (اختصاراً للرد، سيتم استخدام نفس كود العرض الموجود في الردود السابقة هنا)
        
        bs, ss = res["buy_scenario"], res["sell_scenario"]
        alert_txt = ""
        c_buy = "active-buy" if is_bull and c >= bs["entry"] else ""
        c_sell = "active-sell" if not is_bull and c <= ss["entry"] else ""
        
        if c_buy: alert_txt = f"🚀 Buy Signal: {bs['entry']:.2f}"
        if c_sell: alert_txt = f"🔻 Sell Signal: {ss['entry']:.2f}"
        
        if alert_txt: st.markdown(f'<div class="order-alert">{alert_txt}</div>', unsafe_allow_html=True)
        else: st.markdown(f"""<div style="text-align:center; margin-bottom:15px; border:1px dashed #444; padding:10px; border-radius:10px;">{t['wait_zone']} <b>${c:,.2f}</b></div>""", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="zone-title" style="color:#00FF7F;">{t["buy_zone_title"]}</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f'<div class="mini-card buy-box {c_buy}"><div class="card-title">{t["entry_point"]}</div><div class="card-value">${bs["entry"]:,.2f}</div></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="mini-card buy-box {c_buy}"><div class="card-title" style="color:#FF4444;">{t["stop_loss"]}</div><div class="card-value">${bs["sl"]:,.2f}</div></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="mini-card buy-box {c_buy}"><div class="card-title" style="color:#00FF7F;">{t["take_profit"]}</div><div class="card-value">${bs["tp"]:,.2f}</div></div>', unsafe_allow_html=True)

        with col2:
            st.markdown(f'<div class="zone-title" style="color:#FF4444;">{t["sell_zone_title"]}</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f'<div class="mini-card sell-box {c_sell}"><div class="card-title">{t["entry_point"]}</div><div class="card-value">${ss["entry"]:,.2f}</div></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="mini-card sell-box {c_sell}"><div class="card-title" style="color:#FF4444;">{t["stop_loss"]}</div><div class="card-value">${ss["sl"]:,.2f}</div></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="mini-card sell-box {c_sell}"><div class="card-title" style="color:#00FF7F;">{t["take_profit"]}</div><div class="card-value">${ss["tp"]:,.2f}</div></div>', unsafe_allow_html=True)

        # الشارت
        st.markdown("<br>", unsafe_allow_html=True)
        fig = go.Figure(data=[go.Candlestick(x=df_active['Date'], open=df_active['Open'], high=df_active['High'], low=df_active['Low'], close=df_active['Close'], name=selected_tf_display)])
        fig.add_hline(y=bs["entry"], line_dash="dash", line_color="#00FF7F", annotation_text="Buy")
        fig.add_hline(y=ss["entry"], line_dash="dash", line_color="#FF4444", annotation_text="Sell")
        fig.update_layout(height=500, margin=dict(l=10,r=10,t=30,b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#888"), title=f"{t['chart_title']} {selected_tf_display}", dragmode='pan', xaxis_rangeslider_visible=False)
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor='#2b2f44')
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

        # الجدول
        st.markdown("---")
        st.markdown(f"<h3 style='text-align:center; color:#FFD700;'>{t['table_header']}</h3>", unsafe_allow_html=True)
        table_data = []
        for name, key in [("Weekly", "W1"), ("Daily", "D1"), ("4 Hours", "H4"), ("1 Hour", "H1"), ("30 Min", "M30"), ("15 Min", "M15")]:
            df_t = data_dict.get(key, pd.DataFrame())
            if not df_t.empty:
                h_t, l_t = df_t['High'].iloc[-1], df_t['Low'].iloc[-1]
                is_bull_t = df_t['Close'].iloc[-1] >= df_t['Close'].iloc[-2]
                res_t = calculate_logic(h_t, l_t, is_bull_t)
                target = res_t["buy_scenario"]["entry"] if is_bull_t else res_t["sell_scenario"]["entry"]
                sl = res_t["buy_scenario"]["sl"] if is_bull_t else res_t["sell_scenario"]["sl"]
                table_data.append({
                    t['th_timeframe']: name, 
                    t['th_calc']: f"{res_t['calc_val']:.2f}", 
                    t['th_trend']: f"{res_t['trend_color']} {res_t['trend_str']}",
                    t['stop_loss']: f"${sl:,.2f}", 
                    t['th_target']: f"${target:,.2f}"
                })
        if table_data:
            st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

if auto_refresh:
    time.sleep(60)
    st.rerun()
