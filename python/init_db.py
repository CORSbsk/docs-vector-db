from db import get_connection

with open("sql/init.sql", encoding="utf-8") as f:
    sql = f.read()

conn = get_connection()
cur = conn.cursor()
cur.execute(sql)
conn.commit()
conn.close()
print("Tablas creadas correctamente")