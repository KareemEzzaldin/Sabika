import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import time
from datetime import datetime
from languages import translations

# ==========================================
# ⚙️ إعدادات الصفحة
# ==========================================
st.set_page_config(page_title="Mr.Ali Pro", layout="wide", page_icon="🔢")
GOLD_SYMBOL = "GC=F"

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
    
    /* تنسيق خفيف للحقول */
    div[data-baseweb="input"] { border-radius: 8px; background-color: #262730; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🛠️ الهيدر والإعدادات الجانبية
# ==========================================
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown(f"<h1 style='color:#FFD700;'>Mr.Ali Pro <span style='font-size:1rem; color:#aaa'>(Calculator)</span></h1>", unsafe_allow_html=True)
with c2:
    # خيار لتفعيل بيانات السوق الحية بدلاً من اليدوي
    use_live_data = st.checkbox("📡 استخدام بيانات السوق الحية (Yahoo)", value=False)

# ==========================================
# ✍️ منطقة الإدخال اليدوي (فوق الشارت مباشرة)
# ==========================================
if not use_live_data:
    st.markdown("### 📝 أدخل بيانات الشمعة والمعادلة يدوياً")
    
    # الصف الأول: بيانات السعر
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1: 
        INPUT_HIGH = st.number_input("القمة (High)", value=0.0, step=0.1, format="%.2f", help="أعلى سعر للشمعة")
    with col_p2: 
        INPUT_LOW = st.number_input("القاع (Low)", value=0.0, step=0.1, format="%.2f", help="أقل سعر للشمعة")
    with col_p3: 
        INPUT_CLOSE = st.number_input("السعر الحالي (Current Price)", value=0.0, step=0.1, format="%.2f", help="السعر الحالي لتحديد مكانك من المناطق")

    # الصف الثاني: متغيرات المعادلة
    st.markdown("##### 🔢 متغيرات المعادلة")
    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1: 
        INPUT_SERIAL_UP = st.number_input("Serial UP", value=852.0, step=1.0, format="%.2f")
    with col_v2: 
        INPUT_SERIAL_DOWN = st.number_input("Serial DOWN", value=258.0, step=1.0, format="%.2f")
    with col_v3: 
        INPUT_POWER = st.number_input("Power (الأس)", value=2.0, step=0.1, format="%.2f")

    st.markdown("---")

# ==========================================
# 📡 منطق جلب البيانات (يدوي أو آلي)
# ==========================================
# متغيرات ستستخدم في الحساب
calc_high = 0.0
calc_low = 0.0
calc_close = 0.0
calc_prev_close = 0.0 # للوضع الآلي فقط
calc_s_up = INPUT_SERIAL_UP if not use_live_data else 852.0
calc_s_down = INPUT_SERIAL_DOWN if not use_live_data else 258.0
calc_power = INPUT_POWER if not use_live_data else 2.0
df_chart = pd.DataFrame() # للشارت

if use_live_data:
    # جلب من Yahoo
    ticker = yf.Ticker(GOLD_SYMBOL)
    df = ticker.history(period="5d", interval="1h") # فريم الساعة كمثال
    if not df.empty:
        calc_high = df['High'].iloc[-1]
        calc_low = df['Low'].iloc[-1]
        calc_close = df['Close'].iloc[-1]
        calc_prev_close = df['Close'].iloc[-2]
        df_chart = df # نستخدم الداتا فريم كاملة للرسم
    else:
        st.error("فشل في جلب بيانات السوق الحية.")
        st.stop()
else:
    # استخدام البيانات اليدوية
    calc_high = INPUT_HIGH
    calc_low = INPUT_LOW
    calc_close = INPUT_CLOSE
    # في اليدوي، نعتبر الاتجاه صاعد إذا السعر الحالي أكبر من (القمة+القاع)/2 كتقدير، أو نترك المستخدم يقرر
    # لتبسيط الأمر: سنحسب المنطقتين دائماً
    
    # تكوين شمعة وهمية للرسم البياني
    if calc_high > 0:
        data = {
            'Date': [datetime.now()],
            'Open': [(calc_high + calc_low)/2], # افتراضي
            'High': [calc_high],
            'Low': [calc_low],
            'Close': [calc_close if calc_close > 0 else (calc_high+calc_low)/2]
        }
        df_chart = pd.DataFrame(data)

# ==========================================
# 🧮 الحسابات (المنطق الموحد)
# ==========================================
if calc_high > 0 and calc_low > 0:
    
    # 1. معادلة الشراء
    calc_up_val = (calc_high / calc_s_up) ** calc_power
    buy_entry = calc_high + calc_up_val
    buy_sl = buy_entry - 7.0
    buy_tp = buy_entry + 7.0

    # 2. معادلة البيع
    calc_down_val = (calc_low / calc_s_down) ** calc_power
    sell_entry = calc_low + calc_down_val
    sell_sl = sell_entry + 7.0
    sell_tp = sell_entry - 7.0

    # تحديد أين السعر الآن (تنشيط الكروت)
    is_bull_active = False
    is_bear_active = False
    
    if calc_close > 0:
        if calc_close >= buy_entry: is_bull_active = True
        if calc_close <= sell_entry: is_bear_active = True

    # ==========================================
    # 📟 العرض (الكروت والشارت)
    # ==========================================
    
    # كود CSS للكروت النشطة
    cls_buy = "active-buy" if is_bull_active else ""
    cls_sell = "active-sell" if is_bear_active else ""
    
    # عرض التنبيهات
    if is_bull_active: 
        st.markdown(f'<div class="order-alert">🚀 السعر في منطقة الشراء: {buy_entry:.2f}</div>', unsafe_allow_html=True)
    elif is_bear_active:
        st.markdown(f'<div class="order-alert">🔻 السعر في منطقة البيع: {sell_entry:.2f}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f"""<div style="text-align:center; margin-bottom:15px; border:1px dashed #444; padding:10px; border-radius:10px;">منطقة انتظار (داخل النطاق)</div>""", unsafe_allow_html=True)

    # الكروت (Cards)
    c_b, c_s = st.columns(2)
    
    # كروت الشراء
    with c_b: 
        st.markdown(f'<div class="zone-title" style="color:#00FF7F;">منطقة الشراء (Bullish)</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="mini-card buy-box {cls_buy}"><div class="card-title">نقطة الدخول</div><div class="card-value">${buy_entry:,.2f}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="mini-card buy-box {cls_buy}"><div class="card-title" style="color:#FF4444;">وقف الخسارة</div><div class="card-value">${buy_sl:,.2f}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="mini-card buy-box {cls_buy}"><div class="card-title" style="color:#00FF7F;">الهدف</div><div class="card-value">${buy_tp:,.2f}</div></div>', unsafe_allow_html=True)

    # كروت البيع
    with c_s: 
        st.markdown(f'<div class="zone-title" style="color:#FF4444;">منطقة البيع (Bearish)</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="mini-card sell-box {cls_sell}"><div class="card-title">نقطة الدخول</div><div class="card-value">${sell_entry:,.2f}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="mini-card sell-box {cls_sell}"><div class="card-title" style="color:#FF4444;">وقف الخسارة</div><div class="card-value">${sell_sl:,.2f}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="mini-card sell-box {cls_sell}"><div class="card-title" style="color:#00FF7F;">الهدف</div><div class="card-value">${sell_tp:,.2f}</div></div>', unsafe_allow_html=True)

    # الرسم البياني (Chart)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # إعداد الشارت
    fig = go.Figure(data=[go.Candlestick(
        x=df_chart['Date'],
        open=df_chart['Open'],
        high=df_chart['High'],
        low=df_chart['Low'],
        close=df_chart['Close'],
        name="Price"
    )])
    
    # إضافة الخطوط
    fig.add_hline(y=buy_entry, line_dash="dash", line_color="#00FF7F", annotation_text="Buy Entry")
    fig.add_hline(y=sell_entry, line_dash="dash", line_color="#FF4444", annotation_text="Sell Entry")
    
    # تنسيق الشارت
    chart_title = "Manual Calculation Chart" if not use_live_data else "Live Market Chart"
    fig.update_layout(
        height=500, 
        margin=dict(l=10,r=10,t=30,b=10), 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        font=dict(color="#888"), 
        title=chart_title, 
        xaxis_rangeslider_visible=False
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='#2b2f44')
    
    st.plotly_chart(fig, use_container_width=True)

else:
    if not use_live_data:
        st.info("👈 يرجى إدخال **القمة (High)** و **القاع (Low)** في الخانات بالأعلى لبدء الحساب.")

# تذييل بسيط
st.markdown(f"<div style='text-align:center; margin-top:20px; color:#666;'>Developed by Mr.Ali | © 2026</div>", unsafe_allow_html=True)
