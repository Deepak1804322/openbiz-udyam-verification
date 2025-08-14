# run.py - simple launcher
from app import app
if __name__ == '__main__':
    # when executed, this will run Flask's built-in server
    app.run(host='0.0.0.0', port=8000, debug=True)
