import psycopg2

conn = psycopg2.connect(database = "pi",
                        user = "pi",
                        host = "192.168.1.100",
                        password = "BlueBoat2020",
                        port = 5432)

cursor = conn.cursor()
cursor.execute('SELECT * FROM public."Parts";')
rows = cursor.fetchall()
conn.commit()
conn.close()
for row in rows:
    print(row)