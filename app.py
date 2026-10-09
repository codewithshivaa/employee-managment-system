from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from models import User, db, Employee, Attendance, ProfileUpdateRequest, Notification, Leave, LeaveBalance 
from datetime import datetime, date
import csv
import io

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

def admin_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            return redirect(
                url_for("employee_dashboard")
            )

        return function(*args, **kwargs)

    return decorated_function

def employee_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session.get("role") != "employee":
            return redirect(url_for("dashboard"))

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
            session["role"] = user.role

            if user.role == "admin":
                return redirect(url_for("dashboard"))

            elif user.role == "employee":
                return redirect(url_for("employee_dashboard"))

            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template("login.html")

@app.route("/create-employee-account", methods=["GET", "POST"])
@admin_required
def create_employee_account():

    employees = Employee.query.order_by(
        Employee.name.asc()
    ).all()

    if request.method == "POST":

        employee_id = request.form["employee_id"]
        username = request.form["username"].strip()
        password = request.form["password"]

        employee = Employee.query.get_or_404(employee_id)

        # Check if this employee already has an account
        existing_employee_account = User.query.filter_by(
            employee_id=employee.id
        ).first()

        if existing_employee_account:
            flash(
                "This employee already has a login account.",
                "danger"
            )
            return redirect(
                url_for("create_employee_account")
            )

        # Check username
        existing_username = User.query.filter_by(
            username=username
        ).first()

        if existing_username:
            flash(
                "This username is already taken.",
                "danger"
            )
            return redirect(
                url_for("create_employee_account")
            )

        # Validate password
        if len(password) < 6:
            flash(
                "Password must be at least 6 characters.",
                "danger"
            )
            return redirect(
                url_for("create_employee_account")
            )

        password_hash = generate_password_hash(password)

        user = User(
            username=username,
            password=password_hash,
            role="employee",
            employee_id=employee.id
        )

        db.session.add(user)
        db.session.commit()

        notification = Notification(
        employee_id=employee.id,
        message="Your employee account has been created successfully."
        )

        db.session.add(notification)
        db.session.commit()

        flash(
            f"Login account created for {employee.name}!",
            "success"
        )

        return redirect(
            url_for("create_employee_account")
        )

    return render_template(
        "create_employee_account.html",
        employees=employees
    )

@app.route("/employee-dashboard")
@employee_required
def employee_dashboard():

    user = User.query.get_or_404(
        session["user_id"]
    )

    employee = Employee.query.get_or_404(
        user.employee_id
    )

    # ================= TODAY'S ATTENDANCE =================

    today = datetime.now().date()

    attendance = Attendance.query.filter_by(
        employee_id=employee.id,
        date=today
    ).first()

    working_hours = None

    if attendance and attendance.punch_in and attendance.punch_out:

        duration = (
            attendance.punch_out
            - attendance.punch_in
        )

        total_seconds = int(
            duration.total_seconds()
        )

        hours = total_seconds // 3600

        minutes = (
            total_seconds % 3600
        ) // 60

        working_hours = f"{hours} hours {minutes} minutes"

    # ================= PAGE =================

    return render_template(
        "employee_dashboard.html",
        employee=employee,
        attendance=attendance,
        working_hours=working_hours
    )

@app.route("/attendance-history")
@employee_required
def attendance_history():

    user = User.query.get_or_404(
        session["user_id"]
    )

    employee = Employee.query.get_or_404(
        user.employee_id
    )

    # ================= ATTENDANCE HISTORY =================

    history_date = request.args.get(
        "history_date",
        ""
    )

    history_query = Attendance.query.filter_by(
        employee_id=employee.id
    )

    if history_date:

        history_query = history_query.filter(
            Attendance.date == history_date
        )

    history_records = history_query.order_by(
        Attendance.date.desc()
    ).all()

    attendance_history = []

    for record in history_records:

        working_hours_history = "-"

        if record.punch_in and record.punch_out:

            duration = (
                record.punch_out
                - record.punch_in
            )

            total_seconds = int(
                duration.total_seconds()
            )

            hours = total_seconds // 3600

            minutes = (
                total_seconds % 3600
            ) // 60

            working_hours_history = (
                f"{hours}h {minutes}m"
            )

        attendance_history.append({
            "record": record,
            "working_hours": working_hours_history
        })

    return render_template(
        "employee_attendance_history.html",
        employee=employee,
        attendance_history=attendance_history
    )

@app.route("/apply-leave", methods=["GET", "POST"])
@employee_required
def apply_leave():

    user = User.query.get_or_404(
        session["user_id"]
    )

    employee = Employee.query.get_or_404(
        user.employee_id
    )

    if request.method == "POST":

        leave_type = request.form["leave_type"]

        from_date = datetime.strptime(
            request.form["from_date"],
            "%Y-%m-%d"
        ).date()

        to_date = datetime.strptime(
            request.form["to_date"],
            "%Y-%m-%d"
        ).date()

        reason = request.form["reason"].strip()

        # Calculate number of leave days
        leave_days = (
            to_date - from_date
        ).days + 1

        # Validate date range
        if to_date < from_date:

            flash(
                "To date cannot be before from date.",
                "danger"
            )

            return redirect(
                url_for("apply_leave")
            )

        # Check for overlapping leave requests
        overlapping_leave = Leave.query.filter(
            Leave.employee_id == employee.id,
            Leave.status.in_(["Pending", "Approved"]),
            Leave.from_date <= to_date,
            Leave.to_date >= from_date
        ).first()

        if overlapping_leave:

            flash(
                "You already have a leave request for some or all of these dates.",
                "danger"
            )

            return redirect(
                url_for("apply_leave")
    )

        # Find employee's leave balance
        balance = LeaveBalance.query.filter_by(
            employee_id=employee.id,
            leave_type=leave_type
        ).first()

        # Check whether balance exists
        if not balance:

            flash(
                "Leave balance not found for this leave type.",
                "danger"
            )

            return redirect(
                url_for("apply_leave")
            )

        # Calculate remaining balance
        remaining_days = (
            balance.total_days - balance.used_days
        )

        # Check available balance
        if leave_days > remaining_days:

            flash(
                f"You cannot apply for {leave_days} days of "
                f"{leave_type}. You have only "
                f"{remaining_days} day(s) remaining.",
                "warning"
            )

            return redirect(
                url_for("apply_leave")
            )

        # Validate date range
        if to_date < from_date:

            flash(
                "To date cannot be before from date.",
                "danger"
            )

            return redirect(
                url_for("apply_leave")
            )

        new_leave = Leave(
            employee_id=employee.id,
            leave_type=leave_type,
            from_date=from_date,
            to_date=to_date,
            reason=reason
        )

        db.session.add(new_leave)
        db.session.commit()

        flash(
            "Leave application submitted successfully!",
            "success"
        )

        return redirect(
            url_for("apply_leave")
        )

    return render_template(
        "apply_leave.html",
        employee=employee,
        leave_balances=LeaveBalance.query.filter_by(
            employee_id=employee.id
        ).all()
    )

@app.route("/my-leaves")
@employee_required
def my_leaves():

    user = User.query.get_or_404(
        session["user_id"]
    )

    employee = Employee.query.get_or_404(
        user.employee_id
    )

    # Employee's leave requests
    leave_requests = Leave.query.filter_by(
        employee_id=employee.id
    ).order_by(
        Leave.id.desc()
    ).all()

    # Employee's leave balances
    leave_balances = LeaveBalance.query.filter_by(
        employee_id=employee.id
    ).all()

    return render_template(
        "my_leaves.html",
        employee=employee,
        leave_requests=leave_requests,
        leave_balances=leave_balances
    )

@app.route("/punch-in", methods=["POST"])
@employee_required
def punch_in():

    user = User.query.get_or_404(
        session["user_id"]
    )

    today = datetime.now().date()

    existing_attendance = Attendance.query.filter_by(
        employee_id=user.employee_id,
        date=today
    ).first()

    if existing_attendance:
        flash(
            "You have already punched in today.",
            "warning"
        )
        return redirect(
            url_for("employee_dashboard")
        )

    attendance = Attendance(
        employee_id=user.employee_id,
        date=today,
        punch_in=datetime.now(),
        status="Present"
    )

    db.session.add(attendance)
    db.session.commit()

    flash(
        "Punch In successful!",
        "success"
    )

    return redirect(
        url_for("employee_dashboard")
    )

@app.route("/punch-out", methods=["POST"])
@employee_required
def punch_out():

    user = User.query.get_or_404(
        session["user_id"]
    )

    today = datetime.now().date()

    attendance = Attendance.query.filter_by(
        employee_id=user.employee_id,
        date=today
    ).first()

    if not attendance:
        flash(
            "Please punch in first.",
            "warning"
        )
        return redirect(
            url_for("employee_dashboard")
        )

    if attendance.punch_out:
        flash(
            "You have already punched out today.",
            "warning"
        )
        return redirect(
            url_for("employee_dashboard")
        )

    attendance.punch_out = datetime.now()

    db.session.commit()

    flash(
        "Punch Out successful!",
        "success"
    )

    return redirect(
        url_for("employee_dashboard")
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@admin_required
def dashboard():

    # Today's date
    today = date.today()

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

    # Recent employees
    recent_employees = Employee.query.order_by(
        Employee.id.desc()
    ).limit(5).all()

    # ================= ATTENDANCE =================

    today_attendance = Attendance.query.filter_by(
        date=today
    ).all()

    present_today = sum(
        1
        for record in today_attendance
        if record.status == "Present"
    )

    currently_working = sum(
        1
        for record in today_attendance
        if record.punch_in and not record.punch_out
    )

    completed_today = sum(
        1
        for record in today_attendance
        if record.punch_in and record.punch_out
    )

    pending_requests = ProfileUpdateRequest.query.filter_by(
        status="Pending"
    ).count()

    # ================= LEAVE BALANCE =================

    leave_balances = LeaveBalance.query.join(
        Employee,
        LeaveBalance.employee_id == Employee.id
    ).all()

    return render_template(
        "dashboard.html",
        total_employees=total_employees,
        department_counts=department_counts,
        average_salary=average_salary,
        recent_employees=recent_employees,
        present_today=present_today,
        currently_working=currently_working,
        completed_today=completed_today,
        pending_requests=pending_requests,
        leave_balances=leave_balances
    )

@app.route("/add", methods=["GET", "POST"])
@admin_required
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

        # Create default leave balances
        leave_balances = [
            LeaveBalance(
                employee_id=employee.id,
                leave_type="Sick Leave",
                total_days=12,
                used_days=0
            ),
            LeaveBalance(
                employee_id=employee.id,
                leave_type="Casual Leave",
                total_days=12,
                used_days=0
            ),
            LeaveBalance(
                employee_id=employee.id,
                leave_type="Paid Leave",
                total_days=15,
                used_days=0
            )
        ]

        db.session.add_all(leave_balances)
        db.session.commit()

        flash("Employee added successfully!", "success")
        return redirect(url_for("view_employees"))

    return render_template("add_employee.html")

@app.route("/export-employees")
@admin_required
def export_employees():

    employees = Employee.query.order_by(
        Employee.id.asc()
    ).all()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "ID",
        "Name",
        "Email",
        "Phone",
        "Age",
        "Department",
        "Designation",
        "Salary",
        "Joining Date",
        "Status"
    ])

    for employee in employees:

        writer.writerow([
            employee.id,
            employee.name,
            employee.email,
            employee.phone,
            employee.age,
            employee.department,
            employee.designation,
            employee.salary,
            employee.joining_date,
            employee.status
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=employees.csv"
        }
    )

@app.route("/employees")
@admin_required
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

    # Employee can view only their own profile
    if session.get("role") == "employee":

        user = User.query.get_or_404(
            session["user_id"]
        )

        if user.employee_id != employee.id:
            return redirect(
                url_for("employee_dashboard")
            )

    return render_template(
        "employee_details.html",
        employee=employee
    )

@app.route("/my-profile")
@employee_required
def my_profile():

    user = User.query.get_or_404(
        session["user_id"]
    )

    employee = Employee.query.get_or_404(
        user.employee_id
    )

    return render_template(
        "employee_profile.html",
        employee=employee
    )

@app.route(
    "/request-profile-update",
    methods=["GET", "POST"]
)
@employee_required
def request_profile_update():

    user = User.query.get_or_404(
        session["user_id"]
    )

    employee = Employee.query.get_or_404(
        user.employee_id
    )

    if request.method == "POST":

        field = request.form["field"]
        new_value = request.form["new_value"].strip()
        reason = request.form["reason"].strip()

        allowed_fields = {
            "name": "name",
            "email": "email",
            "phone": "phone",
            "age": "age"
        }

        if field not in allowed_fields:

            flash(
                "Invalid profile field.",
                "danger"
            )

            return redirect(
                url_for("request_profile_update")
            )

        old_value = str(
            getattr(
                employee,
                allowed_fields[field]
            )
        )

        if not new_value:

            flash(
                "Please enter the new value.",
                "danger"
            )

            return redirect(
                url_for("request_profile_update")
            )

        profile_request = ProfileUpdateRequest(
            employee_id=employee.id,
            field=field,
            old_value=old_value,
            new_value=new_value,
            reason=reason
        )

        db.session.add(profile_request)
        db.session.commit()

        flash(
            "Profile update request submitted successfully!",
            "success"
        )

        return redirect(
            url_for("my_profile")
        )

    return render_template(
        "request_profile_update.html",
        employee=employee
    )

@app.route("/leave-requests")
@admin_required
def leave_requests():

    leave_requests = Leave.query.order_by(
        Leave.id.desc()
    ).all()

    return render_template(
        "leave_requests.html",
        leave_requests=leave_requests
    )

@app.route("/leave/<int:leave_id>/approve", methods=["POST"])
@admin_required
def approve_leave(leave_id):

    leave = Leave.query.get_or_404(leave_id)

    # Only pending requests can be approved
    if leave.status != "Pending":

        flash(
            "This leave request has already been processed.",
            "warning"
        )

        return redirect(
            url_for("leave_requests")
        )

    # Calculate number of leave days
    leave_days = (
        leave.to_date - leave.from_date
    ).days + 1

    # Find employee's leave balance
    balance = LeaveBalance.query.filter_by(
        employee_id=leave.employee_id,
        leave_type=leave.leave_type
    ).first()

    # Check whether balance exists
    if not balance:

        flash(
            "Leave balance not found for this employee.",
            "danger"
        )

        return redirect(
            url_for("leave_requests")
        )

    # Calculate remaining days
    remaining_days = (
        balance.total_days - balance.used_days
    )

    # Check available balance
    if leave_days > remaining_days:

        flash(
            f"Insufficient leave balance. "
            f"Only {remaining_days} day(s) remaining.",
            "danger"
        )

        return redirect(
            url_for("leave_requests")
        )

    # Approve leave
    leave.status = "Approved"

    # Deduct from leave balance
    balance.used_days += leave_days

    db.session.commit()

    flash(
        "Leave request approved successfully!",
        "success"
    )

    return redirect(
        url_for("leave_requests")
    )

@app.route("/leave/<int:leave_id>/reject", methods=["POST"])
@admin_required
def reject_leave(leave_id):

    leave = Leave.query.get_or_404(leave_id)

    # Only pending requests can be rejected
    if leave.status != "Pending":

        flash(
            "This leave request has already been processed.",
            "warning"
        )

        return redirect(
            url_for("leave_requests")
        )

    # Reject leave
    leave.status = "Rejected"

    db.session.commit()

    flash(
        "Leave request rejected.",
        "success"
    )

    return redirect(
        url_for("leave_requests")
    )

@app.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_required
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
@admin_required
def delete_employee(id):

    employee = Employee.query.get_or_404(id)

    db.session.delete(employee)
    db.session.commit()

    flash("Employee deleted successfully!", "success")

    return redirect(url_for("view_employees"))

@app.route(
    "/toggle-employee-status/<int:id>",
    methods=["POST"]
)
@admin_required
def toggle_employee_status(id):

    employee = Employee.query.get_or_404(id)

    if employee.status == "Active":

        employee.status = "Inactive"

    else:

        employee.status = "Active"

    db.session.commit()

    flash(
        f"{employee.name}'s status changed to {employee.status}.",
        "success"
    )

    return redirect(
        url_for("view_employees")
    )

@app.route("/attendance")
@admin_required
def attendance():

    today = date.today()

    search = request.args.get("search", "").strip()

    date_filter = request.args.get("date", "")

    status_filter = request.args.get("status", "")

    # Get employees
    employees = {
        employee.id: employee
        for employee in Employee.query.all()
    }

    # Start attendance query
    query = Attendance.query

    # Search by employee name
    if search:
        matching_employee_ids = [
            employee.id
            for employee in Employee.query
            .filter(
                Employee.name.ilike(f"%{search}%")
            )
            .all()
        ]

        query = query.filter(
            Attendance.employee_id.in_(matching_employee_ids)
        )

    # Filter by date
    if date_filter:
        query = query.filter(
            Attendance.date == date_filter
        )

    # Filter by status
    if status_filter:
        query = query.filter(
            Attendance.status == status_filter
        )

    # Get filtered records
    attendance_records = query.order_by(
        Attendance.date.desc(),
        Attendance.punch_in.desc()
    ).all()

    # ================= SUMMARY =================

    total_records = len(attendance_records)

    present_records = sum(
        1
        for record in attendance_records
        if record.status == "Present"
    )

    completed_records = sum(
        1
        for record in attendance_records
        if record.punch_in and record.punch_out
    )

    currently_punched_in = sum(
        1
        for record in attendance_records
        if record.punch_in and not record.punch_out
    )

    return render_template(
        "admin_attendance.html",

        attendance_records=attendance_records,

        employees=employees,

        search=search,

        date_filter=date_filter,

        status_filter=status_filter,

        today=today,   # 👈 IMPORTANT

        total_records=total_records,

        present_records=present_records,

        completed_records=completed_records,

        currently_punched_in=currently_punched_in
    )

@app.route("/my-attendance")
@employee_required
def my_attendance():

    user = User.query.get_or_404(
        session["user_id"]
    )

    employee = Employee.query.get_or_404(
        user.employee_id
    )

    today = datetime.now().date()

    attendance_record = Attendance.query.filter_by(
        employee_id=employee.id,
        date=today
    ).first()

    working_hours = None

    if (
        attendance_record
        and attendance_record.punch_in
        and attendance_record.punch_out
    ):

        duration = (
            attendance_record.punch_out
            - attendance_record.punch_in
        )

        total_seconds = int(
            duration.total_seconds()
        )

        hours = total_seconds // 3600

        minutes = (
            total_seconds % 3600
        ) // 60

        working_hours = f"{hours} hours {minutes} minutes"

    return render_template(
        "attendance.html",
        employee=employee,
        attendance=attendance_record,
        working_hours=working_hours,
        today=today
    )

@app.route("/profile-update-requests")
@admin_required
def profile_update_requests():

    requests = ProfileUpdateRequest.query.order_by(
        ProfileUpdateRequest.id.desc()
    ).all()

    employees = {
        employee.id: employee
        for employee in Employee.query.all()
    }

    return render_template(
        "profile_update_requests.html",
        requests=requests,
        employees=employees
    )

@app.route("/my-profile-requests")
@employee_required
def my_profile_requests():

    user = User.query.get_or_404(
        session["user_id"]
    )

    employee = Employee.query.get_or_404(
        user.employee_id
    )

    requests = ProfileUpdateRequest.query.filter_by(
        employee_id=employee.id
    ).order_by(
        ProfileUpdateRequest.id.desc()
    ).all()

    return render_template(
        "my_profile_requests.html",
        requests=requests
    )

@app.route("/approve-profile-request/<int:id>", methods=["POST"])
@admin_required
def approve_profile_request(id):

    profile_request = ProfileUpdateRequest.query.get_or_404(id)

    if profile_request.status != "Pending":

        flash(
            "This request has already been processed.",
            "warning"
        )

        return redirect(
            url_for("profile_update_requests")
        )

    employee = Employee.query.get_or_404(
        profile_request.employee_id
    )

    # Update the requested field

    if profile_request.field == "name":

        employee.name = profile_request.new_value

    elif profile_request.field == "email":

        employee.email = profile_request.new_value

    elif profile_request.field == "phone":

        employee.phone = profile_request.new_value

    elif profile_request.field == "age":

        try:

            employee.age = int(
                profile_request.new_value
            )

        except ValueError:

            flash(
                "Invalid age value.",
                "danger"
            )

            return redirect(
                url_for("profile_update_requests")
            )

    else:

        flash(
            "Invalid profile field.",
            "danger"
        )

        return redirect(
            url_for("profile_update_requests")
        )

    profile_request.status = "Approved"

    db.session.commit()

    flash(
        f"Profile update for {employee.name} approved successfully!",
        "success"
    )

    return redirect(
        url_for("profile_update_requests")
    )   

@app.route("/reject-profile-request/<int:id>", methods=["POST"])
@admin_required
def reject_profile_request(id):

    profile_request = ProfileUpdateRequest.query.get_or_404(id)

    if profile_request.status != "Pending":

        flash(
            "This request has already been processed.",
            "warning"
        )

        return redirect(
            url_for("profile_update_requests")
        )

    profile_request.status = "Rejected"

    db.session.commit()

    flash(
        "Profile update request rejected.",
        "info"
    )

    return redirect(
        url_for("profile_update_requests")
    )


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)