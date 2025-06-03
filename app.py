from pkg import create_app

app = create_app()

application = app

if __name__ == '__main__':
    app.config.from_pyfile("config.py")
    app.run(debug=True, host='0.0.0.0', port=3600)