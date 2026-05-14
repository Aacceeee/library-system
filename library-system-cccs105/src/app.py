from flask import Flask, render_template, request, redirect, session, flash
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


def normalize_text(value):
    return " ".join(value.strip().split()).lower()


def ensure_borrowing_status_column():
    cursor = db.cursor()
    cursor.execute("SHOW COLUMNS FROM borrowings LIKE 'status'")
    if not cursor.fetchone():
        try:
            cursor.execute("ALTER TABLE borrowings ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'borrowed'")
            db.commit()
        except mysql.connector.Error as exc:
            if getattr(exc, "errno", None) != 1060:
                raise
    cursor.close()


def get_borrowing_status(borrowing_row):
    stored_status = borrowing_row[5] if len(borrowing_row) > 5 and borrowing_row[5] else "borrowed"
    return_date = borrowing_row[4]
    if stored_status == "returned":
        return "returned"
    if return_date and return_date < date.today():
        return "overdue"
    return "borrowed"


ensure_borrowing_status_column()

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
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM borrowings
        WHERE COALESCE(status, 'borrowed') <> 'returned'
          AND return_date < %s
        """,
        (date.today(),)
    )
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
    error = None
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        genre = request.form.get("genre", "").strip()
        quantity = request.form.get("quantity", "").strip()
        if not title or not author or not genre or not quantity:
            error = "Please fill in all book fields."
        else:
            try:
                quantity_value = int(quantity)
            except ValueError:
                error = "Quantity must be a whole number."
            else:
                if quantity_value < 0:
                    error = "Quantity cannot be negative."
                else:
                    cursor = db.cursor()
                    cursor.execute(
                        """
                        SELECT book_id
                        FROM books
                        WHERE LOWER(TRIM(title))=%s
                          AND LOWER(TRIM(author))=%s
                          AND LOWER(TRIM(genre))=%s
                        """,
                        (normalize_text(title), normalize_text(author), normalize_text(genre))
                    )
                    if cursor.fetchone():
                        error = "This book already exists."
                    else:
                        cursor.execute(
                            "INSERT INTO books (title, author, genre, quantity) VALUES (%s, %s, %s, %s)",
                            (title, author, genre, quantity_value)
                        )
                        db.commit()
                        flash("Book added successfully.", "success")
                        return redirect("/books")
    return render_template("add_book.html", error=error)

@app.route("/edit_book/<int:id>", methods=["GET", "POST"])
def edit_book(id):
    if not session.get("logged_in"):
        return redirect("/")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM books WHERE book_id=%s", (id,))
    book = cursor.fetchone()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        genre = request.form.get("genre", "").strip()
        quantity = request.form.get("quantity", "").strip()
        error = None
        if not title or not author or not genre or not quantity:
            error = "Please fill in all book fields."
        else:
            try:
                quantity_value = int(quantity)
            except ValueError:
                error = "Quantity must be a whole number."
            else:
                if quantity_value < 0:
                    error = "Quantity cannot be negative."
                else:
                    cursor.execute(
                        """
                        SELECT book_id
                        FROM books
                        WHERE LOWER(TRIM(title))=%s
                          AND LOWER(TRIM(author))=%s
                          AND LOWER(TRIM(genre))=%s
                          AND book_id <> %s
                        """,
                        (normalize_text(title), normalize_text(author), normalize_text(genre), id)
                    )
                    if cursor.fetchone():
                        error = "This book already exists."
                    else:
                        cursor.execute(
                            "UPDATE books SET title=%s, author=%s, genre=%s, quantity=%s WHERE book_id=%s",
                            (title, author, genre, quantity_value, id)
                        )
                        db.commit()
                        flash("Book updated successfully.", "success")
                        return redirect("/books")
        book = (id, title, author, genre, quantity)
        return render_template("edit_book.html", book=book, error=error)
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
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        # Validate name
        if not name.replace(" ", "").isalpha():
            error = "Name must contain letters only!"
        # Validate email
        elif "@" not in email or "." not in email.split("@")[-1]:
            error = "Please enter a valid email address!"
        # Validate phone
        elif not phone.isdigit():
            error = "Phone number must contain numbers only!"
        elif len(phone) > 12:
            error = "Phone number must not exceed 12 digits!"
        else:
            cursor = db.cursor()
            cursor.execute(
                """
                SELECT member_id
                FROM members
                WHERE LOWER(TRIM(name))=%s
                   OR LOWER(TRIM(email))=%s
                """,
                (normalize_text(name), normalize_text(email))
            )
            if cursor.fetchone():
                error = "A member with the same name or email already exists."
            else:
                cursor.execute("INSERT INTO members (name, email, phone) VALUES (%s, %s, %s)",
                              (name, email, phone))
                db.commit()
                flash("Member added successfully.", "success")
                return redirect("/members")
    return render_template("add_member.html", error=error)

@app.route("/edit_member/<int:id>", methods=["GET", "POST"])
def edit_member(id):
    if not session.get("logged_in"):
        return redirect("/")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM members WHERE member_id=%s", (id,))
    member = cursor.fetchone()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        error = None
        if not name.replace(" ", "").isalpha():
            error = "Name must contain letters only!"
        elif "@" not in email or "." not in email.split("@")[-1]:
            error = "Please enter a valid email address!"
        elif not phone.isdigit():
            error = "Phone number must contain numbers only!"
        elif len(phone) > 12:
            error = "Phone number must not exceed 12 digits!"
        else:
            cursor.execute(
                """
                SELECT member_id
                FROM members
                WHERE (LOWER(TRIM(name))=%s OR LOWER(TRIM(email))=%s)
                  AND member_id <> %s
                """,
                (normalize_text(name), normalize_text(email), id)
            )
            if cursor.fetchone():
                error = "A member with the same name or email already exists."
            else:
                cursor.execute("UPDATE members SET name=%s, email=%s, phone=%s WHERE member_id=%s",
                              (name, email, phone, id))
                db.commit()
                flash("Member updated successfully.", "success")
                return redirect("/members")
        member = (id, name, email, phone)
        return render_template("edit_member.html", member=member, error=error)
    return render_template("edit_member.html", member=member)

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
        SELECT b.borrow_id, bk.title, m.name, b.borrow_date, b.return_date, b.status
        FROM borrowings b
        JOIN books bk ON b.book_id = bk.book_id
        JOIN members m ON b.member_id = m.member_id
    """)
    borrowings = []
    for row in cursor.fetchall():
        borrowings.append((row[0], row[1], row[2], row[3], row[4], get_borrowing_status(row)))
    return render_template("borrowings.html", borrowings=borrowings, today=date.today())

@app.route("/add_borrowing", methods=["GET", "POST"])
def add_borrowing():
    if not session.get("logged_in"):
        return redirect("/")
    cursor = db.cursor()
    error = None
    if request.method == "POST":
        book_id = request.form.get("book_id", "").strip()
        member_id = request.form.get("member_id", "").strip()
        borrow_date = request.form.get("borrow_date", "").strip()
        return_date = request.form.get("return_date", "").strip()
        if not book_id or not member_id or not borrow_date or not return_date:
            error = "Please fill in all borrowing fields."
        elif return_date < borrow_date:
            error = "Return date must be on or after the borrow date."
        else:
            cursor.execute("SELECT quantity FROM books WHERE book_id=%s", (book_id,))
            book = cursor.fetchone()
            if not book:
                error = "Selected book was not found."
            elif book[0] <= 0:
                error = "This book is currently out of stock."
            else:
                cursor.execute(
                    "INSERT INTO borrowings (book_id, member_id, borrow_date, return_date, status) VALUES (%s, %s, %s, %s, 'borrowed')",
                    (book_id, member_id, borrow_date, return_date)
                )
                cursor.execute("UPDATE books SET quantity = quantity - 1 WHERE book_id=%s", (book_id,))
                db.commit()
                flash("Borrowing record added successfully.", "success")
                return redirect("/borrowings")
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    cursor.execute("SELECT * FROM members")
    members = cursor.fetchall()
    return render_template("add_borrowing.html", books=books, members=members, error=error)

@app.route("/edit_borrowing/<int:id>", methods=["GET", "POST"])
def edit_borrowing(id):
    if not session.get("logged_in"):
        return redirect("/")
    cursor = db.cursor()
    cursor.execute("SELECT borrow_id, book_id, member_id, borrow_date, return_date, status FROM borrowings WHERE borrow_id=%s", (id,))
    borrowing = cursor.fetchone()
    if request.method == "POST":
        book_id = request.form.get("book_id", "").strip()
        member_id = request.form.get("member_id", "").strip()
        borrow_date = request.form.get("borrow_date", "").strip()
        return_date = request.form.get("return_date", "").strip()
        error = None
        if not book_id or not member_id or not borrow_date or not return_date:
            error = "Please fill in all borrowing fields."
        elif return_date < borrow_date:
            error = "Return date must be on or after the borrow date."
        else:
            current_book_id = borrowing[1]
            current_status = borrowing[5] if borrowing[5] else "borrowed"
            if current_status != "returned":
                if str(book_id) != str(current_book_id):
                    cursor.execute("SELECT quantity FROM books WHERE book_id=%s", (book_id,))
                    new_book = cursor.fetchone()
                    if not new_book:
                        error = "Selected book was not found."
                    elif new_book[0] <= 0:
                        error = "This book is currently out of stock."
                    else:
                        cursor.execute("UPDATE books SET quantity = quantity + 1 WHERE book_id=%s", (current_book_id,))
                        cursor.execute("UPDATE books SET quantity = quantity - 1 WHERE book_id=%s", (book_id,))
                if not error:
                    cursor.execute(
                        "UPDATE borrowings SET book_id=%s, member_id=%s, borrow_date=%s, return_date=%s WHERE borrow_id=%s",
                        (book_id, member_id, borrow_date, return_date, id)
                    )
                    db.commit()
                    flash("Borrowing record updated successfully.", "success")
                    return redirect("/borrowings")
            else:
                cursor.execute(
                    "UPDATE borrowings SET book_id=%s, member_id=%s, borrow_date=%s, return_date=%s WHERE borrow_id=%s",
                    (book_id, member_id, borrow_date, return_date, id)
                )
                db.commit()
                flash("Borrowing record updated successfully.", "success")
                return redirect("/borrowings")
        borrowing = (id, int(book_id) if book_id.isdigit() else book_id, int(member_id) if member_id.isdigit() else member_id, borrow_date, return_date, borrowing[5] if borrowing else "borrowed")
        cursor.execute("SELECT * FROM books")
        books = cursor.fetchall()
        cursor.execute("SELECT * FROM members")
        members = cursor.fetchall()
        return render_template("edit_borrowing.html", borrowing=borrowing, books=books, members=members, error=error)
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    cursor.execute("SELECT * FROM members")
    members = cursor.fetchall()
    return render_template("edit_borrowing.html", borrowing=borrowing, books=books, members=members)


@app.route("/return_borrowing/<int:id>")
def return_borrowing(id):
    if not session.get("logged_in"):
        return redirect("/")
    cursor = db.cursor()
    cursor.execute("SELECT book_id, status FROM borrowings WHERE borrow_id=%s", (id,))
    borrowing = cursor.fetchone()
    if not borrowing:
        flash("Borrowing record not found.", "error")
        return redirect("/borrowings")
    if borrowing[1] == "returned":
        flash("This borrowing is already marked as returned.", "error")
        return redirect("/borrowings")
    cursor.execute("UPDATE borrowings SET status='returned' WHERE borrow_id=%s", (id,))
    cursor.execute("UPDATE books SET quantity = quantity + 1 WHERE book_id=%s", (borrowing[0],))
    db.commit()
    flash("Book returned successfully.", "success")
    return redirect("/borrowings")

@app.route("/delete_borrowing/<int:id>")
def delete_borrowing(id):
    if not session.get("logged_in"):
        return redirect("/")
    cursor = db.cursor()
    cursor.execute("SELECT book_id, status FROM borrowings WHERE borrow_id=%s", (id,))
    borrowing = cursor.fetchone()
    if borrowing and borrowing[1] != "returned":
        cursor.execute("UPDATE books SET quantity = quantity + 1 WHERE book_id=%s", (borrowing[0],))
    cursor.execute("DELETE FROM borrowings WHERE borrow_id=%s", (id,))
    db.commit()
    return redirect("/borrowings")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
