from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import (
   LoginManager, UserMixin, login_user,
   logout_user, current_user, login_required
)
import sqlite3
from datetime import datetime, date
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
DB_NAME = "rza_zoo.db"

# DATABASE CONNECTION
def get_db():
   db_name = app.config.get("DATABASE", DB_NAME)   # Use test DB if set
   conn = sqlite3.connect(db_name)
   conn.row_factory = sqlite3.Row
   return conn

def init_db():
   conn = get_db()
   c = conn.cursor()
   # Users table
   c.execute("""
       CREATE TABLE IF NOT EXISTS users(
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           username TEXT UNIQUE NOT NULL,
           email TEXT UNIQUE NOT NULL,
           password TEXT NOT NULL
       )
   """)
   # Bookings table
   c.execute("""
       CREATE TABLE IF NOT EXISTS bookings(
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           user_id INTEGER NOT NULL,
           name TEXT NOT NULL,
           email TEXT NOT NULL,
           date TEXT NOT NULL,
           tickets INTEGER NOT NULL,
           ticket_type TEXT NOT NULL,
           FOREIGN KEY (user_id) REFERENCES users(id)
       )
   """)
   conn.commit()
   conn.close()

# USER CLASS FOR FLASK-LOGIN
class User(UserMixin):
   def __init__(self, row):
    self.id = str(row["id"])
    self.username = row["username"]
    self.email = row["email"]
    self.password_hash = row["password"]

def get_user_by_id(uid):
   conn = get_db()
   row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
   conn.close()
   return row
def get_user_by_email(email):
   conn = get_db()
   row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
   conn.close()
   return row

@login_manager.user_loader
def load_user(user_id):
   row = get_user_by_id(user_id)
   return User(row) if row else None

# ADMIN DASHBOARD
@app.route('/admin')
@login_required
def admin_dashboard():
   if current_user.id != "1":
       flash("Access denied — Admins only!", "danger")
       return redirect(url_for("home"))
   conn = get_db()
   bookings = conn.execute("""
       SELECT b.*, u.username
       FROM bookings b
       JOIN users u ON b.user_id = u.id
   """).fetchall()
   conn.close()
   return render_template("admin_dashboard.html", bookings=bookings)

# EDIT BOOKING
@app.route('/edit_booking/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_booking(id):
   conn = get_db()
   booking = conn.execute("SELECT * FROM bookings WHERE id = ?", (id,)).fetchone()
   if not booking:
       flash("Booking not found.", "danger")
       return redirect(url_for("account"))
   if str(booking["user_id"]) != current_user.id and current_user.id != "1":
       flash("Access denied.", "danger")
       return redirect(url_for("account"))
   if request.method == "POST":
       name = request.form["name"]
       email = request.form["email"]
       tickets = int(request.form["tickets"])
       ticket_type = request.form["ticket_type"]
       date_selected = request.form["date"]
       booking_date = datetime.strptime(date_selected, "%Y-%m-%d").date()
       if booking_date < date.today():
           flash("Date cannot be in the past!", "error")
           return redirect(url_for("edit_booking", id=id))
       max_date = date.today().replace(year=date.today().year + 1)
       if booking_date > max_date:
           flash("Date too far in the future!", "error")
           return redirect(url_for("edit_booking", id=id))
       conn.execute("""
           UPDATE bookings
           SET name=?, email=?, date=?, tickets=?, ticket_type=?
           WHERE id=?
       """, (name, email, date_selected, tickets, ticket_type, id))
       conn.commit()
       conn.close()
       flash("Booking updated!", "success")
       return redirect(url_for("account"))
   conn.close()
   return render_template("edit_booking.html", booking=booking)

# DELETE BOOKING
@app.route('/delete_booking/<int:id>')
@login_required
def delete_booking(id):
   conn = get_db()
   booking = conn.execute("SELECT * FROM bookings WHERE id=?", (id,)).fetchone()
   if not booking:
       flash("Booking not found", "danger")
       return redirect(url_for("account"))
   if str(booking["user_id"]) != current_user.id and current_user.id != "1":
       flash("Access denied", "danger")
       return redirect(url_for("account"))
   conn.execute("DELETE FROM bookings WHERE id=?", (id,))
   conn.commit()
   conn.close()
   flash("Booking deleted.", "info")
   return redirect(url_for("account"))

# PAGES
@app.route('/')
def home():
   conn = get_db()
   bookings = conn.execute("SELECT * FROM bookings").fetchall()
   conn.close()
   return render_template("index.html", bookings=bookings)
@app.route('/about')
def about():
   return render_template("about.html")
@app.route('/booking')
def booking():
   return render_template("booking.html")
@app.route('/education')
def education():
   return render_template("education.html")
@app.route('/animalsfact')  
def animals_fact():
    return render_template("animals_fact.html")


# BOOKING SUBMISSION
@app.route('/booking/submit', methods=['POST'])
@login_required
def booking_submit():
   name = request.form["name"]
   email = request.form["email"]
   date_selected = request.form["date"]
   tickets = int(request.form["tickets"])
   ticket_type = request.form["ticket_type"]
   booking_date = datetime.strptime(date_selected, "%Y-%m-%d").date()
   ticket_max = 50
   if tickets > ticket_max:
        flash("You can only book 50 tickets max!", "error")
        return redirect(url_for("booking", id=id))
   if booking_date < date.today():
       flash("You cannot choose a past date.", "error")
       return redirect(url_for("booking"))
   max_date = date.today().replace(year=date.today().year + 1)
   if booking_date > max_date:
       flash("Date too far in the future.", "error")
       return redirect(url_for("booking"))
   
   #TICKET PRICES

   ticket_prices = {
      "Single": 12.00,
      "Child":  8.00,
      "Family": 20.00,
      "Education": 10.00
   }

   price_per_ticket = ticket_prices.get(ticket_type, 0)
   total_cost = price_per_ticket * tickets

   conn = get_db()
   conn.execute("""
    INSERT INTO bookings (user_id, name, email, date, tickets, ticket_type)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (current_user.id, name, email, date_selected, tickets, ticket_type))
   conn.commit()
   conn.close()

   return render_template(
      "confirmation.html",
      name=name,
      date=date_selected,
      tickets=tickets,
      ticket_type=ticket_type,
      total_cost=total_cost

   )

# AUTH ROUTES
@app.route('/register', methods=['GET', 'POST'])
def register():
   if request.method == "POST":
       username = request.form["username"]
       email = request.form["email"]
       password = request.form["password"]
       confirm = request.form["confirm_password"]
       if password != confirm:
           flash("Passwords do not match", "error")
           return redirect(url_for("register"))
       if get_user_by_email(email):
           flash("Email already registered", "error")
           return redirect(url_for("login"))
       hashed = bcrypt.generate_password_hash(password).decode("utf-8")
       conn = get_db()
       conn.execute("""
           INSERT INTO users (username, email, password)
           VALUES (?, ?, ?)
       """, (username, email, hashed))
       conn.commit()
       conn.close()
       flash("Account created!", "success")
       return redirect(url_for("login"))
   return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
   if request.method == "POST":
       email = request.form["email"]
       password = request.form["password"]
       row = get_user_by_email(email)
       if row and bcrypt.check_password_hash(row["password"], password):
           user = User(row)
           login_user(user)
           return redirect(url_for("home"))
       flash("Invalid credentials", "danger")
   return render_template("login.html")

@app.route('/account')
@login_required
def account():
   conn = get_db()
   bookings = conn.execute(
       "SELECT * FROM bookings WHERE user_id=?", (current_user.id,)
   ).fetchall()
   conn.close()
   return render_template("account.html",
        user=current_user,
        bookings=bookings)

@app.route('/logout')
@login_required
def logout():
   logout_user()
   flash("Logged out", "info")
   return redirect(url_for("home"))

# RUN APP
if __name__ == "__main__":
   init_db()
   app.run(debug=True)


