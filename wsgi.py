from app import app
from scheduler import init_scheduler

if __name__ == "__main__":
    app.run()
else:
    # Initialize scheduler when running under WSGI server
    init_scheduler(app)