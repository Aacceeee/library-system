from flask import Flask, render_template, request, redirect
import mysql.connector
from datetime import date
import os

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)


@app.route("/__diag")
def diag():
    return {
        "url_map": str(app.url_map),
        "template_searchpath": app.jinja_loader.searchpath,
        "cwd": os.getcwd(),
    }

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="cccs105"
)


@app.route("/")
def home():
    return redirect("/welcome")


@app.route("/welcome")
def welcome():
    return render_template("welcome.html")


@app.route("/dashboard")
def dashboard():
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
    return render_template(
        "index.html",
        total_books=total_books,
        total_members=total_members,
        total_borrowings=total_borrowings,
        overdue=overdue,
        books=books,
    )

@app.route("/books")
def books():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    return render_template("books.html", books=books)

@app.route("/add_book", methods=["GET", "POST"])
def add_book():
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
    cursor = db.cursor()
    cursor.execute("DELETE FROM books WHERE book_id=%s", (id,))
    db.commit()
    return redirect("/books")

@app.route("/members")
def members():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM members")
    members = cursor.fetchall()
    return render_template("members.html", members=members)

@app.route("/add_member", methods=["GET", "POST"])
def add_member():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        cursor = db.cursor()
        cursor.execute("INSERT INTO members (name, email, phone) VALUES (%s, %s, %s)",
                      (name, email, phone))
        db.commit()
        return redirect("/members")
    return render_template("add_member.html")

@app.route("/edit_member/<int:id>", methods=["GET", "POST"])
def edit_member(id):
    cursor = db.cursor()
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        cursor.execute("UPDATE members SET name=%s, email=%s, phone=%s WHERE member_id=%s",
                      (name, email, phone, id))
        db.commit()
        return redirect("/members")
    cursor.execute("SELECT * FROM members WHERE member_id=%s", (id,))
    member = cursor.fetchone()
    return render_template("edit_member.html", member=member)

@app.route("/delete_member/<int:id>")
def delete_member(id):
    cursor = db.cursor()
    cursor.execute("DELETE FROM members WHERE member_id=%s", (id,))
    db.commit()
    return redirect("/members")

@app.route("/borrowings")
def borrowings():
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
    cursor = db.cursor()
    cursor.execute("DELETE FROM borrowings WHERE borrow_id=%s", (id,))
    db.commit()
    return redirect("/borrowings")

if __name__ == "__main__":
    app.run(debug=True)