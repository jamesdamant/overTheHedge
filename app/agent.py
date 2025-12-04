import os
import yfinance as yf
from config import get_config
from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain.tools import tool

os.environ["AZURE_OPENAI_API_KEY"] = "c3cd1443e26345dca5254896e070e727"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://farmai.openai.azure.com/"
os.environ["OPENAI_API_VERSION"] = "2024-12-01-preview"
os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = "gpt-4.1"


@tool
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



class OverTheHedgeAgent():

    def __init__(self):
        self.model = init_chat_model(
            "azure_openai:gpt-4.1",
            azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
        )

        self.db = SQLDatabase.from_uri("sqlite:///data/db/hedgefund.db")
        self.system_prompt = get_config("prompt", "system_prompt")
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.model)
        self.tools = self.toolkit.get_tools() + [get_yfinance_data]

        self.agent = create_agent(
            self.model,
            self.tools,
            system_prompt=self.system_prompt,
        )

    def call(self, chat_history, user_query):
        """
        Streams the response from the agent, yielding the content of assistant
        messages as they are generated.
        """
        # Prepare messages for the agent
        lc_messages = []
        for msg in chat_history:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
        
        # Add the current user query
        lc_messages.append(HumanMessage(content=user_query))
        
        for step in self.agent.stream(
            {"messages": lc_messages},
            stream_mode="values", 
        ):
            last_message = step["messages"][-1]
            if isinstance(last_message, AIMessage):
                yield last_message.content