import mysql.connector
from datetime import date, timedelta
import random

# DB config (matches app.py)
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="cccs105"
)

cursor = db.cursor()

def get_member_ids():
    cursor.execute("SELECT member_id FROM members ORDER BY member_id")
    return [r[0] for r in cursor.fetchall()]

def get_book_ids():
    cursor.execute("SELECT book_id FROM books ORDER BY book_id")
    return [r[0] for r in cursor.fetchall()]

def add_members(n, start_index):
    for i in range(start_index, start_index + n):
        name = f"Seed Member {i}"
        email = f"seed_member_{i}@example.com"
        phone = f"090{1000000 + i}"
        cursor.execute("INSERT INTO members (name, email, phone) VALUES (%s, %s, %s)", (name, email, phone))

def add_books(n, start_index):
    for i in range(start_index, start_index + n):
        title = f"Seed Book {i}"
        author = "Seed Author"
        genre = "Misc"
        quantity = 1
        cursor.execute("INSERT INTO books (title, author, genre, quantity) VALUES (%s, %s, %s, %s)", (title, author, genre, quantity))

def ensure_book_available(book_id):
    cursor.execute("SELECT quantity FROM books WHERE book_id=%s", (book_id,))
    q = cursor.fetchone()
    if not q:
        return
    if q[0] <= 0:
        cursor.execute("UPDATE books SET quantity = 1 WHERE book_id=%s", (book_id,))

def main():
    # Ensure total members will be 60 and create 50 borrowing members
    cursor.execute("SELECT COUNT(*) FROM members")
    current_members = cursor.fetchone()[0]
    target_total = 60
    to_add = max(0, target_total - current_members)

    # We'll add members to reach total 60
    if to_add > 0:
        print(f"Adding {to_add} new members to reach {target_total} total members...")
        add_members(to_add, current_members + 1)
        db.commit()

    # Refresh member ids
    member_ids = get_member_ids()
    if len(member_ids) < 50:
        raise SystemExit("Not enough members to select 50 borrowers after seeding; aborting.")

    # Choose 50 distinct members to be borrowers. Prefer the newest members.
    borrowers = member_ids[-50:]

    # Ensure we have at least 50 distinct books
    cursor.execute("SELECT COUNT(*) FROM books")
    book_count = cursor.fetchone()[0]
    if book_count < 50:
        need_books = 50 - book_count
        print(f"Adding {need_books} seed books to reach 50 unique books...")
        add_books(need_books, book_count + 1)
        db.commit()

    book_ids = get_book_ids()
    if len(book_ids) < 50:
        raise SystemExit("Failed to ensure 50 books are present; aborting.")

    selected_books = book_ids[:50]

    # Create borrowings: each borrower borrows a unique book
    today = date.today()
    for member_id, book_id in zip(borrowers, selected_books):
        ensure_book_available(book_id)
        borrow_date = today - timedelta(days=random.randint(1, 10))
        return_date = borrow_date + timedelta(days=14)
        cursor.execute(
            "INSERT INTO borrowings (book_id, member_id, borrow_date, return_date, status) VALUES (%s, %s, %s, %s, 'borrowed')",
            (book_id, member_id, borrow_date, return_date)
        )
        cursor.execute("UPDATE books SET quantity = quantity - 1 WHERE book_id=%s", (book_id,))

    db.commit()
    cursor.execute("SELECT COUNT(*) FROM members")
    total_members = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM borrowings")
    total_borrowings = cursor.fetchone()[0]
    print(f"Done. Total members: {total_members}, total borrowings: {total_borrowings}")

if __name__ == '__main__':
    main()
