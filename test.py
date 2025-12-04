import pandas as pd
import requests 

df = pd.read_json("./data/primary_doc.json")

# print(df.head(10))

def cik_lookup(name: str):
    url = "https://efts.sec.gov/LATEST/search-index"

    headers = {
        "User-Agent": "james@damant.com",   # REQUIRED BY SEC
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "keys": name,
        # "category": "entity"   # tells SEC to search filer names
    }

    r = requests.post(url, json=payload, headers=headers)
    print(r.text)
    data = r.json()

    results = data.get("hits", {}).get("hits", [])

    cik_results = []
    for item in results:
        source = item.get("_source", {})
        cik = source.get("cik")
        entity = source.get("entity")
        if cik:
            cik_results.append({
                "entity": entity,
                "cik": str(cik).zfill(10)
            })

    return cik_results


# Example
# results = cik_lookup("Bridgewater Associates")
# for r in results:
#     print(r)


from ingest import DataLoader

dl = DataLoader()
md=dl.get_latest_sub("1637460")
print(md)
# md= {'name': 'Bridgewater Associates, LP', 'form': '13F-HR', 'accessionNumber': '0001172661-25-004777', 'filingDate': '2025-11-13', 'reportDate': '2025-09-30'}
# dl.get_infotable("1637460", '000163746025-000003', md)

from agent import OverTheHedgeAgent

agent = OverTheHedgeAgent()

# agent.call([], "what fund holds AMD?")

from database import Database
dbman = Database()
# print(dbman.select_test("select * from holdings where nameOfIssuer = 'NVIDIA CORPORATION'"))
import yfinance as yf


def get_yfinance_data(ticker: str) -> str:
    """
    Fetches real-time stock market data and recent news headlines (top 3) 
    for a given ticker symbol (e.g., 'NVDA', 'AAPL') using yfinance.

    Use this tool to find current stock price, market fundamentals, and recent context 
    that complements the 13F holdings data. The agent should use this output 
    to provide the "market intelligence" aspect of the trade pitch.
    
    Args:
        ticker: The stock ticker symbol (e.g., 'NVDA').
    Returns:
        A string summarizing the current price, key metrics, and recent news.
    """
    if not ticker:
        return "Error: Ticker symbol cannot be empty."

    try:
        from curl_cffi import requests

        with requests.Session(impersonate="chrome") as session:

            session.verify = False  # Disable SSL verification
        
            stock = yf.Ticker(ticker=ticker, session=session)
            info = stock.info
            news = stock.news

            current_price = info.get('currentPrice', 'N/A')
            previous_close = info.get('previousClose', 'N/A')
            week_52_high = info.get('fiftyTwoWeekHigh', 'N/A')
            week_52_low = info.get('fiftyTwoWeekLow', 'N/A')
            market_cap = info.get('marketCap', 'N/A')

            summary = (
                f"Market Intelligence for {ticker}:\n"
                f" - Current Price: ${current_price}\n"
                f" - Previous Close: ${previous_close}\n"
                f" - 52-Week Range: ${week_52_low} to ${week_52_high}\n"
                f" - Market Cap: {market_cap}\n"
            )
            # print(news)
            # Get recent news
            if news:
                summary += "\nRecent News Headlines (Top 3):\n"
                for i, article in enumerate(news[:3]):
                    title=article.get("content").get("summary")
                    summary += f"- Title: {title}\n"
            else:
                summary += "\nNo recent news headlines found.\n"
                
        return summary

    except Exception as e:
        return f"Error fetching yfinance data for {ticker}. The ticker may be invalid or market data is unavailable. Detail: {e}"


print(get_yfinance_data("NVDA"))