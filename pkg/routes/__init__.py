def register_blueprints(app):
    from .main import main_bp
    from .users import users_bp
    from .business import business_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(business_bp)
