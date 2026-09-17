import os

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "your_local_password"),
    "database": os.environ.get("DB_NAME", "studysync"),
    "port": int(os.environ.get("DB_PORT", 3306))
}