import sqlite3

con = sqlite3.connect("server/users.db")
cur = con.cursor()
cur.executescript("""
                  CREATE TABLE IF NOT EXISTS user
                  (
                      user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_login    TEXT UNIQUE,
                      user_password TEXT    NOT NULL DEFAULT '',
                      banned        INTEGER NOT NULL DEFAULT 0
                  );
                  CREATE TABLE IF NOT EXISTS post
                  (
                      post_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_login TEXT,
                      post_text  TEXT,
                      post_image TEXT DEFAULT "no image here",

                      FOREIGN KEY (user_login) REFERENCES user (user_login)
                  );
                  CREATE TABLE IF NOT EXISTS admin
                  (
                      admin_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_login TEXT UNIQUE,

                      FOREIGN KEY (user_login) REFERENCES "old_user" (user_login)
                  );
                  INSERT OR IGNORE INTO admin (user_login)
                  VALUES ('maximka');
                  """)
con.commit()
con.close()
