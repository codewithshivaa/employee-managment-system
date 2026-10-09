import sqlite3

database_path = "instance/employee.db"

connection = sqlite3.connect(database_path)
cursor = connection.cursor()

# Add role column
try:
    cursor.execute(
        "ALTER TABLE user ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'employee'"
    )
    print("role column added successfully!")

except sqlite3.OperationalError as e:
    print("role column:", e)


# Add employee_id column
try:
    cursor.execute(
        "ALTER TABLE user ADD COLUMN employee_id INTEGER"
    )
    print("employee_id column added successfully!")

except sqlite3.OperationalError as e:
    print("employee_id column:", e)


connection.commit()
connection.close()

print("Database migration completed!")