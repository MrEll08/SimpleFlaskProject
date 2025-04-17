from flask import Flask
from flask import redirect, request, render_template, url_for
import sqlite3

import jwt
import datetime
from flask import make_response
from mistune.plugins.ruby import render_ruby

SECRET_KEY = "your_secret_key_here"

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY  # Замени на надёжный ключ


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


def check_cookie():
    token = request.cookies.get("jwt")
    if token is None:
        return [0, None]
    print(token)
    try:
        # Проверка подписи
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return [1, payload]
    except jwt.ExpiredSignatureError:
        return [2, None]
    except jwt.InvalidSignatureError:
        return [3, None]
    except jwt.DecodeError:
        return [4, None]
    except jwt.InvalidTokenError:
        return [5, None]


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
    check_cookie()
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_logic():
    login = request.form["login"]
    password = request.form["password"]

    con = sqlite3.connect("server/users.db")
    cur = con.cursor()
    user = cur.execute("""
                       SELECT user_id
                       FROM users
                       WHERE user_login = ?
                         AND user_password = ?
                       """, (login, password)).fetchone()
    con.close()

    if user is not None:
        token_payload = {
            "user": login,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(token_payload, app.config["SECRET_KEY"], algorithm="HS256")

        response = make_response(redirect(url_for("hello_index", username=login)))
        response.set_cookie("jwt", token, httponly=True, max_age=3600)

        return response
    else:
        return "Неверное имя пользователя или пароль"


@app.route("/hello/<username>")
def hello_index(username):
    return f"Вы зашли под пользователем {username}"


@app.route("/feed")
def feed():
    con = sqlite3.connect("server/users.db")
    cur = con.cursor()
    posts = cur.execute("""
                        SELECT post_id, user_login, post_text
                        FROM (SELECT *
                              FROM posts
                              ORDER BY post_id DESC
                              LIMIT 20)
                        ORDER BY post_id
                        """).fetchall()
    con.close()
    if len(posts) == 0:
        return "Пока не было постов"
    return render_template("feed.html", posts=posts)


@app.route("/make_post", methods=["POST"])
def make_post_logic():
    flag, jwt_payload = check_cookie()
    if flag != 1:
        return "Необходимо корректно залогиниться, чтобы делать посты"
    post = request.form["post"]
    user_login = jwt_payload["user"]

    con = sqlite3.connect("server/users.db")
    cur = con.cursor()

    cur.execute("""
                INSERT INTO posts(user_login, post_text)
                VALUES (?, ?)""", (user_login, post))

    con.commit()
    con.close()
    return redirect("/feed#make_post")


if __name__ == '__main__':
    con = sqlite3.connect("server/users.db")
    cur = con.cursor()
    cur.executescript("""
                      CREATE TABLE IF NOT EXISTS users
                      (
                          user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                          user_login    TEXT UNIQUE,
                          user_password TEXT
                      );
                      CREATE TABLE IF NOT EXISTS posts
                      (
                          post_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                          user_login INTEGER,
                          post_text  TEXT
                      );
                      """)
    con.commit()
    con.close()

    app.run(debug=True)
