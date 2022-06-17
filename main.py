import sqlite3


def get_DBcursor():
    con = sqlite3.connect('edu.db')  # DB open
    c = con.cursor()  # 커서 획득
    return (con, c)

con, c = get_DBcursor()

c.execute("SELECT Subject FROM historyTBL where ID = ?",(("qwe",)))
row = c.fetchall()
print(row.)
