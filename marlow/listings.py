"""Listings API and pages."""
import os

from flask import Blueprint, abort, current_app, jsonify, request, send_file

from .db import get_db, to_listing
from .templating import listing_badge
from vendor.floorplan import decode_floorplan

bp = Blueprint("listings", __name__)


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
    rows = (
        get_db()
        .execute(
            "SELECT * FROM listings WHERE title LIKE '%' || ? || '%' ORDER BY id",
            (q,),
        )
        .fetchall()
    )
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
    plan = decode_floorplan(request.get_data())
    return jsonify({"rooms": len(plan.get("rooms", []))})
