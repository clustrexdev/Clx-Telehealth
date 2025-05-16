from modul import app

# Comment the handler in init.py while testing in local development.
if __name__ == "__main__":
    app.run(host="0.0.0.0",port=3000, debug=True)

