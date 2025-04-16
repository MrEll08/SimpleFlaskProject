from flask import Flask
from flask import template_rendered

app = Flask(__name__)

@app.route("/hello")
def hello_world():
    return "hello world"

@app.route("/users/<username>")
def hello_user(username: str):
    return f"Hello, {username}"

if __name__ == '__main__':
    app.run(debug=True)