import streamlit as st
import yfinance as yf
import mplfinance as mpf
import yahoo_fin.stock_info as yfs
import datetime as dt
import pandas as pd
import talib
import requests

st.title("My Stock Analysis Dashboard")
st.sidebar.title("What do You want to see?")

start_date = st.sidebar.date_input("Start date", dt.date(2021, 1, 1))
end_date = st.sidebar.date_input("End date", dt.date.today())

ticker = st.sidebar.text_input("Enter a stock symbol", value= "JAGX")

ticker_data = yf.Ticker(ticker)

string_logo = '<img src=%s>' % ticker_data.info['logo_url']
st.markdown(string_logo, unsafe_allow_html=True)



string_name = ticker_data.info['longName']
st.header('**%s**' % string_name)

with st.beta_expander("See a short summary of the company"):
    string_summary = ticker_data.info['longBusinessSummary']
    st.success(string_summary)


from PIL import Image
st.image("https://charts2.finviz.com/chart.ashx?t="+ticker+"&ty=c&ta=1&p=d&s=l")


df = yf.download(ticker,start=start_date, end=end_date)
df["MA100"] = df["Adj Close"].rolling(window=100).mean()
df["MA50"] = df["Adj Close"].rolling(window=50).mean()
df["MA20"] = df["Adj Close"].rolling(window=20).mean()

data_ticker = pd.DataFrame(df,columns=["Adj Close","MA20","MA50","MA100"])
data_volume = df["Volume"]


with st.beta_expander("Financials"):
    col1, col2 = st.beta_columns(2)

    with col1:
        st.subheader("Earnings per Year")
        st.table(ticker_data.earnings)

    with col2:
        st.subheader("Earnings per Quarter")
        st.table(ticker_data.quarterly_earnings)

    st.subheader("Recommendations")
    rec_df = pd.DataFrame(ticker_data.recommendations)
    rec_df.reset_index(inplace=True)
    rec_df["Date"] = rec_df["Date"].dt.strftime('%d-%m-%Y')
    st.write(rec_df)

    st.subheader("Sustainability")
    st.write(ticker_data.sustainability)

    st.subheader("Institutional Holders")
    inst_df = pd.DataFrame(ticker_data.institutional_holders)
    inst_df["Date Reported"] = inst_df["Date Reported"].dt.strftime('%d-%m-%Y')
    st.write(inst_df)

    st.subheader("Major Holders")
    st.write(ticker_data.major_holders)

    st.subheader("Mutual Fund Holders")
    mutual_df = pd.DataFrame(ticker_data.mutualfund_holders)
    mutual_df["Date Reported"] = mutual_df["Date Reported"].dt.strftime('%d-%m-%Y')
    st.write(mutual_df)


with st.beta_expander("Stocktwits interactions"):

    r = requests.get(f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json")
    data = r.json()
    """st.write(data)
    st.write(messages["sentiment"])"""
    for messages in data["messages"]:

        st.image(messages["user"]["avatar_url"])
        st.write(messages["user"]["username"])
        st.write(messages["created_at"])
        st.write(messages["body"])
        #st.success(messages["entities"]["sentiment"]["basic"])

with st.beta_expander("Momentum Indicators"):

    #Price history
    df['SMA'] = talib.SMA(df['Adj Close'], timeperiod=20)
    df['EMA'] = talib.EMA(df['Adj Close'], timeperiod=20)
    st.header(f"Simple Moving Average vs. Exponential Moving Average\n {ticker}")
    st.line_chart(df[['Adj Close', 'SMA', 'EMA']])

    st.subheader("Volume")
    st.bar_chart(data_volume)

    # Bollinger Bands
    df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(df['Adj Close'], timeperiod =20)
    st.header(f"Bollinger Bands\n {ticker}")
    st.line_chart(df[['Adj Close','upper_band','middle_band','lower_band']])

    # MACD
    df['macd'], df['macdsignal'], df['macdhist'] = talib.MACD(df['Adj Close'], fastperiod=12, slowperiod=26, signalperiod=9)
    st.header(f"Moving Average Convergence Divergence\n {ticker}")
    st.line_chart(df[['macd','macdsignal']])

    ## CCI (Commodity Channel Index)
    # CCI
    cci = talib.CCI(df['High'], df['Low'], df['Close'], timeperiod=14)
    st.header(f"Commodity Channel Index\n {ticker}")
    st.line_chart(cci)

    # ## RSI (Relative Strength Index)
    # RSI
    df['RSI'] = talib.RSI(df['Adj Close'], timeperiod=14)
    st.header(f"Relative Strength Index\n {ticker}")
    st.line_chart(df['RSI'])

    df["MFI"] = talib.MFI(df['High'], df['Low'], df['Close'],df["Volume"], timeperiod=14)
    st.header(f"Money Flow Index\n {ticker}")
    st.line_chart(df['MFI'])

    # ## OBV (On Balance Volume)
    # OBV
    df['OBV'] = talib.OBV(df['Adj Close'], df['Volume'])/10**6
    st.header(f"On Balance Volume\n {ticker}")
    st.line_chart(df['OBV'])

with st.beta_expander("News Sentiment last 5"):
    from urllib.request import urlopen, Request
    from bs4 import BeautifulSoup
    from nltk.sentiment.vader import SentimentIntensityAnalyzer

    news_tables = {}

    finviz_url = "https://finviz.com/quote.ashx?t="

    url = finviz_url + ticker

    req = Request(url=url, headers={"user-agent": "my-app"})
    response = urlopen(req)

    html = BeautifulSoup(response, "html")
    news_table = html.find(id="news-table")
    news_tables[ticker] = news_table

    # Parse the data
    parsed_data = []
    for ticker, news_table in news_tables.items():

        for row in news_table.findAll("tr"):

            title = row.a.text
            date_data = row.td.text.split(" ")

            if len(date_data) == 1:
                time = date_data[0]
            else:
                date = date_data[0]
                time = date_data[1]

            parsed_data.append([ticker, date, time, title])

    df = pd.DataFrame(parsed_data, columns=["ticker", "date", "time", "title"])

    vader = SentimentIntensityAnalyzer()

    f = lambda title: vader.polarity_scores(title)["compound"]
    df["compound"] = df["title"].apply(f)
    df["date"] = pd.to_datetime(df.date).dt.date

    mean_df = df.groupby(["ticker", "date", "title"]).mean()

    mean_df = mean_df.tail(5)

    st.table(mean_df)