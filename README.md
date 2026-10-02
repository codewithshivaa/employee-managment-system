Employee Management System

A web-based Employee Management System developed using Python and Flask.
The application allows users to manage employee information through a simple web interface.

Features
🔐 User login/authentication
👨‍💼 Add new employees
📋 View all employees
🔎 View employee details
✏️ Edit employee information
🗑️ Manage employee records
📊 Dashboard for employee management
🗄️ Database integration
Technologies Used
Python
Flask
HTML5
CSS
SQLite / Database
Jinja2 Templates
Project Structure
EMPLOYEE MANAGEMENT SYSTEM/
│
├── app.py
├── models.py
├── create_admin.py
├── .gitignore
│
├── Templates/
│   ├── login.html
│   ├── dashboard.html
│   ├── employees.html
│   ├── add_employee.html
│   ├── edit_employee.html
│   └── employee_details.html
│
└── instance/
    └── database files

The instance/ folder is excluded from GitHub using .gitignore to avoid uploading local database files.

Installation
1. Clone the repository
git clone https://github.com/codewithshivaa/employee-managment-system.git
2. Navigate to the project directory
cd employee-managment-system
3. Create a virtual environment
python -m venv venv
4. Activate the virtual environment

Windows:

venv\Scripts\activate

macOS/Linux:

source venv/bin/activate
5. Install dependencies

If the project contains a requirements.txt file:

pip install -r requirements.txt

Otherwise, install Flask:

pip install flask

Install any additional packages required by the project.

Running the Application

Run the Flask application:

python app.py

The application will start on a local development server.

Open your browser and visit:

http://127.0.0.1:5000/
Admin Setup

If required, run the admin creation script:

python create_admin.py

Follow the instructions provided by the application/script.

Application Pages
Page	Description
Login	User authentication
Dashboard	Overview of the system
Employees	View employee records
Add Employee	Add a new employee
Edit Employee	Update employee information
Employee Details	View detailed employee information
Future Improvements
Add employee search and filtering
Add employee profile images
Add role-based access control
Add pagination
Improve UI/UX
Add REST API support
Add automated testing
Deploy the application online
Author

Shivanjali Pawar

GitHub:
https://github.com/codewithshivaa

License

This project is created for learning and educational purposes.
