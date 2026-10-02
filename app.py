from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from models import User, db, Employee

app = Flask(__name__)
app.secret_key = "employee-management-secret-key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///employee.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

def login_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(user.password, password):

            session["user_id"] = user.id
            session["username"] = user.username

            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():

    # Total employees
    total_employees = Employee.query.count()

    # Department-wise employee count
    department_counts = db.session.query(
        Employee.department,
        db.func.count(Employee.id)
    ).group_by(
        Employee.department
    ).all()

    # Average salary
    average_salary = db.session.query(
        db.func.avg(Employee.salary)
    ).scalar()

    if average_salary is None:
        average_salary = 0

    recent_employees = Employee.query.order_by(
        Employee.id.desc()
).limit(5).all()

    if average_salary is None:
        average_salary = 0

    return render_template(
        "dashboard.html",
        total_employees=total_employees,
        department_counts=department_counts,
        average_salary=average_salary,
        recent_employees=recent_employees
    )

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_employee():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        age = int(request.form["age"])
        department = request.form["department"]
        designation = request.form["designation"]
        salary = float(request.form["salary"])
        joining_date = request.form["joining_date"]
        status = request.form["status"]

        # Age validation
        if age < 18 or age > 60:
            flash("Age must be between 18 and 60", "danger")
            return redirect(url_for("add_employee"))

        # Salary validation
        if salary < 0:
            flash("Salary cannot be negative", "danger")
            return redirect(url_for("add_employee"))

        # Duplicate email validation
        existing_employee = Employee.query.filter_by(
            email=email
        ).first()

        if existing_employee:
            flash("An employee with this email already exists", "danger")
            return redirect(url_for("add_employee"))

        employee = Employee(
            name=name,
            email=email,
            phone=phone,
            age=age,
            department=department,
            designation=designation,
            salary=salary,
            joining_date=joining_date,
            status=status
        )

        db.session.add(employee)
        db.session.commit()

        flash("Employee added successfully!", "success")
        return redirect(url_for("view_employees"))

    return render_template("add_employee.html")

@app.route("/employees")
@login_required
def view_employees():

    search = request.args.get("search", "")
    department = request.args.get("department", "")
    sort = request.args.get("sort", "id_desc")
    status = request.args.get("status", "")

    page = request.args.get("page", 1, type=int)

    per_page = 10

    query = Employee.query

    # Search
    if search:
        query = query.filter(
            (Employee.name.ilike(f"%{search}%")) |
            (Employee.email.ilike(f"%{search}%")) |
            (Employee.designation.ilike(f"%{search}%"))
        )

    # Department filter
    if department:
        query = query.filter(
            Employee.department == department
        )

    # Status filter
    if status:
        query = query.filter(
            Employee.status == status
        )

    # Sorting
    if sort == "name_asc":
        query = query.order_by(Employee.name.asc())

    elif sort == "name_desc":
        query = query.order_by(Employee.name.desc())

    elif sort == "salary_asc":
        query = query.order_by(Employee.salary.asc())

    elif sort == "salary_desc":
        query = query.order_by(Employee.salary.desc())

    elif sort == "id_asc":
        query = query.order_by(Employee.id.asc())

    else:
        query = query.order_by(Employee.id.desc())

    # Pagination
    employee_list = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    departments = db.session.query(
        Employee.department
    ).distinct().all()

    return render_template(
        "employees.html",
        employees=employee_list,
        departments=departments,
        search=search,
        selected_department=department,
        selected_sort=sort,
        selected_status=status
    )
@app.route("/employee/<int:id>")
@login_required
def employee_details(id):

    employee = Employee.query.get_or_404(id)

    return render_template(
        "employee_details.html",
        employee=employee
    )

@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_employee(id):

    employee = Employee.query.get_or_404(id)

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        age = int(request.form["age"])
        department = request.form["department"]
        designation = request.form["designation"]
        salary = float(request.form["salary"])
        joining_date = request.form["joining_date"]
        status = request.form["status"]

        # Age validation
        if age < 18 or age > 60:
            flash("Age must be between 18 and 60", "danger")
            return redirect(url_for("edit_employee", id=id))

        # Salary validation
        if salary < 0:
            flash("Salary cannot be negative", "danger")
            return redirect(url_for("edit_employee", id=id))

        # Duplicate email validation
        existing_employee = Employee.query.filter_by(
            email=email
        ).first()

        if existing_employee and existing_employee.id != employee.id:
            flash(
                "Another employee already uses this email",
                "danger"
            )
            return redirect(url_for("edit_employee", id=id))

        # Update employee
        employee.name = name
        employee.email = email
        employee.phone = phone
        employee.age = age
        employee.department = department
        employee.designation = designation
        employee.salary = salary
        employee.joining_date = joining_date
        employee.status = status

        db.session.commit()

        flash("Employee updated successfully!", "success")

        return redirect(url_for("view_employees"))

    return render_template(
        "edit_employee.html",
        employee=employee
    )

@app.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_employee(id):

    employee = Employee.query.get_or_404(id)

    db.session.delete(employee)
    db.session.commit()

    flash("Employee deleted successfully!", "success")

    return redirect(url_for("view_employees"))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)