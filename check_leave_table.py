import sqlite3

connection = sqlite3.connect(
    "instance/employee.db"
)

cursor = connection.cursor()

cursor.execute("PRAGMA table_info(leave)")

columns = cursor.fetchall()

print("\nCurrent columns in leave table:\n")

for column in columns:
    print(column)

connection.close()