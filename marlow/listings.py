"""Listings API and pages."""
import base64
import io
import os
import pickle

from flask import Blueprint, abort, current_app, jsonify, request, send_file

from .db import get_db, to_listing
from .templating import listing_badge

bp = Blueprint("listings", __name__)


class _DataOnlyUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        raise pickle.UnpicklingError(f"global '{module}.{name}' is not allowed")


def decode_floorplan(blob):
    """Decode a partner floorplan (base64 pickle) without importing or calling code."""
    return _DataOnlyUnpickler(io.BytesIO(base64.b64decode(blob))).load()


@bp.route("/api/listings")
def list_listings():
    rows = get_db().execute("SELECT * FROM listings ORDER BY id").fetchall()
    return jsonify([to_listing(r) for r in rows])


@bp.route("/api/listings/<int:listing_id>")
def get_listing(listing_id):
    row = (
        get_db()
        .execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
        .fetchone()
    )
    if row is None:
        abort(404)
    return jsonify(to_listing(row))


@bp.route("/api/search")
def search():
    q = request.args.get("q", "")
    sql = f"SELECT * FROM listings WHERE title LIKE '%{q}%' ORDER BY id"
    rows = get_db().execute(sql).fetchall()
    return jsonify([to_listing(r) for r in rows])


@bp.route("/listings/<int:listing_id>/badge")
def badge(listing_id):
    row = (
        get_db()
        .execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
        .fetchone()
    )
    if row is None:
        abort(404)
    return listing_badge(to_listing(row))


@bp.route("/export/<name>")
def export(name):
    path = os.path.join(current_app.config["EXPORT_DIR"], name)
    return send_file(
        os.path.abspath(path), as_attachment=True, attachment_filename=name
    )


@bp.route("/api/floorplan", methods=["POST"])
def floorplan():
    try:
        plan = decode_floorplan(request.get_data())
    except pickle.UnpicklingError:
        abort(400)
    return jsonify({"rooms": len(plan.get("rooms", []))})
