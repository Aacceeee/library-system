-- Insert sample BOOKS data
INSERT INTO books (title, author, genre, quantity) VALUES
('The Great Gatsby', 'F. Scott Fitzgerald', 'Fiction', 5),
('To Kill a Mockingbird', 'Harper Lee', 'Fiction', 3),
('A Brief History of Time', 'Stephen Hawking', 'Science', 4),
('Pride and Prejudice', 'Jane Austen', 'Romance', 6),
('The Hobbit', 'J.R.R. Tolkien', 'Fantasy', 4);

-- Insert sample MEMBERS data
INSERT INTO members (name, email, phone) VALUES
('Juan Dela Cruz', 'juan@email.com', '09123456789'),
('Maria Santos', 'maria@email.com', '09198765432'),
('Pedro Reyes', 'pedro@email.com', '09111222333'),
('Ana Garcia', 'ana@email.com', '09144556677');

-- Insert sample BORROWINGS data
INSERT INTO borrowings (book_id, member_id, borrow_date, return_date) VALUES
(1, 1, '2025-01-01', '2025-01-15'),
(2, 2, '2025-01-05', '2025-01-20'),
(3, 3, '2025-01-10', '2025-01-25');