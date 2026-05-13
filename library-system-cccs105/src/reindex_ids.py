import mysql.connector


def main():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="cccs105",
    )
    cursor = db.cursor(dictionary=True)

    try:
        # Read existing data in stable order.
        cursor.execute("SELECT book_id, title, author, genre, quantity FROM books ORDER BY book_id")
        books = cursor.fetchall()

        cursor.execute("SELECT member_id, name, email, phone FROM members ORDER BY member_id")
        members = cursor.fetchall()

        cursor.execute(
            "SELECT borrow_id, book_id, member_id, borrow_date, return_date, status "
            "FROM borrowings ORDER BY borrow_id"
        )
        borrowings = cursor.fetchall()

        # Rebuild IDs by truncating and reinserting.
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("TRUNCATE TABLE borrowings")
        cursor.execute("TRUNCATE TABLE books")
        cursor.execute("TRUNCATE TABLE members")

        book_id_map = {}
        for row in books:
            cursor.execute(
                "INSERT INTO books (title, author, genre, quantity) VALUES (%s, %s, %s, %s)",
                (row["title"], row["author"], row["genre"], row["quantity"]),
            )
            book_id_map[row["book_id"]] = cursor.lastrowid

        member_id_map = {}
        for row in members:
            cursor.execute(
                "INSERT INTO members (name, email, phone) VALUES (%s, %s, %s)",
                (row["name"], row["email"], row["phone"]),
            )
            member_id_map[row["member_id"]] = cursor.lastrowid

        for row in borrowings:
            new_book_id = book_id_map[row["book_id"]]
            new_member_id = member_id_map[row["member_id"]]
            cursor.execute(
                "INSERT INTO borrowings (book_id, member_id, borrow_date, return_date, status) "
                "VALUES (%s, %s, %s, %s, %s)",
                (new_book_id, new_member_id, row["borrow_date"], row["return_date"], row["status"]),
            )

        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        db.commit()

        cursor.execute("SELECT COUNT(*), MIN(book_id), MAX(book_id) FROM books")
        books_stats = cursor.fetchone()
        cursor.execute("SELECT COUNT(*), MIN(member_id), MAX(member_id) FROM members")
        members_stats = cursor.fetchone()
        cursor.execute("SELECT COUNT(*), MIN(borrow_id), MAX(borrow_id) FROM borrowings")
        borrowings_stats = cursor.fetchone()

        print(
            f"books: {books_stats['COUNT(*)']} rows ({books_stats['MIN(book_id)']}-{books_stats['MAX(book_id)']})"
        )
        print(
            f"members: {members_stats['COUNT(*)']} rows ({members_stats['MIN(member_id)']}-{members_stats['MAX(member_id)']})"
        )
        print(
            f"borrowings: {borrowings_stats['COUNT(*)']} rows ({borrowings_stats['MIN(borrow_id)']}-{borrowings_stats['MAX(borrow_id)']})"
        )

    finally:
        cursor.close()
        db.close()


if __name__ == "__main__":
    main()
