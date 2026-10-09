Employee Management System

A web-based Employee Management System built using Python, Flask, SQLite, HTML, and CSS. The application helps administrators manage employee records, track attendance, handle leave requests, and manage employee profile information.

Features
Admin Features
Admin login and dashboard
Add, view, edit, and manage employee records
Track and manage employee attendance
Review and manage employee leave requests
View and manage employee profile-update requests
Employee Features
Employee account creation and login
Employee dashboard
View and manage profile information
View attendance history
Apply for leave and view leave requests
Submit profile-update requests
Technologies Used
Backend: Python, Flask
Database: SQLite
Frontend: HTML, CSS, Bootstrap (if used in the project)
Version Control: Git and GitHub
Project Structure
EMPLOYEE MANAGEMENT SYSTEM/
├── app.py
├── models.py
├── create_admin.py
├── requirements.txt
├── .gitignore
├── Templates/
│   ├── add_employee.html
│   ├── dashboard.html
│   ├── employees.html
│   ├── employee_details.html
│   ├── edit_employee.html
│   ├── login.html
│   ├── admin_attendance.html
│   ├── attendance.html
│   ├── apply_leave.html
│   ├── leave_requests.html
│   ├── employee_dashboard.html
│   └── ...
└── instance/
Installation and Setup
1. Clone the repository
git clone https://github.com/codewithshivaa/employee-managment-system.git
cd employee-managment-system
2. Create a virtual environment
python -m venv venv

Activate it on Windows:

venv\Scripts\activate
3. Install dependencies
pip install -r requirements.txt
4. Configure the application

Set up any required environment variables and database configuration according to the project code. Do not publish real passwords, secret keys, or other sensitive credentials.

5. Initialize the database and admin account

If required by your application, run the appropriate database setup or migration scripts and follow the instructions in create_admin.py to create an administrator account.

6. Run the application
python app.py

Open the local URL displayed in your terminal, commonly:

http://127.0.0.1:5000

Database

The application uses SQLite to store employee and related application data. The database is created or initialized according to the application's configuration.

Note: Do not commit a database containing real employee information or other private data.

Future Improvements
Improve input validation and error handling
Add role-based access control and stronger authentication
Add reporting and data export features
Improve the user interface and mobile responsiveness
Add automated tests

Author
Shivanjali Pawar
GitHub: @codewithshivaa

License
This project is created for learning and educational purposes.
