from pkg import create_app, socketio

app = create_app()

application = app 

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=3600)