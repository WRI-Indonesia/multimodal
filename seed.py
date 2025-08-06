import psycopg2

sql_path = "districts.sql"

with open(sql_path, "r") as f:
    sql_script = f.read()

conn = psycopg2.connect(
    dbname="multimodal",
    user="postgres",
    password="mynewpassword",
    host="localhost",
    port=5432,
)

cur = conn.cursor()
cur.execute(sql_script)
conn.commit()

print("✅ District seeding complete.")
cur.close()
conn.close()
