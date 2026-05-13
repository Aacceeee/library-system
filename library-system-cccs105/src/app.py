from flask import Flask, render_template, request, redirect, session
import re
import mysql.connector
from datetime import date

app = Flask(__name__)
app.secret_key = "library123"

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="cccs105"
)

# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "admin123":
            session["logged_in"] = True
            return redirect("/welcome")
        else:
            error = "Invalid username or password!"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/welcome")
def welcome():
    if not session.get("logged_in"):
        return redirect("/")
    return render_template("welcome.html")

@app.route("/dashboard")
def home():
    if not session.get("logged_in"):
        return redirect("/")
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM books")
    total_books = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM members")
    total_members = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM borrowings")
    total_borrowings = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM borrowings WHERE return_date < %s", (date.today(),))
    overdue = cursor.fetchone()[0]
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    return render_template("index.html",
                           total_books=total_books,
                           total_members=total_members,
                           total_borrowings=total_borrowings,
                           overdue=overdue,
                           books=books)

@app.route("/books")
def books():
    if not session.get("logged_in"):
        return redirect("/")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    return render_template("books.html", books=books)

@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if not session.get("logged_in"):
        return redirect("/")
    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        genre = request.form["genre"]
        quantity = request.form["quantity"]
        cursor = db.cursor()
        cursor.execute("INSERT INTO books (title, author, genre, quantity) VALUES (%s, %s, %s, %s)",
                      (title, author, genre, quantity))
        db.commit()
        return redirect("/books")
    return render_template("add_book.html")

@app.route("/edit_book/<int:id>", methods=["GET", "POST"])
def edit_book(id):
    if not session.get("logged_in"):
        return redirect("/")
    cursor = db.cursor()
    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        genre = request.form["genre"]
        quantity = request.form["quantity"]
        cursor.execute("UPDATE books SET title=%s, author=%s, genre=%s, quantity=%s WHERE book_id=%s",
                      (title, author, genre, quantity, id))
        db.commit()
        return redirect("/books")
    cursor.execute("SELECT * FROM books WHERE book_id=%s", (id,))
    book = cursor.fetchone()
    return render_template("edit_book.html", book=book)

@app.route("/delete_book/<int:id>")
def delete_book(id):
    if not session.get("logged_in"):
        return redirect("/")
    cursor = db.cursor()
    cursor.execute("DELETE FROM books WHERE book_id=%s", (id,))
    db.commit()
    return redirect("/books")

@app.route("/members")
def members():
    if not session.get("logged_in"):
        return redirect("/")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM members")
    members = cursor.fetchall()
    return render_template("members.html", members=members)

@app.route("/add_member", methods=["GET", "POST"])
def add_member():
    if not session.get("logged_in"):
        return redirect("/")
    error = None
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]

        # Validate name
        if not name.replace(" ", "").isalpha():
            error = "Name must contain letters only!"
        # Validate email
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(com|net|org|edu|gov|ph)$', email):
    error = "Please enter a valid email address (e.g. name@gmail.com)!""
        # Validate phone
        elif not phone.isdigit():
            error = "Phone number must contain numbers only!"
        elif len(phone) > 12:
            error = "Phone number must not exceed 12 digits!"
        else:
            cursor = db.cursor()
            cursor.execute("INSERT INTO members (name, email, phone) VALUES (%s, %s, %s)",
                          (name, email, phone))
            db.commit()
            return redirect("/members")
    return render_template("add_member.html", error=error)

@app.route("/edit_member/<int:id>", methods=["GET", "POST"])
def edit_member(id):
    if not session.get("logged_in"):
        return redirect("/")
    cursor = db.cursor()
    error = None
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]

        # Validate name
        if not name.replace(" ", "").isalpha():
            error = "Name must contain letters only!"
        # Validate email properly
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(com|net|org|edu|gov|ph)$', email):
            error = "Please enter a valid email address (e.g. name@gmail.com)!"
        # Validate phone
        elif not phone.isdigit():
            error = "Phone number must contain numbers only!"
        elif len(phone) > 12:
            error = "Phone number must not exceed 12 digits!"
        else:
            cursor.execute("UPDATE members SET name=%s, email=%s, phone=%s WHERE member_id=%s",
                          (name, email, phone, id))
            db.commit()
            return redirect("/members")
    cursor.execute("SELECT * FROM members WHERE member_id=%s", (id,))
    member = cursor.fetchone()
    return render_template("edit_member.html", member=member, error=error)
@app.route("/delete_member/<int:id>")
def delete_member(id):
    if not session.get("logged_in"):
        return redirect("/")
    cursor = db.cursor()
    cursor.execute("DELETE FROM members WHERE member_id=%s", (id,))
    db.commit()
    return redirect("/members")

@app.route("/borrowings")
def borrowings():
    if not session.get("logged_in"):
        return redirect("/")
    cursor = db.cursor()
    cursor.execute("""
        SELECT b.borrow_id, bk.title, m.name, b.borrow_date, b.return_date
        FROM borrowings b
        JOIN books bk ON b.book_id = bk.book_id
        JOIN members m ON b.member_id = m.member_id
    """)
    borrowings = cursor.fetchall()
    return render_template("borrowings.html", borrowings=borrowings, today=date.today())

@app.route("/add_borrowing", methods=["GET", "POST"])
def add_borrowing():
    if not session.get("logged_in"):
        return redirect("/")
    cursor = db.cursor()
    if request.method == "POST":
        book_id = request.form["book_id"]
        member_id = request.form["member_id"]
        borrow_date = request.form["borrow_date"]
        return_date = request.form["return_date"]
        cursor.execute("INSERT INTO borrowings (book_id, member_id, borrow_date, return_date) VALUES (%s, %s, %s, %s)",
                      (book_id, member_id, borrow_date, return_date))
        db.commit()
        return redirect("/borrowings")
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    cursor.execute("SELECT * FROM members")
    members = cursor.fetchall()
    return render_template("add_borrowing.html", books=books, members=members)

@app.route("/edit_borrowing/<int:id>", methods=["GET", "POST"])
def edit_borrowing(id):
    if not session.get("logged_in"):
        return redirect("/")
    cursor = db.cursor()
    if request.method == "POST":
        book_id = request.form["book_id"]
        member_id = request.form["member_id"]
        borrow_date = request.form["borrow_date"]
        return_date = request.form["return_date"]
        cursor.execute("UPDATE borrowings SET book_id=%s, member_id=%s, borrow_date=%s, return_date=%s WHERE borrow_id=%s",
                      (book_id, member_id, borrow_date, return_date, id))
        db.commit()
        return redirect("/borrowings")
    cursor.execute("SELECT * FROM borrowings WHERE borrow_id=%s", (id,))
    borrowing = cursor.fetchone()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    cursor.execute("SELECT * FROM members")
    members = cursor.fetchall()
    return render_template("edit_borrowing.html", borrowing=borrowing, books=books, members=members)

@app.route("/delete_borrowing/<int:id>")
def delete_borrowing(id):
    if not session.get("logged_in"):
        return redirect("/")
    cursor = db.cursor()
    cursor.execute("DELETE FROM borrowings WHERE borrow_id=%s", (id,))
    db.commit()
    return redirect("/borrowings")

if __name__ == "__main__":
    app.run(debug=True)
