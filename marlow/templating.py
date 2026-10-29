"""Small HTML snippets embedded by partner sites."""


def listing_badge(listing):
    from jinja2 import Markup, escape

    title = escape(listing["title"])
    return Markup(
        f'<div class="marlow-badge"><b>{title}</b>'
        f" &middot; {listing['city']} &middot; &pound;{listing['rent']}/mo</div>"
    )
