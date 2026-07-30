from flask import Flask, g
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shared.config import settings
from .models import Base
from .routes import bp

engine = create_engine(
    settings.DATABASE_URL.replace("+asyncpg", "").replace("postgresql", "postgresql"),
    pool_size=10, max_overflow=5,
)
SessionLocal = sessionmaker(bind=engine)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    CORS(app, origins=settings.CORS_ORIGINS)

    Base.metadata.create_all(bind=engine)

    @app.before_request
    def before_request():
        g.db = SessionLocal()

    @app.teardown_request
    def teardown_request(exception=None):
        db = g.pop("db", None)
        if db is not None:
            if exception:
                db.rollback()
            else:
                db.commit()
            db.close()

    app.register_blueprint(bp, url_prefix=f"{settings.API_PREFIX}/auth")
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8001, debug=settings.DEBUG)