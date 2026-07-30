from flask import Flask
from flask_cors import CORS
from shared.config import settings
from .routes import bp

def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    CORS(app, origins=settings.CORS_ORIGINS)
    app.register_blueprint(bp, url_prefix=f"{settings.API_PREFIX}/daraja")
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8004, debug=settings.DEBUG)
