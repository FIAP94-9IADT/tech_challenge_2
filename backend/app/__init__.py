import logging
import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS


def create_app() -> Flask:
    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = Flask(__name__)


    CORS(app, origins=os.environ.get("CORS_ORIGINS", "*"))

    from .api.routes import api

    app.register_blueprint(api)

    return app
