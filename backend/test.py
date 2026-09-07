import pymysql

conn = pymysql.connect(
    host="127.0.0.1",
    port=3306,
    user="root",
    password="aertghWZD2",
    charset="utf8mb4"
)
print("✅ Python连接MySQL成功")
conn.close()