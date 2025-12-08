import streamlit as st
from datetime import date, timedelta
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
from plotly import graph_objs as go
from googletrans import Translator
import pandas as pd

# วันที่
TODAY = date.today().strftime("%Y-%m-%d")

# ----------------------------------------------------------------------
# 1. จัดชื่อเว็บแอปให้อยู่ตรงกลาง
st.set_page_config(layout="wide")

# ใช้ st.markdown และ HTML/CSS เพื่อจัดกึ่งกลางชื่อ
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
    <div class="centered-title">📈 แอปทำนายราคาหุ้นและดัชนี พร้อมข้อมูลบริษัท (ภาษาไทย)</div>
    """, 
    unsafe_allow_html=True
)

# ----------------------------------------------------------------------
# 2. เลือกหมวดหมู่และเลือกหุ้น (ปกติ)

col1, col2 = st.columns(2)

with col1:
    category = st.selectbox("เลือกหมวดหมู่", ["หุ้นสหรัฐฯ", "หุ้นไทย", "กองทุนรวม / ดัชนี"])

# รายชื่อหุ้นแต่ละหมวด
us_stocks = {
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "Google (GOOGL)": "GOOGL",
    "Amazon (AMZN)": "AMZN",
    "Meta (META)": "META",
    "Nvidia (NVDA)": "NVDA",
    "Tesla (TSLA)": "TSLA",
    "UnitedHealth Group (UNH)": "UNH",
    "Johnson & Johnson (JNJ)": "JNJ",
    "Visa (V)": "V",
    "JPMorgan Chase (JPM)": "JPM",
    "Exxon Mobil (XOM)": "XOM",
    "Procter & Gamble (PG)": "PG",
    "Mastercard (MA)": "MA",
    "Home Depot (HD)": "HD",
    "Chevron (CVX)": "CVX",
    "Eli Lilly (LLY)": "LLY",
    "AbbVie (ABBV)": "ABBV",
    "Merck & Co. (MRK)": "MRK",
    "Pfizer (PFE)": "PFE",
    "PepsiCo (PEP)": "PEP",
    "Coca-Cola (KO)": "KO",
    "Walmart (WMT)": "WMT",
    "Cisco Systems (CSCO)": "CSCO",
    "Intel (INTC)": "INTC",
    "Comcast (CMCSA)": "CMCSA",
    "Adobe (ADBE)": "ADBE",
    "Netflix (NFLX)": "NFLX",
    "Salesforce (CRM)": "CRM",
    "Thermo Fisher Scientific (TMO)": "TMO",
    "Broadcom (AVGO)": "AVGO",
    "Abbott Laboratories (ABT)": "ABT",
    "Verizon Communications (VZ)": "VZ",
    "Walt Disney (DIS)": "DIS",
    "Accenture (ACN)": "ACN",
    "PayPal Holdings (PYPL)": "PYPL",
    "Texas Instruments (TXN)": "TXN",
    "Qualcomm (QCOM)": "QCOM",
    "Oracle (ORCL)": "ORCL",
    "Bristol-Myers Squibb (BMY)": "BMY",
    "Amgen (AMGN)": "AMGN",
    "Union Pacific (UNP)": "UNP",
    "NextEra Energy (NEE)": "NEE",
    "Honeywell International (HON)": "HON",
    "Lockheed Martin (LMT)": "LMT",
    "General Electric (GE)": "GE",
    "3M Company (MMM)": "MMM",
    "Boeing (BA)": "BA",
    "Citigroup (C)": "C",
    "KLA Corporation (KLAC)": "KLAC",
    "Nasdaq Inc (NDAQ)": "NDAQ"
}

thai_stocks = {
    "แอดวานซ์ อินโฟร์ เซอร์วิส (ADVANC)": "ADVANC.BK",
    "แอสเสท เวิรด์ คอร์ป (AWC)": "AWC.BK",
    "เอเซีย พลัส กรุ๊ป โฮลดิ้งส์ (ASPS)": "ASPS.BK",
    "บางจาก คอร์ปอเรชั่น (BCP)": "BCP.BK",
    "แบงก์ ออฟ อายุตยธยา (BAY)": "BAY.BK",
    "ธนาคารกรุงเทพ (BBL)": "BBL.BK",
    "บีทีเอส กรุ๊ป โฮลดิ้งส์ (BTS)": "BTS.BK",
    "กรุงเทพดุสิตเวชการ (BDMS)": "BDMS.BK",
    "เบอร์ลี่ ยุคเกอร์ (BJC)": "BJC.BK",
    "บางกอก เชน ฮอสปิทอล (BCH)": "BCH.BK",
    "ซีพี ออลล์ (CPALL)": "CPALL.BK",
    "เจริญโภคภัณฑ์อาหาร (CPF)": "CPF.BK",
    "ไชน่า โมบายล์ อินเตอร์เนชั่นแนล (CHG)": "CHG.BK",
    "เดลต้า อีเลคโทรนิคส์ (DELTA)": "DELTA.BK",
    "ดูโฮม (DOHOME)": "DOHOME.BK",
    "อีเอสเอสโอ (ESSO)": "ESSO.BK",
    "พลังงานบริสุทธิ์ (EA)": "EA.BK",
    "โกลบอล เพาเวอร์ ซินเนอร์ยี่ (GPSC)": "GPSC.BK",
    "กัลฟ์ เอ็นเนอร์จี ดีเวลลอปเมนท์ (GULF)": "GULF.BK",
    "ไออาร์พีซี (IRPC)": "IRPC.BK",
    "อินทัช โฮลดิ้งส์ (INTUCH)": "INTUCH.BK",
    "ไทยออยล์ (TOP)": "TOP.BK",
    "ท่าอากาศยานไทย (AOT)": "AOT.BK",
    "การบินไทย (THAI)": "THAI.BK",
    "บ้านปู (BANPU)": "BANPU.BK",
    "คาราบาวกรุ๊ป (CBG)": "CBG.BK",
    "คิวอาร์ที (KCE)": "KCE.BK",
    "แลนด์แอนด์เฮ้าส์ (LH)": "LH.BK",
    "มิตซุย ซูมิโตโม อินชัวรันซ์ (MEGA)": "MEGA.BK",
    "เมืองไทย แคปปิตอล (MTC)": "MTC.BK",
    "เนชั่นแนล เพาเวอร์ ซัพพลาย (NPS)": "NPS.BK",
    "โอเอสพี (OSP)": "OSP.BK",
    "พีทีที (PTT)": "PTT.BK",
    "พีทีที โกลบอล เคมิคอล (PTTGC)": "PTTGC.BK",
    "ราช กรุ๊ป (RATCH)": "RATCH.BK",
    "แสนสิริ (SIRI)": "SIRI.BK",
    "ศรีอยุธยา แคปปิตอล (SCB)": "SCB.BK",
    "เอสซีจี แพคเกจจิ้ง (SCGP)": "SCGP.BK",
    "เซ็นทรัล รีเทล คอร์ปอเรชั่น (CRC)": "CRC.BK",
    "ไทยเบฟเวอเรจ (THBEV)": "THBEV.BK",
    "ไทยยูเนี่ยน กรุ๊ป (TU)": "TU.BK",
    "ทีโอที ดิจิทัล เซอร์วิส (TTB)": "TTB.BK",
    "ทรู คอร์ปอเรชั่น (TRUE)": "TRUE.BK",
    "ทริพเพิล ไอ โลจิสติกส์ (III)": "III.BK",
    "แอลพีเอ็น ดีเวลลอปเมนท์ (LPN)": "LPN.BK",
    "เวิร์ลด์ รีจินอล เจเนอเรชั่น (WHA)": "WHA.BK",
    "โรงพยาบาลบำรุงราษฎร์ (BH)": "BH.BK",
    "ไทยพาณิชย์ (SCB)": "SCB.BK",
    "เจ มาร์ท (JMART)": "JMART.BK"
}

funds_indices = {
    "NASDAQ Composite": "^IXIC",
    "S&P 500": "^GSPC",
    "Dow Jones Industrial": "^DJI",
    "ARK Innovation ETF": "ARKK",
    "Vanguard S&P500 ETF (VOO)": "VOO",
    "SET50 Index (SET50)": "^SET.BK"
}


# เลือกรายการตามหมวด
if category == "หุ้นสหรัฐฯ":
    stock_options = us_stocks
elif category == "หุ้นไทย":
    stock_options = thai_stocks
else:
    stock_options = funds_indices

with col2:
    selected_label = st.selectbox(f"เลือก {category}", list(stock_options.keys()))
    selected_stock = stock_options[selected_label]

# ตัวแปรสำหรับฟังก์ชัน load_data
START_DEFAULT = "2015-01-01"

# โหลดข้อมูลหุ้น
@st.cache_data
def load_data(ticker, start_date):
    # แก้ไข: ดึงข้อมูลแบบรายสัปดาห์ (Weekly interval)
    data = yf.download(ticker, start_date, TODAY, interval="1wk")
    data.reset_index(inplace=True)
    
    # แก้ไขปัญหา ValueError: length mismatch
    if len(data.columns) == 7:
        data.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    elif len(data.columns) == 6:
        data.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        data['Adj Close'] = data['Close'] # ใช้ Close แทน Adj Close สำหรับดัชนี/กองทุน
    else:
        st.error(f"⚠️ โหลดข้อมูลล้มเหลว: จำนวนคอลัมน์ที่ได้รับ ({len(data.columns)}) ไม่ถูกต้อง")

    return data

# ----------------------------------------------------------------------
# 3. ข้อมูลบริษัท

st.subheader("📄 ข้อมูลบริษัท (จาก Yahoo Finance)")

# เก็บ cache การแปลใน session_state
if "translated_cache" not in st.session_state:
    st.session_state.translated_cache = {}

try:
    ticker_info = yf.Ticker(selected_stock).info
    long_name = ticker_info.get('longName', selected_label)
    industry = ticker_info.get('industry', 'ไม่มีข้อมูล')
    sector = ticker_info.get('sector', 'ไม่มีข้อมูล')
    website = ticker_info.get('website', '')
    city = ticker_info.get('city', '')
    country = ticker_info.get('country', '')
    summary_en = ticker_info.get('longBusinessSummary', 'ไม่มีข้อมูล')

    # ถ้ามีการแปลเก็บไว้ใน cache แล้ว ให้ใช้เลย
    if selected_stock in st.session_state.translated_cache:
        summary_th = st.session_state.translated_cache[selected_stock]
    else:
        # ฟังก์ชันช่วยแปลอย่างปลอดภัย (แบ่งเป็นช่วง ๆ)
        from googletrans import Translator
        import time

        def safe_translate(text, translator, max_chunk=4500):
            parts = []
            while len(text) > 0:
                chunk = text[:max_chunk]
                text = text[max_chunk:]
                try:
                    translated = translator.translate(chunk, src='en', dest='th').text
                    parts.append(translated)
                    time.sleep(0.8)  # หน่วงเล็กน้อยป้องกันโดนแบน
                except Exception:
                    parts.append("(ไม่สามารถแปลบางส่วนได้)")
                    time.sleep(1.5)
            return " ".join(parts)

        try:
            translator = Translator()
            summary_th = safe_translate(summary_en, translator)
            st.session_state.translated_cache[selected_stock] = summary_th
        except Exception as e:
            summary_th = f"⚠️ ไม่สามารถแปลได้ ({e})"

    # ---------------- แสดงผล ----------------
    st.markdown(f"### 🏢 {long_name}")
    st.markdown(f"**อุตสาหกรรม:** {industry} | **ภาคธุรกิจ:** {sector}")
    st.markdown(f"**ที่ตั้ง:** {city}, {country}")
    st.markdown(f"**เว็บไซต์:** [{website}]({website})" if website else "**เว็บไซต์:** ไม่มีข้อมูล")

    st.markdown("### 📘 สรุปธุรกิจ (ภาษาไทย)")
    st.markdown(summary_th)

except Exception as e:
    st.warning(f"⚠️ ไม่สามารถโหลดหรือแสดงข้อมูลบริษัทของ {selected_label} ได้ ({e})")
# ----------------------------------------------------------------------
# 4. กราฟราคาย้อนหลัง พร้อมตัวเลือกเดือน/ปี

st.markdown("---")
st.subheader('📈 กราฟราคาย้อนหลัง (Weekly Price Chart)') # แก้ไขหัวข้อ

# ตัวเลือกกำหนดช่วงเวลาเริ่มต้น
start_date_limit = date.today() - timedelta(days=365 * 10) # ย้อนหลังได้สูงสุด 10 ปี
start_date = st.date_input(
    'เลือกวันที่เริ่มต้นสำหรับการแสดงกราฟราคาย้อนหลัง:',
    value=date(2018, 1, 1), # ค่าเริ่มต้นที่ดูสมเหตุสมผล
    min_value=start_date_limit,
    max_value=date.today() - timedelta(days=30) # ต้องมีข้อมูลอย่างน้อย 1 เดือน
)

# โหลดข้อมูลตามช่วงวันที่เลือก
data_load_state = st.info('📥 กำลังดาวน์โหลดข้อมูลราคารายสัปดาห์ย้อนหลัง...') # แก้ไขข้อความ
data = load_data(selected_stock, start_date.strftime("%Y-%m-%d"))
data_load_state.empty()

# ฟังก์ชันแสดงกราฟแท่งเทียน (Candlestick Chart)
def plot_candlestick_chart(df, label):
    fig = go.Figure(data=[go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        increasing_line_color='#2ecc71', # สีเขียว (ราคาขึ้น)
        decreasing_line_color='#e74c3c' # สีแดง (ราคาลง)
    )])
    
    fig.update_layout(
        title=f'กราฟแท่งเทียนราคาย้อนหลังรายสัปดาห์ของ {label} (ตั้งแต่วันที่ {start_date.strftime("%Y-%m-%d")})',
        xaxis_title='วันที่ (สัปดาห์)', # แก้ไขชื่อแกน
        yaxis_title='ราคา',
        xaxis_rangeslider_visible=True, 
        template='plotly_white',
        hovermode='x unified',
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)

# ฟังก์ชันแสดงกราฟเส้น (Line Chart)
def plot_line_chart(df, label):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Close'],
        mode='lines',
        name='ราคาปิด (Close)',
        line=dict(color='#3498db', width=2),
        fill='tozeroy', 
        fillcolor='rgba(52, 152, 219, 0.2)' 
    ))

    fig.update_layout(
        title=f'กราฟเส้นราคาปิดย้อนหลังรายสัปดาห์ของ {label} (ตั้งแต่วันที่ {start_date.strftime("%Y-%m-%d")})',
        xaxis_title='วันที่ (สัปดาห์)', # แก้ไขชื่อแกน
        yaxis_title='ราคา',
        xaxis_rangeslider_visible=True, 
        template='plotly_white',
        hovermode='x unified',
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)


if not data.empty:
    chart_type = st.radio(
        "เลือกประเภทกราฟ:",
        ('Candlestick Chart (แนะนำ)', 'Line Chart (ราคาปิด)'),
        horizontal=True
    )
    
    if chart_type == 'Candlestick Chart (แนะนำ)':
        plot_candlestick_chart(data, selected_label)
    else:
        plot_line_chart(data, selected_label)

    # ----------------------------------------------------------------------
    # 5. ตารางราคาย้อนหลัง

    st.subheader('ตารางข้อมูลราคาย้อนหลังรายสัปดาห์ (Raw Data)') # แก้ไขหัวข้อ
    st.dataframe(data.tail(20).set_index('Date').style.format('{:.2f}'), use_container_width=True)

    # ----------------------------------------------------------------------
    # 6. เลือกจำนวนปีที่ต้องการทำนาย (พร้อมหัวข้อเด่นชัด) - แก้ไขให้เป็น 1 ปี

    st.markdown("---")
    st.markdown("## 🔮 ส่วนการทำนายราคาในอนาคต (1 ปี ด้วยข้อมูลรายสัปดาห์)")
    st.markdown("---")

    # กำหนดค่าทำนายคงที่ 1 ปี
    n_years = 1 
    period_weeks = 52 # 52 สัปดาห์สำหรับ 1 ปี
    period = period_weeks 
    
    col_pred_select, col_pred_info = st.columns([1, 2])

    with col_pred_select:
        st.metric("ระยะเวลาทำนายที่กำหนด", f"{n_years} ปี ({period} สัปดาห์)")
        
    with col_pred_info:
        st.info(f"ระบบจะใช้ข้อมูล**รายสัปดาห์ (Weekly)** ตั้งแต่ **ปี {data['Date'].min().year}** ถึง **ปัจจุบัน** เพื่อสร้างแบบจำลองและคาดการณ์ราคาไปอีก **1 ปี** ข้างหน้าโดยอัตโนมัติ")

    # ----------------------------------------------------------------------
    # 7. กราฟทำนาย

    # เตรียมข้อมูลสำหรับ Prophet
    df_train = data[['Date', 'Close']].rename(columns={"Date": "ds", "Close": "y"})
    
    # Train Model
    try:
        m = Prophet()
        m.fit(df_train)
        future = m.make_future_dataframe(periods=period, freq='W') # กำหนดความถี่เป็นสัปดาห์
        forecast = m.predict(future)

        # แสดงผลการทำนาย
        st.subheader(f'ผลลัพธ์การคาดการณ์ราคา 1 ปีของ {selected_label}') # แก้ไขหัวข้อ
        
        # ตารางผลการทำนาย
        st.markdown("#### ตารางผลการคาดการณ์ (10 แถวล่าสุด)")
        forecast_display = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(10)
        forecast_display.columns = ['วันที่ (สิ้นสัปดาห์)', 'ราคาคาดการณ์ (yhat)', 'ช่วงต่ำสุด (Lower)', 'ช่วงสูงสุด (Upper)'] # แก้ไขชื่อคอลัมน์
        st.dataframe(forecast_display.set_index('วันที่ (สิ้นสัปดาห์)').style.format({'ราคาคาดการณ์ (yhat)': '{:.2f}', 'ช่วงต่ำสุด (Lower)': '{:.2f}', 'ช่วงสูงสุด (Upper)': '{:.2f}'}), use_container_width=True)

        # กราฟคาดการณ์
        st.markdown(f'#### กราฟคาดการณ์ 1 ปีข้างหน้า') # แก้ไขหัวข้อ
        fig1 = plot_plotly(m, forecast)
        fig1.update_layout(height=600)
        st.plotly_chart(fig1, use_container_width=True)

        # รายละเอียดองค์ประกอบ
        st.markdown("#### องค์ประกอบการคาดการณ์ (Trends and Seasonality)")
        fig2 = m.plot_components(forecast)
        st.write(fig2)
        
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการทำนายด้วย Prophet: {e}")
        st.warning("กรุณาตรวจสอบว่ามีข้อมูลเพียงพอสำหรับการสร้างแบบจำลองหรือไม่")

else:
    st.error("ไม่สามารถโหลดข้อมูลราคาย้อนหลังได้ กรุณาตรวจสอบ Ticker หรือช่วงวันที่")