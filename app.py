from flask import Flask
from flask import template_rendered, redirect, request, render_template, url_for
import sqlite3

app = Flask(__name__)


def insert_db(login, password):
    con = sqlite3.connect("server/users.db")
    cur = con.cursor()
    try:
        cur.execute("""
            INSERT INTO users(user_login, user_password)
            VALUES (?, ?)
        """, (login, password))
        con.commit()
        return True
    except sqlite3.IntegrityError as e:
        return False
    finally:
        con.close()


@app.route("/register")
def register_index():
    return render_template('register.html')


@app.route("/register", methods=["POST"])
def register_logic():
    user_login = request.form["login"]
    user_password = request.form["password"]
    if insert_db(user_login, user_password):
        return "Вы успешно зарегестрированы"

    return "Такой пользователь уже существует, регистрация не прошла"


@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_logic():
    login = request.form["login"]
    password = request.form["password"]

    con = sqlite3.connect("server/users.db")
    cur = con.cursor()
    user_id = con.execute("""
        SELECT user_id 
          FROM users
         WHERE user_login = ? AND user_password = ?
    """, (login, password)).fetchone()

    if user_id is not None:
        user_id = user_id[0]
        return redirect(url_for("hello_index", username=login))
    else:
        return "Неверное имя пользователя или пароль"


@app.route("/hello/<username>")
def hello_index(username):
    return f"Вы зашли под пользователем {username}"


if __name__ == '__main__':
    con = sqlite3.connect("server/users.db")
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_login TEXT UNIQUE,
            user_password TEXT
        );
    """)
    con.commit()
    con.close()

    app.run(debug=True)
