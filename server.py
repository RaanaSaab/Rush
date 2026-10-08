import json
import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "rush_admin_secret_key_change_me"

DB_FILE = os.path.join(os.path.dirname(__file__), "users_db.json")
DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASS = "admin123"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                if "settings" not in data:
                    data["settings"] = {}
                if "admin_user" not in data["settings"]:
                    data["settings"]["admin_user"] = DEFAULT_ADMIN_USER
                if "admin_pass" not in data["settings"]:
                    data["settings"]["admin_pass"] = DEFAULT_ADMIN_PASS
                return data
        except Exception:
            pass
    return {
        "users": {},
        "settings": {
            "admin_user": DEFAULT_ADMIN_USER,
            "admin_pass": DEFAULT_ADMIN_PASS
        }
    }

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rush App - Admin Control Panel</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }
        .card { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 15px; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }
        th { background-color: #343a40; color: white; }
        .badge { padding: 5px 10px; border-radius: 4px; font-weight: bold; color: white; font-size: 12px; }
        .badge-active { background-color: #28a745; }
        .badge-deactive { background-color: #ffc107; color: #212529; }
        .badge-blocked { background-color: #dc3545; }
        .btn { padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; font-size: 13px; margin-right: 4px; }
        .btn-active { background-color: #28a745; color: white; }
        .btn-deactive { background-color: #ffc107; color: black; }
        .btn-block { background-color: #dc3545; color: white; }
        .btn-delete { background-color: #6c757d; color: white; }
        .btn-logout { background-color: #6c757d; color: white; float: right; }
        .login-box { max-width: 400px; margin: 80px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.15); }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        .btn-submit { width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }
        .alert-success { background-color: #d4edda; color: #155724; padding: 10px; border-radius: 4px; margin-bottom: 15px; }
    </style>
</head>
<body>

{% if logged_in %}
<div class="container">
    <a href="/logout" class="btn btn-logout">Logout</a>
    <h1>Rush App - Admin Control Panel</h1>

    {% if msg %}
    <div class="alert-success">{{ msg }}</div>
    {% endif %}

    <div class="card">
        <h3>Server Information</h3>
        <p><strong>Server Status:</strong> <span style="color: green;">Online 🟢</span></p>
        <p><strong>App Endpoint:</strong> <code>/api/check_status</code></p>
    </div>

    <h2>Registered Users & Devices ({{ users|length }})</h2>
    <table>
        <thead>
            <tr>
                <th>Username</th>
                <th>Device ID</th>
                <th>Device Model</th>
                <th>Last Seen</th>
                <th>Current Status</th>
                <th>Action / Controls</th>
            </tr>
        </thead>
        <tbody>
            {% for uid, user in users.items() %}
            <tr>
                <td><strong>{{ user.username }}</strong></td>
                <td><code>{{ user.device_id }}</code></td>
                <td>{{ user.device_name }}</td>
                <td>{{ user.last_seen }}</td>
                <td>
                    {% if user.status == 'active' %}
                        <span class="badge badge-active">ACTIVE</span>
                    {% elif user.status == 'deactive' %}
                        <span class="badge badge-deactive">DEACTIVATED</span>
                    {% else %}
                        <span class="badge badge-blocked">BLOCKED</span>
                    {% endif %}
                </td>
                <td>
                    <a href="/update_status?uid={{ uid }}&status=active" class="btn btn-active">Activate</a>
                    <a href="/update_status?uid={{ uid }}&status=deactive" class="btn btn-deactive">Deactivate</a>
                    <a href="/update_status?uid={{ uid }}&status=blocked" class="btn btn-block">Block</a>
                    <a href="/delete_user?uid={{ uid }}" class="btn btn-delete" onclick="return confirm('Is user ko table se delete karna chahte hain?');">Delete 🗑️</a>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="6" style="text-align: center; color: #777;">Koi user connect nahi hua abhi tak. Mobile App khol kar connect karein.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <br><hr><br>

    <div class="card">
        <h3>🔐 Change Admin Login Credentials</h3>
        <form method="POST" action="/change_credentials" style="max-width: 400px;">
            <div class="form-group">
                <label>New Admin Username</label>
                <input type="text" name="new_username" value="{{ current_admin_user }}" required>
            </div>
            <div class="form-group">
                <label>New Admin Password</label>
                <input type="password" name="new_password" placeholder="Enter new password" required>
            </div>
            <button type="submit" class="btn btn-submit" style="width: auto;">Update Credentials</button>
        </form>
    </div>
</div>
{% else %}
<div class="login-box">
    <h2 style="text-align: center; color: #2c3e50;">Admin Login</h2>
    {% if error %}
    <p style="color: red; text-align: center;">{{ error }}</p>
    {% endif %}
    <form method="POST" action="/login">
        <div class="form-group">
            <label>Username</label>
            <input type="text" name="username" required value="admin">
        </div>
        <div class="form-group">
            <label>Password</label>
            <input type="password" name="password" required>
        </div>
        <button type="submit" class="btn-submit">Login Panel</button>
    </form>
</div>
{% endif %}

</body>
</html>
"""

@app.route("/")
def index():
    if "admin_logged_in" not in session:
        return render_template_string(HTML_TEMPLATE, logged_in=False, error=None)
    db = load_db()
    msg = request.args.get("msg")
    current_admin_user = db.get("settings", {}).get("admin_user", DEFAULT_ADMIN_USER)
    return render_template_string(
        HTML_TEMPLATE,
        logged_in=True,
        users=db.get("users", {}),
        msg=msg,
        current_admin_user=current_admin_user
    )

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    db = load_db()
    admin_user = db.get("settings", {}).get("admin_user", DEFAULT_ADMIN_USER)
    admin_pass = db.get("settings", {}).get("admin_pass", DEFAULT_ADMIN_PASS)

    if username == admin_user and password == admin_pass:
        session["admin_logged_in"] = True
        return redirect(url_for("index"))
    return render_template_string(HTML_TEMPLATE, logged_in=False, error="Invalid Username or Password!")

@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("index"))

@app.route("/update_status")
def update_status():
    if "admin_logged_in" not in session:
        return redirect(url_for("index"))

    uid = request.args.get("uid")
    new_status = request.args.get("status")

    if uid and new_status in ["active", "deactive", "blocked"]:
        db = load_db()
        if uid in db["users"]:
            db["users"][uid]["status"] = new_status
            save_db(db)

    return redirect(url_for("index"))

@app.route("/delete_user")
def delete_user():
    if "admin_logged_in" not in session:
        return redirect(url_for("index"))

    uid = request.args.get("uid")
    if uid:
        db = load_db()
        if uid in db.get("users", {}):
            del db["users"][uid]
            save_db(db)

    return redirect(url_for("index", msg="User record deleted successfully!"))

@app.route("/change_credentials", methods=["POST"])
def change_credentials():
    if "admin_logged_in" not in session:
        return redirect(url_for("index"))

    new_user = request.form.get("new_username", "").strip()
    new_pass = request.form.get("new_password", "").strip()

    if new_user and new_pass:
        db = load_db()
        db["settings"]["admin_user"] = new_user
        db["settings"]["admin_pass"] = new_pass
        save_db(db)
        return redirect(url_for("index", msg="Admin Username & Password Successfully Updated!"))

    return redirect(url_for("index"))

# API called by Android App
@app.route("/api/check_status", methods=["GET"])
def check_status():
    username = request.args.get("username", "unknown")
    device_id = request.args.get("device_id", "unknown")
    device_name = request.args.get("device_name", "Android Device")

    db = load_db()
    users = db.get("users", {})

    user_key = f"{username}_{device_id}"

    if user_key not in users:
        users[user_key] = {
            "username": username,
            "device_id": device_id,
            "device_name": device_name,
            "status": "active",
            "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        db["users"] = users
        save_db(db)
    else:
        users[user_key]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        users[user_key]["device_name"] = device_name
        db["users"] = users
        save_db(db)

    current_status = users[user_key]["status"]
    return jsonify({
        "status": current_status,
        "message": f"User status is {current_status}"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 60)
    print(f" Rush Admin Server Running on port {port}!")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=False)
