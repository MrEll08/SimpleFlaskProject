# Flask SQLite App

A simple Flask web application using SQLite, fully containerized with Docker.

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/MrEll08/SimpleFlaskProject.git your-path
cd your-path
```

### 2. Build the Docker Image
```bash
docker build -t my_flask_app .
```

### 3. Run the Container
```bash
docker run -p 23952:5000 --name flask_app my_flask_app
```
Now open your browser and go to:
```
http://localhost:23952
```

## Project structure
```bash
.
├── app.py                 # Main Flask app
├── create_database.py     # Creates and initializes the database
├── Dockerfile             # Docker build instructions
├── requirements.txt       # Python dependencies
├── server/
│   └── users.db           # SQLite database file
├── static
│   └── uploads            
│       └── ...            # Pictures from user posts
├── templates
│   └── ...                HTML pages
└── README.md              # Project instructions
```

## Dependencies

All Python dependencies are listed in `requirements.txt` and are installed automatically during the Docker build process.


## Admin User

On the first run, `create_database.py` adds a user named `maximka` to the list of admins.  
However, this user is not yet registered in the system.  

To complete the setup:
1. Register a new account with the username `maximka`.
2. Log in as `maximka` — this account will now have admin (and superuser) privileges.

You can add other admins by logging in as `maximka` and using the admin interface.


## Port Notes
If port 23952 is already in use on your machine, you can map the container’s port to another one:
```bash
docker run -p 8080:5000 --name flask_app my_flask_app
```
Then access the app at:
```
http://localhost:8080
```

## Available Pages

| Route        | Description                                                                 |
|--------------|-----------------------------------------------------------------------------|
| `/`          | Home page of the application                                                |
| `/register`  | User registration page                                                      |
| `/login`     | Login page for existing users                                               |
| `/feed`      | Public feed where users can see posts                                       |
| `/admin`     | Admin interface for managing the feed (admins can delete messages)          |
| `/user_list` | List of all users (admins can ban or unban users from here)                 |