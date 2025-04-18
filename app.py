import os
from functools import wraps
from urllib.parse import urlparse

from flask import Flask, session, flash
from flask import redirect, request, render_template, url_for
import sqlite3

import jwt
import datetime
from flask import make_response
from mistune.plugins.ruby import render_ruby
from werkzeug.utils import secure_filename

SECRET_KEY = "0YHQtdC60YDQtdGC0L3Ri9C5INC60LvRjtGH"

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["UPLOAD_FOLDER"] = "static/uploads/"


def get_user():
    flag, payload = check_cookie()
    if flag != 1:
        return None
    return payload["user_name"]


def is_admin(user):
    if user is None:
        return False
    flag, payload = check_cookie()
    if flag != 1:
        return False
    con = sqlite3.connect("server/users.db")
    cur = con.cursor()
    admin_id = cur.execute("""
                           SELECT admin_id
                           FROM admin
                           WHERE user_login = ?
                           """, (user,)).fetchone()
    return admin_id is not None

@app.route("/bad_request")
def bad_request_index():
    return render_template("bad_request.html", text=session["bad_request"])


def bad_request(text):
    session["bad_request"] = text
    return redirect("/bad_request")

def only_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_user()
        if not is_admin(user):
            return bad_request("Действие запрещено")
        return func(*args, **kwargs)

    return wrapper


def only_superuser(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_user()
        if user != "maximka":
            return bad_request("Действие запрещено")
        return func(*args, **kwargs)

    return wrapper


def only_normal_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_user()
        if user is None:
            return render_template("login_required.html")

        con = sqlite3.connect("server/users.db")
        cur = con.cursor()
        is_banned = cur.execute("""SELECT banned
                                   FROM user
                                   WHERE user_login = ?""", (user,)).fetchone()[0]
        if is_banned:
            return bad_request("Вы не можете этого сделать, так как были забанены")
        return func(*args, **kwargs)
    return wrapper


def insert_db(login, password):
    con = sqlite3.connect("server/users.db")
    cur = con.cursor()
    try:
        cur.execute("""
                    INSERT INTO user(user_login, user_password)
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
        flash("Вы успешно зарегестрированы, теперь войдите")
        return redirect("/login")

    return bad_request("Такой пользователь уже существует, регистрация не прошла")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_logic():
    login = request.form["login"]
    password = request.form["password"]

    con = sqlite3.connect("server/users.db")
    cur = con.cursor()
    user = cur.execute("""
                       SELECT user_id
                       FROM user
                       WHERE user_login = ?
                         AND user_password = ?
                       """, (login, password)).fetchone()
    con.close()

    if user is not None:
        token_payload = {
            "user_name": login,
        }
        token = jwt.encode(token_payload, app.config["SECRET_KEY"], algorithm="HS256")

        response = make_response(redirect(url_for("hello_index", username=login)))
        response.set_cookie("jwt", token, httponly=True, max_age=3600)

        return response
    else:
        return bad_request("Неверное имя пользователя или пароль")


@app.route("/hello")
@only_normal_user
def hello_index():
    user = get_user()
    return render_template("hello.html", username=user)


@app.route("/")
def home_index():
    return render_template("home.html")


def get_posts():
    con = sqlite3.connect("server/users.db")
    cur = con.cursor()
    posts = cur.execute("""
                        SELECT *
                        FROM (SELECT *
                              FROM post
                              ORDER BY post_id DESC
                              LIMIT 20)
                        ORDER BY post_id
                        """).fetchall()
    con.close()
    return posts


@app.route("/feed")
def feed():
    posts = get_posts()
    user = get_user()
    return render_template("feed.html", current_user=user or "не вошли", posts=posts)


@app.route("/make_post", methods=["POST"])
@only_normal_user
def make_post_logic():
    user = get_user()
    post = request.form["post"]

    file = request.files.get("image")
    savepath = None
    if file and file.filename != "":
        filename = secure_filename(file.filename)
        savepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(savepath)

    con = sqlite3.connect("server/users.db")
    cur = con.cursor()

    cur.execute("""
                INSERT INTO post(user_login, post_text, post_image)
                VALUES (?, ?, ?)""", (user, post, savepath or "no image here"))

    con.commit()
    con.close()
    return redirect(request.referrer + "#make_post")


@app.route("/admin")
@only_admin
def admin():
    posts = get_posts()
    user = get_user()
    return render_template("admin.html", current_user=user or "не вошли", posts=posts)


@app.route("/delete_post", methods=["POST"])
@only_admin
def delete_post():
    post_id = request.form["post_id"]

    con = sqlite3.connect("server/users.db")
    cur = con.cursor()
    cur.execute("""
                DELETE
                FROM post
                WHERE post_id = ?
                """, (post_id,))
    con.commit()
    con.close()

    return redirect("/admin#make_post")


@app.route("/user_list")
def user_list():
    user = get_user()

    con = sqlite3.connect("server/users.db")
    cur = con.cursor()
    admins = cur.execute("""
                         SELECT user_login
                         FROM admin""").fetchall()
    users = cur.execute("""
                        SELECT user_login
                        FROM user
                                 LEFT JOIN admin USING (user_login)
                        WHERE admin_id IS NULL
                          AND banned = 0
                        """).fetchall()
    banned = cur.execute("""
                         SELECT user_login
                         FROM user
                         WHERE banned = 1
                         """).fetchall()
    if user == "maximka":
        return render_template("user_list_super.html",
                               current_user=user,
                               admins=admins, users=users, banned_users=banned)
    if is_admin(user):
        return render_template("user_list_admin.html",
                               current_user=user,
                               admins=admins, users=users, banned_users=banned)

    return render_template("user_list_standart.html",
                           current_user=user or "вы не вошли в систему",
                           admins=admins, users=users, banned_users=banned)


@app.route("/toggle_user_ban", methods=["POST"])
@only_admin
def toggle_user_ban():
    user_to_toggle = request.form["user_to_toggle"]
    con = sqlite3.connect("server/users.db")
    cur = con.cursor()
    now_state = cur.execute("""
                            SELECT banned
                            FROM user
                            WHERE user_login = ?
                            """, (user_to_toggle,)).fetchone()
    if now_state is None:
        return bad_request("Вы пытаетесь применить команду для неверного пользователя")
    now_state = now_state[0]
    cur.execute("""
                UPDATE user
                SET banned = ?
                WHERE user_login = ?
                """, (now_state ^ 1, user_to_toggle))
    con.commit()
    con.close()
    return redirect("/user_list")


@app.route("/make_admin", methods=["POST"])
@only_superuser
def make_admin():
    user_to_promote = request.form["user_to_promote"]

    con = sqlite3.connect("server/users.db")
    cur = con.cursor()
    cur.execute("""
                INSERT INTO admin(user_login)
                VALUES (?)
                """, (user_to_promote,))
    con.commit()
    con.close()
    return redirect("/user_list")


@app.route("/disable_admin", methods=["POST"])
@only_superuser
def disable_admin():
    user_to_disable = request.form["user_to_disable"]
    con = sqlite3.connect("server/users.db")
    cur = con.cursor()
    cur.execute("""
                DELETE
                FROM admin
                WHERE user_login = ?
                """, (user_to_disable,))
    con.commit()
    con.close()
    return redirect("/user_list")


if __name__ == '__main__':
    app.run(debug=True)
