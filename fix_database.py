import sqlite3

connection = sqlite3.connect(
    "instance/employee.db"
)

cursor = connection.cursor()

# Add missing columns to leave table

cursor.execute("""
    ALTER TABLE leave
    ADD COLUMN leave_type VARCHAR(50)
""")

cursor.execute("""
    ALTER TABLE leave
    ADD COLUMN from_date DATE
""")

cursor.execute("""
    ALTER TABLE leave
    ADD COLUMN to_date DATE
""")

cursor.execute("""
    ALTER TABLE leave
    ADD COLUMN reason TEXT
""")

cursor.execute("""
    ALTER TABLE leave
    ADD COLUMN status VARCHAR(20) DEFAULT 'Pending'
""")

cursor.execute("""
    ALTER TABLE leave
    ADD COLUMN applied_on DATETIME
""")

connection.commit()

connection.close()

print("Leave table updated successfully!")