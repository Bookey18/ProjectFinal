import streamlit as st
from datetime import date
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
from plotly import graph_objs as go
from googletrans import Translator

# วันที่
START = "2015-01-01"
TODAY = date.today().strftime("%Y-%m-%d")

st.set_page_config(layout="wide")
st.title('📈 แอปทำนายราคาหุ้นและดัชนี พร้อมข้อมูลบริษัท (ภาษาไทย)')

# กล่องเลือกหมวดหมู่
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
    "KLA Corporation (KLAC)": "KLAC"

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

selected_label = st.selectbox(f"เลือก {category}", list(stock_options.keys()))
selected_stock = stock_options[selected_label]

# ปีที่ต้องการทำนาย
n_years = st.slider('เลือกจำนวนปีที่ต้องการทำนาย:', 1, 4)
period = n_years * 365

# โหลดข้อมูลหุ้น
@st.cache_data
def load_data(ticker):
    data = yf.download(ticker, START, TODAY)
    data.reset_index(inplace=True)
    
    # ตรวจสอบจำนวนคอลัมน์เพื่อจัดการกรณีที่ 'Adj Close' หายไป (โดยเฉพาะสำหรับดัชนี/กองทุน)
    # yfinance มักจะคืนค่า 7 คอลัมน์ (รวม Date) หรือ 6 คอลัมน์ (เมื่อไม่มี Adj Close)
    if len(data.columns) == 7:
        # 7 คอลัมน์: Date, Open, High, Low, Close, Adj Close, Volume
        data.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    elif len(data.columns) == 6:
        # 6 คอลัมน์: Date, Open, High, Low, Close, Volume
        data.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        # เพิ่มคอลัมน์ Adj Close โดยใช้ค่าจาก Close เพื่อให้โค้ดส่วนอื่นทำงานได้
        data['Adj Close'] = data['Close']
    else:
        # กรณีคอลัมน์ไม่ตรงกับที่คาดไว้ (ไม่น่าจะเกิดขึ้น)
        st.error(f"⚠️ โหลดข้อมูลล้มเหลว: จำนวนคอลัมน์ที่ได้รับ ({len(data.columns)}) ไม่ถูกต้อง")

    return data

data_load_state = st.text('📥 กำลังดาวน์โหลดข้อมูล...')
data = load_data(selected_stock)
data_load_state.text('✅ ดาวน์โหลดข้อมูลเสร็จสิ้น')


# ----------------------------------------------------------------------
# ********** ส่วนที่แก้ไข/เพิ่มเติม: การแสดงกราฟราคาย้อนหลัง **********

st.subheader('📊 ราคาย้อนหลัง')

# ตัวเลือกประเภทกราฟ
chart_type = st.radio(
    "เลือกประเภทกราฟ:",
    ('Candlestick Chart (แนะนำ)', 'Line Chart (ราคาปิด)'),
    horizontal=True
)

# ฟังก์ชันแสดงกราฟแท่งเทียน (Candlestick Chart)
def plot_candlestick_chart():
    fig = go.Figure(data=[go.Candlestick(
        x=data['Date'],
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        increasing_line_color='#2ecc71', # สีเขียว (ราคาขึ้น)
        decreasing_line_color='#e74c3c' # สีแดง (ราคาลง)
    )])
    
    # ปรับแต่ง layout
    fig.update_layout(
        title=f'📈 กราฟแท่งเทียนราคาย้อนหลังของ {selected_label}',
        xaxis_title='วันที่',
        yaxis_title='ราคา',
        xaxis_rangeslider_visible=True, # เปิดแถบเลื่อนด้านล่างสำหรับซูม
        template='plotly_white',
        hovermode='x unified',
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)

# ฟังก์ชันแสดงกราฟเส้น (Line Chart) ที่ดูง่ายกว่าแบบ Area Chart เดิม
def plot_line_chart():
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data['Date'],
        y=data['Close'],
        mode='lines',
        name='ราคาปิด (Close)',
        line=dict(color='#3498db', width=2), # สีน้ำเงิน
        fill='tozeroy', 
        fillcolor='rgba(52, 152, 219, 0.2)' 
    ))

    fig.update_layout(
        title=f'📈 กราฟเส้นราคาปิดย้อนหลังของ {selected_label}',
        xaxis_title='วันที่',
        yaxis_title='ราคา',
        xaxis_rangeslider_visible=True, 
        template='plotly_white',
        hovermode='x unified',
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)


if chart_type == 'Candlestick Chart (แนะนำ)':
    plot_candlestick_chart()
else:
    plot_line_chart()

# แสดงข้อมูลดิบ (ย้ายมาไว้ข้างล่างกราฟ)
st.write(data.tail())

# ----------------------------------------------------------------------

# แสดงข้อมูลบริษัท พร้อมแปล
st.subheader("📄 ข้อมูลบริษัท (จาก Yahoo Finance)")

try:
    ticker_info = yf.Ticker(selected_stock).info
    long_name = ticker_info.get('longName', selected_label)
    industry = ticker_info.get('industry', 'ไม่มีข้อมูล')
    sector = ticker_info.get('sector', 'ไม่มีข้อมูล')
    website = ticker_info.get('website', '')
    city = ticker_info.get('city', '')
    country = ticker_info.get('country', '')
    summary_en = ticker_info.get('longBusinessSummary', 'ไม่มีข้อมูล')

    # แปลเป็นภาษาไทย
    translator = Translator()
    translation = translator.translate(summary_en, src='en', dest='th')
    summary_th = translation.text

    # แสดงข้อมูล
    st.markdown(f"### 🏢 {long_name}")
    st.markdown(f"**อุตสาหกรรม:** {industry}")
    st.markdown(f"**ภาคธุรกิจ:** {sector}")
    st.markdown(f"**ที่ตั้ง:** {city}, {country}")
    st.markdown(f"**เว็บไซต์:** [{website}]({website})")

    st.markdown("### 📘 สรุปธุรกิจ (ภาษาไทย)")
    st.markdown(summary_th)

except Exception as e:
    st.warning("⚠️ ไม่สามารถโหลดหรือแปลข้อมูลบริษัทได้")
    # st.code(str(e)) # ปิดโค้ดแสดง error เพื่อให้ดูสะอาดตา

# เตรียมข้อมูลสำหรับ Prophet
df_train = data[['Date', 'Close']].rename(columns={"Date": "ds", "Close": "y"})
m = Prophet()
m.fit(df_train)
future = m.make_future_dataframe(periods=period)
forecast = m.predict(future)

# แสดงผลการทำนาย
st.subheader('🔮 การทำนายราคาหุ้น')
st.write(forecast.tail())

st.write(f'🕒 กราฟคาดการณ์ {n_years} ปีข้างหน้า')
fig1 = plot_plotly(m, forecast)
# ปรับปรุงสีของกราฟคาดการณ์ให้ดูดีขึ้น
fig1.update_traces(marker=dict(color='#ff7f0e'), selector=dict(name='trend')) 
fig1.update_layout(height=600)

st.plotly_chart(fig1, use_container_width=True)

st.write("🔍 รายละเอียดองค์ประกอบการคาดการณ์")
fig2 = m.plot_components(forecast)
st.write(fig2)