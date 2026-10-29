"""Marlow Lettings backend."""
import decimal
import json

from flask import Flask


class MoneyEncoder(json.JSONEncoder):
    """Rents are stored as Decimal; the API returns them as numbers."""

    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super().default(o)


def create_app(db_path=None):
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path or "marlow.db"
    app.config["EXPORT_DIR"] = "exports"
    app.json_encoder = MoneyEncoder

    from . import db, listings

    db.init_app(app)
    app.register_blueprint(listings.bp)
    return app
