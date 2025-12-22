import streamlit as st
from datetime import date, timedelta
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
from plotly import graph_objs as go
import pandas as pd
import wikipedia
import numpy as np 

# วันที่ปัจจุบัน
TODAY = date.today().strftime("%Y-%m-%d")

# ----------------------------------------------------------------------
# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(layout="wide", page_title="Stock Prediction App")

st.markdown(
    """
    <style>
    .centered-title {
        text-align: center;
        font-size: 2.5em;
        font-weight: bold;
        color: #1a1a1a;
        padding-bottom: 20px;
    }
    </style>
    <div class="centered-title">📈 แอปทำนายราคาหุ้นและดัชนี (Daily Forecast)</div>
    """, 
    unsafe_allow_html=True
)

# ----------------------------------------------------------------------
# 2. เลือกหมวดหมู่และเลือกหุ้น

col1, col2 = st.columns(2)

with col1:
    category = st.selectbox("เลือกหมวดหมู่", ["หุ้นสหรัฐฯ", "หุ้นไทย", "กองทุนรวม / ดัชนี"])

# รายชื่อหุ้น
us_stocks = {
    "Apple (AAPL)": "AAPL", "Microsoft (MSFT)": "MSFT", "Google (GOOGL)": "GOOGL",
    "Amazon (AMZN)": "AMZN", "Meta (META)": "META", "Nvidia (NVDA)": "NVDA",
    "Tesla (TSLA)": "TSLA", "UnitedHealth Group (UNH)": "UNH", "Johnson & Johnson (JNJ)": "JNJ",
    "Visa (V)": "V", "JPMorgan Chase (JPM)": "JPM", "Exxon Mobil (XOM)": "XOM",
    "Procter & Gamble (PG)": "PG", "Mastercard (MA)": "MA", "Home Depot (HD)": "HD",
    "Chevron (CVX)": "CVX", "Eli Lilly (LLY)": "LLY", "AbbVie (ABBV)": "ABBV",
    "Merck & Co. (MRK)": "MRK", "Pfizer (PFE)": "PFE", "PepsiCo (PEP)": "PEP",
    "Coca-Cola (KO)": "KO", "Walmart (WMT)": "WMT", "Cisco Systems (CSCO)": "CSCO",
    "Intel (INTC)": "INTC", "Netflix (NFLX)": "NFLX", "Walt Disney (DIS)": "DIS",
    "PayPal (PYPL)": "PYPL", "Boeing (BA)": "BA"
}
thai_stocks = {
    "แอดวานซ์ อินโฟร์ เซอร์วิส (ADVANC)": "ADVANC.BK", "ท่าอากาศยานไทย (AOT)": "AOT.BK",
    "ธนาคารกรุงเทพ (BBL)": "BBL.BK", "กรุงเทพดุสิตเวชการ (BDMS)": "BDMS.BK",
    "ซีพี ออลล์ (CPALL)": "CPALL.BK", "เจริญโภคภัณฑ์อาหาร (CPF)": "CPF.BK",
    "เซ็นทรัล รีเทล (CRC)": "CRC.BK", "เดลต้า อีเลคโทรนิคส์ (DELTA)": "DELTA.BK",
    "พลังงานบริสุทธิ์ (EA)": "EA.BK", "กัลฟ์ เอ็นเนอร์จี (GULF)": "GULF.BK",
    "กสิกรไทย (KBANK)": "KBANK.BK", "พีทีที (PTT)": "PTT.BK",
    "เอสซีจี แพคเกจจิ้ง (SCGP)": "SCGP.BK", "ปูนซิเมนต์ไทย (SCC)": "SCC.BK"
}
funds_indices = {
    "NASDAQ Composite": "^IXIC", "S&P 500": "^GSPC", "Dow Jones Industrial": "^DJI",
    "ARK Innovation ETF": "ARKK", "Vanguard S&P500 ETF (VOO)": "VOO"
}

if category == "หุ้นสหรัฐฯ": stock_options = us_stocks
elif category == "หุ้นไทย": stock_options = thai_stocks
else: stock_options = funds_indices

with col2:
    selected_label = st.selectbox(f"เลือก {category}", list(stock_options.keys()))
    selected_stock = stock_options[selected_label]

# ----------------------------------------------------------------------
# 3. โหลดข้อมูลหุ้น

@st.cache_data
def load_data(ticker, start_date):
    # ใช้ interval="1d"
    data = yf.download(ticker, start_date, TODAY, interval="1d")
    data.reset_index(inplace=True)
    
    # [FIX] Clean Column names & Drop Duplicates
    if len(data.columns) >= 6:
        try:
            # Flatten columns if MultiIndex (common in new yfinance)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            
            # Ensure columns exist and rename
            data = data.iloc[:, :6]
            data.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            
            # [FIX IMPORTANT] ลบข้อมูลวันที่ซ้ำกันออก เพื่อแก้ปัญหา Styler Error
            data = data.drop_duplicates(subset=['Date'])
            
        except Exception as e:
            st.error(f"Error organizing columns: {e}")
            
    return data

# ----------------------------------------------------------------------
# 4. ข้อมูลบริษัท (Wikipedia)
st.subheader("📄 ข้อมูลบริษัท (จาก wikipedia)")

@st.cache_data(ttl=24*3600)
def get_wiki_company_info(label_name):
    wikipedia.set_lang("th")
    clean_name = label_name.split('(')[0].strip()
    search_candidates = [f"{clean_name} (บริษัท)", f"บริษัท {clean_name}", f"{clean_name} Inc.", clean_name]
    
    if "Amazon" in clean_name: search_candidates.insert(0, "อเมซอน.คอม")
    elif "Meta" in clean_name: search_candidates.insert(0, "เมตา แพลตฟอร์มส์")
    elif "Google" in clean_name: search_candidates.insert(0, "กูเกิล")
    elif "PTT" in clean_name: search_candidates.insert(0, "ปตท. (บริษัท)")

    found_summary, found_url = None, None
    for query in search_candidates:
        try:
            page = wikipedia.page(query, auto_suggest=False)
            content_snippet = page.content[:500]
            if any(k in content_snippet for k in ["บริษัท", "Inc", "Corporation", "Holding", "หุ้น", "ธุรกิจ"]):
                found_summary = page.summary[:600] + "..."
                found_url = page.url
                break
        except: continue
    return found_summary, found_url

wiki_summary, wiki_url = get_wiki_company_info(selected_label)
st.markdown(f"### 🏢 {selected_label}")
if wiki_summary:
    st.info(wiki_summary)
    st.markdown(f"🔗 [อ่านฉบับเต็มบน Wikipedia]({wiki_url})")
else:
    st.warning(f"⚠️ ไม่พบข้อมูลบริษัท '{selected_label}' ในฐานข้อมูล Wikipedia ภาษาไทย")

# ----------------------------------------------------------------------
# 5. กราฟราคาย้อนหลัง

st.markdown("---")
st.subheader('📈 กราฟราคาย้อนหลัง (Daily Price Chart)')

start_date = st.date_input(
    'เลือกวันที่เริ่มต้น:', value=date(2018, 1, 1), 
    min_value=date.today() - timedelta(days=365*10), 
    max_value=date.today() - timedelta(days=30)
)

data_load_state = st.info('📥 กำลังดาวน์โหลดข้อมูลราคารายวันย้อนหลัง...')
data = load_data(selected_stock, start_date.strftime("%Y-%m-%d"))
data_load_state.empty()

# ฟังก์ชัน Plot Graph
def plot_chart(df, label, chart_type):
    fig = go.Figure()
    if chart_type == 'Candlestick':
        fig.add_trace(go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']))
    else:
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], mode='lines', name='Close', line=dict(color='#3498db'), fill='tozeroy'))
    
    fig.update_layout(title=f'ราคา {label} ({chart_type})', height=600, xaxis_rangeslider_visible=True)
    st.plotly_chart(fig, use_container_width=True)

# เช็คว่ามีข้อมูลหรือไม่
if not data.empty and len(data) > 0:
    c_type = st.radio("ประเภทกราฟ:", ('Candlestick', 'Line Chart'), horizontal=True)
    plot_chart(data, selected_label, c_type)
    
    st.subheader('ตารางข้อมูลราคาย้อนหลัง (Daily)')
    # [FIX] ใช้ drop_duplicates ก่อน set_index เพื่อแก้ Styler Error
    display_data = data.tail(10).drop_duplicates(subset=['Date']).set_index('Date')
    st.dataframe(display_data.style.format('{:.2f}'), use_container_width=True)

    # ----------------------------------------------------------------------
    # 6. ตั้งค่าทำนาย
    st.markdown("---")
    st.markdown("## 🔮 ส่วนการทำนายราคาในอนาคต (3 เดือน - รายวัน)")
    st.markdown("---")

    n_days = 90
    
    col_pred_select, col_pred_info = st.columns([1, 2])
    with col_pred_select:
        st.metric("ระยะเวลาทำนาย", f"{n_days} วัน")
    with col_pred_info:
        st.info(f"ระบบจะใช้ข้อมูล**รายวัน (Daily)** เพื่อสร้างแบบจำลองที่ละเอียดขึ้น (รวมวันหยุดและ Weekly Seasonality) และคาดการณ์ไปอีก **{n_days} วัน** ข้างหน้า")

    # ----------------------------------------------------------------------
    # 7. กราฟทำนาย (Prophet)
    
    df_train = data[['Date', 'Close']].rename(columns={"Date": "ds", "Close": "y"})
    
    # [FIX] เริ่ม Try Block ตรงนี้เพื่อให้ครอบคลุมทั้งหมด
    try:
        m = Prophet()
        
        # ใส่ Holiday
        if category == "หุ้นสหรัฐฯ" or category == "กองทุนรวม / ดัชนี":
            m.add_country_holidays(country_name='US')
        elif category == "หุ้นไทย":
            m.add_country_holidays(country_name='TH')

        with st.spinner('🤖 กำลังเทรนโมเดล Prophet... (กรุณารอสักครู่)'):
            m.fit(df_train)

        # ส่วนแสดงสถานะ
        if m.country_holidays is not None:
            detected_holidays = m.train_holiday_names.unique()
            st.success(f"🎉 โมเดลเปิดใช้งาน h(t) สมบูรณ์แบบ! (Data ตรงวันหยุดจริง) - ใช้ปฏิทิน: {m.country_holidays}")
        else:
            st.warning("⚠️ ไม่ได้เปิดใช้งานโหมดวันหยุด")

        st.markdown("### 🛠️ เครื่องมือตรวจสอบโมเดล (Model Inspection)")
        with st.expander("คลิกเพื่อดูข้อมูลภายใน Model (Holidays, Changepoints, Dict)"):
            if m.country_holidays is not None:
                st.markdown("#### 📅 1. วันหยุดที่นำมาคำนวณ (Holidays)")
                st.write(detected_holidays)
                st.markdown("---")
            
            st.markdown("#### 📉 2. จุดเปลี่ยนเทรนด์ (Changepoints)")
            st.caption("ตารางแสดงวันที่กราฟมีการ 'หักมุม' พร้อมราคา ณ วันนั้น และทิศทางที่เปลี่ยนไป")
            
            # --- [FIXED SECTION START] ---
            
            # 1. สร้าง DataFrame ของ Changepoints
            df_cp = pd.DataFrame({
                'Date': m.changepoints,
                'Delta': m.params['delta'][0]
            })
            
            # 2. เตรียมข้อมูลราคาจาก history
            history_df = m.history[['ds', 'y']].copy()
            
            # 3. Merge ข้อมูล
            df_cp = pd.merge(df_cp, history_df, left_on='Date', right_on='ds', how='left')
            
            # 4. จัดการคอลัมน์
            df_cp = df_cp.rename(columns={'y': 'Price'})
            df_cp = df_cp[['Date', 'Price', 'Delta']] 
            
            # [CRITICAL FIX] ล้างค่าซ้ำและรีเซ็ต Index เพื่อแก้ Styler Error
            df_cp = df_cp.drop_duplicates(subset=['Date']).reset_index(drop=True)
            
            # สร้างฟังก์ชันใส่สี
            def highlight_delta(val):
                color = '#2ecc71' if val >= 0 else '#e74c3c'
                return f'color: {color}; font-weight: bold'

            # 5. แสดงผล 10 จุดล่าสุด
            st.write("showing last 10 changepoints:")
            st.dataframe(
                df_cp.tail(10).style
                .map(highlight_delta, subset=['Delta'])
                .format({'Price': '{:.2f}', 'Delta': '{:+.4f}'}),
                use_container_width=True
            )
            
            # [FIX] เปลี่ยนจาก st.info เป็น st.markdown เพื่อแก้ Error: AlertMixin
            st.markdown("""
            <div style="padding: 10px; border-radius: 5px; background-color: #f0f2f6; border-left: 5px solid #31333F;">
            <ul>
                <li><b>Price:</b> ราคาหุ้น ณ วันที่เกิดจุดเปลี่ยน</li>
                <li><b>Delta:</b> ความแรงของการเปลี่ยนทิศทาง
                    <ul>
                        <li><span style='color:#2ecc71'><b>สีเขียว (+)</b></span> : กราฟหักหัว <b>ขึ้น</b> (ชันขึ้น หรือ ลงน้อยลง)</li>
                        <li><span style='color:#e74c3c'><b>สีแดง (-)</b></span> : กราฟหักหัว <b>ลง</b> (ขึ้นน้อยลง หรือ ดิ่งลง)</li>
                    </ul>
                </li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # --- [FIXED SECTION END] ---

            # --- [NEW SECTION: MODEL DICT] ---
            st.markdown("---")
            st.markdown("#### ⚙️ 3. พารามิเตอร์ของโมเดล (Trained Model Dict)")
            st.caption("นี่คือค่าสัมประสิทธิ์ (Coefficient) จริงที่ Prophet คำนวณได้และเก็บไว้ใน `m.params`")

            # เตรียมข้อมูล Dictionary แบบสรุป (Scalar values)
            params_summary = {
                "growth (สูตรที่ใช้)": m.growth,
                "k (Base Growth Rate)": float(m.params['k'][0][0]),
                "m (Offset)": float(m.params['m'][0][0]),
                "sigma_obs (Noise Variance)": float(m.params['sigma_obs'][0][0]),
                "delta_length (จำนวนจุดเปลี่ยน)": m.params['delta'].shape[1],
                "beta_length (จำนวน Seasonality+Holiday)": m.params['beta'].shape[1]
            }
            
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.markdown("**Summary (สรุปค่าหลัก):**")
                st.json(params_summary)
            with col_d2:
                st.markdown("**Keys ทั้งหมดใน `m.params`:**")
                st.write(list(m.params.keys()))
                st.markdown("**Component Modes:**")
                st.write(m.component_modes)

            with st.popover("📂 คลิกเพื่อดูข้อมูล Raw Dict ทั้งหมด (JSON)"):
                st.write("หมายเหตุ: ข้อมูลนี้คือค่าดิบทั้งหมดรวมถึง Array ขนาดใหญ่ (delta, beta)")
                # แปลง Numpy เป็น List เพื่อให้แสดงผลผ่าน st.json ได้
                def convert_to_serializable(obj):
                    if isinstance(obj, np.ndarray):
                        return obj.tolist()
                    return obj
                
                # สร้าง Dict ใหม่สำหรับการแสดงผล
                safe_params = {k: convert_to_serializable(v) for k, v in m.params.items()}
                st.json(safe_params)
            
            st.markdown("---")
            # --- [INSERT THIS CODE: SEASONALITY CHECK] ---
            st.markdown("---")
            st.markdown("#### 🌊 4. ตรวจสอบค่า P (Seasonality Configuration)")
            st.caption("เช็คว่าโมเดลเปิดใช้งาน Seasonality ตัวไหนบ้าง และใช้ค่า P เท่าไหร่ (ดึงจาก `m.seasonalities`)")

            # ดึงข้อมูลจาก m.seasonalities มาจัดรูปแบบลงตาราง
            season_config = []
            for name, props in m.seasonalities.items():
                season_config.append({
                    "Component Name": name,
                    "Period (P)": f"{props['period']:.2f} days",
                    "Fourier Order (N)": props['fourier_order'],
                    "Prior Scale": props['prior_scale'],
                    "Mode": props['mode']
                })
            
            st.table(pd.DataFrame(season_config))
            
            st.success("""
            **ความหมาย:**
            * **weekly:** $P=7$ คือดูพฤติกรรม จันทร์-ศุกร์ (ใช้ $N=3$ ตามมาตรฐาน)
            * **yearly:** $P=365.25$ คือดูพฤติกรรมรายปี/ฤดูกาล (ใช้ $N=10$ เพื่อเก็บรายละเอียดได้เยอะกว่า)
            """)
            # --- [END INSERT CODE] ---

        # สร้าง Future Dataframe
        future = m.make_future_dataframe(periods=n_days, freq='D') 
        forecast = m.predict(future)

        st.subheader(f'ผลลัพธ์การคาดการณ์ 90 วันข้างหน้า ({selected_label})') 
        
        st.markdown("#### ตารางผลการคาดการณ์ (10 วันล่าสุด)")
        forecast_display = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(10)
        st.dataframe(forecast_display.style.format({'yhat': '{:.2f}', 'yhat_lower': '{:.2f}', 'yhat_upper': '{:.2f}'}), use_container_width=True)

        st.markdown(f'#### กราฟคาดการณ์ (รวมวันหยุดและ Weekly Seasonality)') 
        fig1 = plot_plotly(m, forecast)
        st.plotly_chart(fig1, use_container_width=True)

        st.markdown("#### องค์ประกอบการคาดการณ์ (Components)")
        st.caption("สังเกต: ตอนนี้จะมี Weekly Seasonality (รายสัปดาห์) เพิ่มขึ้นมา เพราะเราใช้ข้อมูลรายวันแล้ว")
        fig2 = m.plot_components(forecast)
        st.write(fig2)

        # ----------------------------------------------------------------------
        # 8. ส่วนอธิบายสมการ
        st.markdown("---")
        st.markdown("### 🧮 เบื้องหลังการคำนวณ: สมการ Prophet")
            
        with st.expander("คลิกเพื่อดูคำอธิบายสูตรคณิตศาสตร์"):
            st.latex(r"y(t) = g(t) + s(t) + h(t) + \epsilon_t")

            st.markdown("#### 1. $g(t)$: แนวโน้มหลัก (Trend)")
            st.latex(r"g(t) = (k + a(t)^T \delta)t + (m + a(t)^T \gamma)")

            st.markdown("#### 2. $s(t)$: ฤดูกาล (Seasonality)")
            st.info("💡 Update: เมื่อใช้ข้อมูลรายวัน (Daily) โมเดลจะคำนวณ **Weekly Seasonality** ($P=7$) เพิ่มให้ด้วย")
            st.latex(r"s(t) = \sum_{n=1}^N \left( a_n \cos\left(\frac{2\pi n t}{P}\right) + b_n \sin\left(\frac{2\pi n t}{P}\right) \right)")
            st.markdown("""
            * **Yearly Seasonality:** $P = 365.25$ (วนรอบทุก 1 ปี)
            * **Weekly Seasonality:** $P = 7$ (วนรอบทุก 7 วัน - ดูพฤติกรรม จันทร์-ศุกร์)
            """)

            st.markdown("#### 3. $h(t)$: วันหยุด (Holidays)")
            st.success("✅ สถานะ: ทำงานสมบูรณ์แบบ (ข้อมูลรายวันทำให้ระบุวันหยุดได้ตรงวัน)")
            st.latex(r"h(t) = \sum_{i} \kappa_i \cdot 1_{\{t \in D_i\}}")

            st.markdown("#### 4. $\epsilon_t$: Noise")
            st.latex(r"\epsilon_t \sim \text{Normal}(0, \sigma^2)")

        # ----------------------------------------------------------------------
        # 9. ส่วนเจาะลึก (Deep Dive) - [NEW LOGIC]
        st.markdown("---")
        st.markdown(f"### 🔍 เจาะลึก: ลองแทนค่าจริงจากข้อมูลของ {selected_label}")

        with st.expander("คลิกเพื่อดูการแทนค่าตัวเลขจริง (Real Numbers Substitution)", expanded=False):
            
            # --- [NEW LOGIC] ค้นหาวันหยุดมาแสดงเป็นตัวอย่าง ---
            # ค่าเริ่มต้น: เอาวันสุดท้ายของการทำนาย
            target_row = forecast.tail(1).iloc[0]
            example_source = "วันสุดท้ายของการทำนาย (Last Forecast Day)"
            
            # ตรวจสอบว่ามีคอลัมน์ holidays และมีวันไหนที่ไม่ใช่ 0 ไหม
            if 'holidays' in forecast.columns:
                holiday_days = forecast[forecast['holidays'].abs() > 0] # หาแถวที่มีค่า holiday (ทั้งบวกและลบ)
                
                if not holiday_days.empty:
                    # ถ้าเจอวันหยุด ให้เลือก "วันหยุดล่าสุด" (ที่อยู่ในอนาคตหรือท้ายตาราง) มาแสดง
                    target_row = holiday_days.iloc[-1]
                    date_str = target_row['ds'].strftime("%Y-%m-%d")
                    st.info(f"💡 ระบบเลือกแสดงตัวอย่างวันที่ **{date_str}** โดยอัตโนมัติ เนื่องจากเป็น **วันหยุด (Holiday)** เพื่อให้เห็นการทำงานของค่า $h(t)$ ได้ชัดเจนครับ")
                else:
                    st.write(f"**ตัวอย่าง: การคำนวณราคาของวันที่ {target_row['ds'].strftime('%Y-%m-%d')}** ({example_source})")
            else:
                    st.write(f"**ตัวอย่าง: การคำนวณราคาของวันที่ {target_row['ds'].strftime('%Y-%m-%d')}** ({example_source})")

            # ---------------------------------------------------------
            # 1. ดึงข้อมูลจาก Row ที่เลือก (Target Row)
            last_date = target_row['ds'].strftime("%Y-%m-%d")
            
            # ดึงค่าองค์ประกอบย่อย
            val_trend = target_row['trend']
            val_seasonality = target_row['additive_terms'] if 'additive_terms' in target_row else 0.0
            
            # ดึงค่า Holiday (ถ้ามี)
            val_holiday = 0.0
            if 'holidays' in target_row:
                val_holiday = target_row['holidays']
            
            # ดึง Parameter ภายใน (Internal Scale)
            params = m.params
            k = params['k'][0][0]           # ความชัน (Slope)
            m_offset = params['m'][0][0]    # จุดตัดแกน (Offset)
            sigma = params['sigma_obs'][0][0] # Noise
            
            # จัดการ Array ให้แสดงผลสวยงาม
            deltas = params['delta'][0]
            betas = params['beta'][0]

            def format_array_preview(arr, n=5):
                preview = [f"{x:.6f}" for x in arr[:n]]
                return f"[ {', '.join(preview)}, ... ] (มีทั้งหมด {len(arr)} ตัว)"

            deltas_str = format_array_preview(deltas)
            betas_str = format_array_preview(betas)

            # 2. ส่วนแสดงผลลัพธ์สุดท้าย (The Summation)
            
            st.markdown("#### 1. ผลรวมองค์ประกอบ (The Summation)")
            st.caption("นำค่าที่โมเดลคำนวณได้แต่ละส่วนมารวมกัน:")
            
            # แบ่งเป็น 5 คอลัมน์ (Trend + Season + Holiday + Noise = Result)
            c1, c2, c3, c4, c5 = st.columns(5)
            
            with c1:
                st.metric("1. Trend g(t)", f"{val_trend:.2f}")
            with c2:
                # เพื่อไม่ให้ซ้ำซ้อน เราจะลบ holiday ออกจาก additive_terms เพื่อโชว์แยก
                season_only = val_seasonality - val_holiday
                st.metric("2. Season s(t)", f"{season_only:.2f}")
            with c3:
                # ถ้า val_holiday ไม่ใช่ 0 ให้โชว์สีเด่นๆ
                h_delta_color = "normal"
                if val_holiday > 0: h_delta_color = "normal"
                elif val_holiday < 0: h_delta_color = "inverse"
                
                st.metric("3. Holiday h(t)", f"{val_holiday:.2f}", delta_color="off")
            with c4:
                st.metric("4. Noise (0)", "0.00")
            with c5:
                st.metric("= Prediction y(t)", f"{target_row['yhat']:.2f}", delta_color="off")   
            
            # แสดงสมการบรรทัดเดียว
            st.markdown(r"$$y(t) = g(t) + s(t) + h(t) + \epsilon_t$$")

            st.latex(rf"""
            y({last_date}) \approx 
            \underbrace{{{val_trend:.2f}}}_{{Trend}} + 
            \underbrace{{({season_only:.2f})}}_{{Seasonality}} + 
            \underbrace{{({val_holiday:.2f})}}_{{Holiday}} + 
            0 = 
            \mathbf{{{target_row['yhat']:.2f}}}
            """)
            
            if val_holiday == 0:
                st.caption(f"*หมายเหตุ: ค่า Holiday เป็น 0.00 แสดงว่าวันที่ {last_date} ไม่ตรงกับวันหยุดพิเศษใดๆ*")
            else:
                st.success(f"✨ **Highlight:** วันนี้ ({last_date}) มีผลกระทบจากวันหยุด ทำให้ราคาเปลี่ยนไป **{val_holiday:.2f}** บาท")

            st.markdown("---")

            # 3. ส่วนแสดงเครื่องยนต์ข้างใน (The Engine)
            st.markdown("#### 2. ค่าสัมประสิทธิ์เบื้องหลัง (Parameters form `model.params`)")
            st.warning("⚠️ ค่าเหล่านี้เป็นค่าภายใน (Internal Scale) ก่อนถูกแปลงเป็นบาท")

            # --- ส่วน Trend ---
            st.markdown("**ส่วน Trend ($g(t)$):**")
            st.code(f"k (Slope) = {k:.6f}, m (Offset) = {m_offset:.6f}\ndelta (Changes) = {deltas_str}")

            # --- ส่วน Seasonality & Holiday ---
            st.markdown("**ส่วน Seasonality ($s(t)$) และ Holiday ($h(t)$):**")
            st.text("ค่า beta จะเก็บน้ำหนักของทั้ง Seasonality (Fourier) และ Holiday (Indicators) รวมกัน")
            st.code(f"beta (Coefficients) = {betas_str}")
            
            if m.country_holidays is not None:
                st.caption(f"เนื่องจากเปิดใช้งาน Holiday: ค่า beta บางตัวในนี้คือค่าความแรง (Kappa) ของวันหยุด {list(m.train_holiday_names.unique())}")

    # [FIX] Except block ต้องอยู่ตรงนี้ และ Indent ให้ตรงกับ Try ด้านบนสุด
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการเทรนโมเดล Prophet: {str(e)}")
        st.write("ลองเปลี่ยนหุ้น หรือช่วงเวลาวันที่ แล้วกด Refresh")