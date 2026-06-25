import sqlite3

def check():
    conn = sqlite3.connect("backend/investment_ai.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trades")
    trades = cursor.fetchall()
    print("Trades:")
    for t in trades:
        print(t)
    conn.close()

if __name__ == "__main__":
    check()
