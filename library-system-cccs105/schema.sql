-- LIBRARY MANAGEMENT SYSTEM - DATABASE SCHEMA
-- Course: CCCS 105 - Information Management

CREATE DATABASE IF NOT EXISTS cccs105;
USE cccs105;

-- TABLE: BOOKS - Stores book information
CREATE TABLE IF NOT EXISTS books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    genre VARCHAR(100) NOT NULL,
    quantity INT NOT NULL
);

-- TABLE: MEMBERS - Stores member information
CREATE TABLE IF NOT EXISTS members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(12) NOT NULL
);

-- TABLE: BORROWINGS - Records borrowing transactions
CREATE TABLE IF NOT EXISTS borrowings (
    borrow_id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    member_id INT NOT NULL,
    borrow_date DATE NOT NULL,
    return_date DATE NOT NULL,
    CONSTRAINT fk_book
        FOREIGN KEY (book_id)
        REFERENCES books(book_id),
    CONSTRAINT fk_member
        FOREIGN KEY (member_id)
        REFERENCES members(member_id)
);