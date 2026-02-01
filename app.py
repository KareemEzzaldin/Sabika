import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import time
# استدعاء ملف اللغات
from languages import translations

# ==========================================
# 🔐 الأرقام السرية (Logic)
# ==========================================
SERIAL_UP = 852.0   
SERIAL_DOWN = 258.0 
POWER_VAL = 2.0     

# إعدادات المخاطرة
RISK_DOLLARS = 5.0  
REWARD_RATIO = 2.0  

# 1. إعداد الصفحة (مؤقت حتى يتم تحميل الترجمة)
st.set_page_config(page_title="Mr.Ali Pro", layout="wide", page_icon="📊")

# ==========================================
# 🔄 متغيرات الجلسة
# ==========================================
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

# ==========================================
# 🎨 إعدادات التصميم (Dark Mode)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;700;900&display=swap');
    
    [data-testid="stAppViewContainer"] { background-color: #0E1117 !important; color: #FAFAFA !important; }
    [data-testid="stSidebar"] { background-color: #262730 !important; }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    [data-testid="stHeaderActionElements"] {display: none !important;}

    /* كروت السيناريوهات */
    .scenario-card {
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
        transition: transform 0.3s;
    }
    .buy-card {
        background: linear-gradient(145deg, rgba(0, 255, 127, 0.1), #0E1117);
        border: 2px solid #00FF7F;
    }
    .sell-card {
        background: linear-gradient(145deg, rgba(255, 68, 68, 0.1), #0E1117);
        border: 2px solid #FF4444;
    }
    .active-card {
        box-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
        transform: scale(1.02);
        border-color: #FFD700 !important;
    }

    /* جدول التحليل الرقمي */
    .analysis-table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-family: 'Cairo', sans-serif;
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        overflow: hidden;
    }
    .analysis-table th {
        background-color: #262730;
        color: #FFD700;
        padding: 15px;
        text-align: center;
        border-bottom: 2px solid #444;
    }
    .analysis-table td {
        padding: 12px;
        border-bottom: 1px solid #333;
        text-align: center;
        color: #fff;
        font-size: 1.1rem;
    }
    
    /* تنبيه الأمر */
    .order-alert {
        padding: 20px;
        background-color: #FFD700;
        color: #000;
        border-radius: 10px;
        text-align: center;
        font-weight: 900;
        font-size: 1.5rem;
        margin-bottom: 20px;
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.8; } 100% { opacity: 1; } }

    .price-large { font-size: 2.5rem; font-weight: bold; margin: 10px 0; }
    .label-text { font-size: 1rem; color: #aaa; }
    
    h1, h2, h3 { color: #f0f0f0 !important; }
    .live-dot { height: 10px; width: 10px; background-color: #00FF00; border-radius: 50%; display: inline-block; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ الإعدادات واللغة
# ==========================================
with st.expander("⚙️ Settings", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        language_sel = st.selectbox("اللغة / Language", ["العربية", "English"])
    with c2:
        auto_refresh = st.checkbox("Auto Refresh / تحديث تلقائي", value=True)

# تحديد قاموس الترجمة
lang_code = "ar" if language_sel == "العربية" else "en"
t = translations[lang_code]

# --- اللوجو ---
st.markdown(f"""
<div style="text-align: center; margin-bottom: 20px; margin-top: -20px;">
    <h1 style="font-size: 4rem; font-weight: 900; background: linear-gradient(to bottom, #FFD700, #8A6E2F); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-family: 'Cairo', sans-serif;">
        {t['app_name']}
    </h1>
    <p style="color: #888; letter-spacing: 2px; font-size: 1rem;">{t['slogan']}</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 📡 دالة جلب البيانات المتعددة
# ==========================================
@st.cache_data(ttl=60)
def get_data():
    try:
        df_1m = yf.download("GC=F", period="5d", interval="1m", progress=False)
        df_15m = yf.download("GC=F", period="5d", interval="15m", progress=False)
        df_30m = yf.download("GC=F", period="5d", interval="30m", progress=False)
        df_1h = yf.download("GC=F", period="5d", interval="1h", progress=False)
        
        dfs = [df_1m, df_15m, df_30m, df_1h]
        clean_dfs = []
        for df in dfs:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df.reset_index(inplace=True)
            if 'Datetime' in df.columns: df.rename(columns={'Datetime': 'Date'}, inplace=True)
            if df.empty: return None
            clean_dfs.append(df)
            
        return clean_dfs 
    except:
        return None

data = get_data()

if data:
    df_live, df_15m, df_30m, df_1h = data
    current_price = df_live['Close'].iloc[-1]
    
    # ==========================================
    # 🧮 المحرك الحسابي
    # ==========================================
    
    def calculate_frame_logic(df):
        ref_price = df['Close'].iloc[-2]
        open_price = df['Open'].iloc[-2]
        is_bullish = ref_price >= open_price
        serial = SERIAL_UP if is_bullish else SERIAL_DOWN
        trend_str = t['trend_up'] if is_bullish else t['trend_down']
        trend_color = "#00FF7F" if is_bullish else "#FF4444"
        calc_val = (ref_price / serial) ** POWER_VAL
        target = ref_price + calc_val if is_bullish else ref_price - calc_val
        return calc_val, target, trend_str, trend_color

    val_15m, target_15m, trend_15m, color_15m = calculate_frame_logic(df_15m)
    val_30m, target_30m, trend_30m, color_30m = calculate_frame_logic(df_30m)
    val_1h, target_1h, trend_1h, color_1h = calculate_frame_logic(df_1h)

    # ==========================================
    # 🚦 سيناريوهات التداول (الساعة)
    # ==========================================
    calc_up_1h = (df_1h['Close'].iloc[-2] / SERIAL_UP) ** POWER_VAL
    buy_entry = df_1h['Close'].iloc[-2] + calc_up_1h
    
    calc_down_1h = (df_1h['Close'].iloc[-2] / SERIAL_DOWN) ** POWER_VAL
    sell_entry = df_1h['Close'].iloc[-2] - calc_down_1h
    
    # التنبيهات
    is_buy_active = current_price >= buy_entry
    is_sell_active = current_price <= sell_entry
    
    action_msg = ""
    if is_buy_active:
        action_msg = f"{t['alert_buy']} {buy_entry:.1f}"
        active_class_buy, active_class_sell = "active-card", ""
    elif is_sell_active:
        action_msg = f"{t['alert_sell']} {sell_entry:.1f}"
        active_class_buy, active_class_sell = "", "active-card"
    else:
        active_class_buy, active_class_sell = "", ""

    # ==========================================
    # 📺 العرض (UI)
    # ==========================================
    
    # 1. التنبيه العلوي
    if action_msg:
        st.markdown(f'<div class="order-alert">{action_msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="text-align:center; color:#888; margin-bottom:20px; border:1px dashed #444; padding:10px; border-radius:10px;">
            {t['wait_zone']} <b>${current_price:,.2f}</b> <span class="live-dot"></span>
        </div>
        """, unsafe_allow_html=True)

    # 2. كروت السيناريوهات
    c_buy, c_sell = st.columns(2)
    
    with c_buy:
        buy_sl = buy_entry - RISK_DOLLARS
        buy_tp = buy_entry + (RISK_DOLLARS * REWARD_RATIO)
        st.markdown(f"""
        <div class="scenario-card buy-card {active_class_buy}">
            <h2 style="color:#00FF7F; margin:0;">{t['buy_zone_title']}</h2>
            <p class="label-text">{t['entry_point']}</p>
            <div class="price-large" style="color:#fff;">${buy_entry:,.2f}</div>
            <hr style="border-color:rgba(0,255,127,0.3);">
            <div style="display:flex; justify-content:space-between;">
                <div><span style="color:#FF4444;">{t['stop_loss']}</span><br><b>${buy_sl:,.1f}</b></div>
                <div><span style="color:#00FF7F;">{t['take_profit']}</span><br><b>${buy_tp:,.1f}</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c_sell:
        sell_sl = sell_entry + RISK_DOLLARS
        sell_tp = sell_entry - (RISK_DOLLARS * REWARD_RATIO)
        st.markdown(f"""
        <div class="scenario-card sell-card {active_class_sell}">
            <h2 style="color:#FF4444; margin:0;">{t['sell_zone_title']}</h2>
            <p class="label-text">{t['entry_point']}</p>
            <div class="price-large" style="color:#fff;">${sell_entry:,.2f}</div>
            <hr style="border-color:rgba(255,68,68,0.3);">
            <div style="display:flex; justify-content:space-between;">
                <div><span style="color:#FF4444;">{t['stop_loss']}</span><br><b>${sell_sl:,.1f}</b></div>
                <div><span style="color:#00FF7F;">{t['take_profit']}</span><br><b>${sell_tp:,.1f}</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 3. الجدول
    st.markdown(f"<h3 style='text-align:center; color:#FFD700; margin-top:20px;'>{t['table_header']}</h3>", unsafe_allow_html=True)
    st.markdown(f"""
    <table class="analysis-table">
        <tr>
            <th>{t['th_timeframe']}</th>
            <th>{t['th_calc']}</th>
            <th>{t['th_trend']}</th>
            <th>{t['th_target']}</th>
        </tr>
        <tr>
            <td>{t['tf_1h']}</td>
            <td style="color:#00e6e6; font-weight:bold;">{val_1h:.2f}</td>
            <td style="color:{color_1h};">{trend_1h}</td>
            <td style="color:#FFD700; font-weight:bold;">${target_1h:,.2f}</td>
        </tr>
        <tr>
            <td>{t['tf_30m']}</td>
            <td style="color:#00e6e6; font-weight:bold;">{val_30m:.2f}</td>
            <td style="color:{color_30m};">{trend_30m}</td>
            <td style="color:#FFD700; font-weight:bold;">${target_30m:,.2f}</td>
        </tr>
        <tr>
            <td>{t['tf_15m']}</td>
            <td style="color:#00e6e6; font-weight:bold;">{val_15m:.2f}</td>
            <td style="color:{color_15m};">{trend_15m}</td>
            <td style="color:#FFD700; font-weight:bold;">${target_15m:,.2f}</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)

    # 4. الرسم البياني
    st.markdown("<br>", unsafe_allow_html=True)
    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(go.Candlestick(
        x=df_live['Date'], open=df_live['Open'], high=df_live['High'],
        low=df_live['Low'], close=df_live['Close'], name='Price'
    ))
    
    fig.add_hline(y=buy_entry, line_dash="dash", line_color="#00FF7F", annotation_text=t['chart_buy_zone'])
    fig.add_hline(y=sell_entry, line_dash="dash", line_color="#FF4444", annotation_text=t['chart_sell_zone'])

    fig.update_layout(
        height=500, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#888"), showlegend=False, dragmode='pan',
        title=dict(text=t['chart_title'], font=dict(size=14, color="#fff"))
    )
    fig.update_xaxes(showgrid=False, rangeslider_visible=False)
    fig.update_yaxes(showgrid=True, gridcolor='#2b2f44')
    
    if len(df_live) > 60:
        fig.update_xaxes(range=[df_live['Date'].iloc[-60], df_live['Date'].iloc[-1]])

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': True})

    if auto_refresh:
        time.sleep(30)
        st.rerun()

else:
    st.warning(t['loading'])
    time.sleep(2)
    st.rerun()