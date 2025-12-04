import sqlite3
import pandas as pd

class Database():
    def __init__(self, db_name="./data/db/hedgefund.db", check_same_thread=True):
        """
        Initialize connection to SQLite database.
        
        The check_same_thread=False parameter is added to allow the connection
        to be used across different threads, which is necessary in environments
        like Streamlit where database operations might happen in different threads.
        """
        self.conn = sqlite3.connect(db_name, check_same_thread=check_same_thread)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        """Create table if it does not exist."""
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nameOfIssuer TEXT,
            titleOfClass TEXT,
            cusip TEXT,
            value INTEGER,
            sshPrnamt INTEGER,
            sshPrnamtType TEXT,
            investmentDiscretion TEXT,
            voting_Sole INTEGER,
            voting_Shared INTEGER,
            voting_None INTEGER,
            fundName TEXT,
            form TEXT,
            accessionNumber TEXT,
            filingDate TEXT,
            reportDate TEXT
        )
        """)
        self.conn.commit()

    def insert_dataframe(self, df: pd.DataFrame):
        """Insert all rows from a pandas DataFrame into the table."""
        df.to_sql("holdings", self.conn, if_exists="append", index=False)

    def insert_record(self, record: dict):
        """Insert a single record (dict with column names)."""
        columns = ", ".join(record.keys())
        placeholders = ", ".join(["?"] * len(record))
        sql = f"INSERT INTO holdings ({columns}) VALUES ({placeholders})"
        self.cursor.execute(sql, tuple(record.values()))
        self.conn.commit()

    def select_all(self):
        """Retrieve all records."""
        self.cursor.execute("SELECT * FROM holdings")
        return self.cursor.fetchall()

    def select_where(self, col_name, condition):
        """Retrieve records filtered by a specific column and value."""
        valid_columns = [
            "nameOfIssuer", "titleOfClass", "cusip", "value", "sshPrnamt",
            "sshPrnamtType", "investmentDiscretion", "voting_Sole", "voting_Shared",
            "voting_None", "fundName", "form", "accessionNumber", "filingDate", "reportDate"
        ]
        if col_name not in valid_columns:
            raise ValueError(f"Invalid column name: {col_name}")

        sql = f"SELECT * FROM holdings WHERE {col_name} = ?"
        self.cursor.execute(sql, (condition,))
        return self.cursor.fetchall()
    
    def select_test(self, sql):
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def close(self):
        """Close the database connection."""
        self.conn.close()