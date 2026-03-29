import tkinter as tk
import mysql.connector

# DB connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="YOUR_PASSWORD",
    database="library_db"
)
cursor = db.cursor()

# Add user
def add_user():
    uid = user_id_entry.get()
    name = name_entry.get()
    email = email_entry.get()

    cursor.execute(
        "INSERT INTO usersdatabase (lid, name, email) VALUES (%s, %s, %s)",
        (uid, name, email)
    )
    db.commit()
    print("User Added")

# Add book
def add_book():
    bid = book_id_entry.get()
    bookname = book_name_entry.get()

    cursor.execute(
        "INSERT INTO bookdatabase (uid, bookname) VALUES (%s, %s)",
        (bid, bookname)
    )
    db.commit()
    print("Book Added")

# GUI
root = tk.Tk()
root.title("Admin Panel")

# USER
tk.Label(root, text="User ID").grid(row=0)
tk.Label(root, text="Name").grid(row=1)
tk.Label(root, text="Email").grid(row=2)

user_id_entry = tk.Entry(root)
name_entry = tk.Entry(root)
email_entry = tk.Entry(root)

user_id_entry.grid(row=0, column=1)
name_entry.grid(row=1, column=1)
email_entry.grid(row=2, column=1)

tk.Button(root, text="Add User", command=add_user).grid(row=3)

# BOOK
tk.Label(root, text="Book ID").grid(row=4)
tk.Label(root, text="Book Name").grid(row=5)

book_id_entry = tk.Entry(root)
book_name_entry = tk.Entry(root)

book_id_entry.grid(row=4, column=1)
book_name_entry.grid(row=5, column=1)

tk.Button(root, text="Add Book", command=add_book).grid(row=6)

root.mainloop()