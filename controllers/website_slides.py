# controllers/website_slides.py
from odoo import http
from odoo.http import request
from odoo.addons.website_slides.controllers.main import WebsiteSlides

# IMPORTANT: Use your module's technical name here (from your folder).
# Your traceback shows: /opt/odoo/custom/addons/habit_sequential_learning/...
# So the XMLID should be:
TEMPLATE_XMLID = "habit_sequential_learning.locked_lesson_template"


def _render_locked(slide):
    """
    Render the custom locked page with contextual info about when this
    lesson will unlock for the current user.
    """
    user = request.env.user
    info = slide.next_unlock_info(user)
    lesson_name = slide.name or "Lesson"

    unlock_str = ""
    if info.get("unlock_dt_local"):
        dt = info["unlock_dt_local"]
        try:
            unlock_str = dt.strftime("%a, %d %b %Y — %I:%M %p %Z")
        except Exception:
            unlock_str = dt.strftime("%a, %d %b %Y — %I:%M %p")

    qcontext = {
        "lesson_name": lesson_name,
        "unlock_message": info.get("unlock_message") or "",
        "unlock_datetime_str": unlock_str,
    }
    return request.render(TEMPLATE_XMLID, qcontext)


class WebsiteSlidesGate(WebsiteSlides):
    """
    Gate common slide routes. If a slide is locked for the current user,
    show our custom page instead of letting core code attempt to mark
    completion (which would raise AccessError -> 403).
    """

    # NEW: This is the route your logs show being called.
    # In Odoo 18 it's typically:
    #   /slides/slide/<model("slide.slide"):slide>
    @http.route()
    def slide_view(self, slide, **kw):
        if slide and slide.exists():
            user = request.env.user
            if not slide.is_unlocked_for(user):
                return _render_locked(slide)
        # Unlocked -> proceed with normal behavior (may mark completed, etc.)
        return super().slide_view(slide, **kw)

    # These two are kept for other themes/routes that call them.
    @http.route()
    def slide_slide_view(self, channel_id, slide_id, **kw):
        slide = request.env["slide.slide"].browse(int(slide_id))
        if slide.exists():
            user = request.env.user
            if not slide.is_unlocked_for(user):
                return _render_locked(slide)
        return super().slide_slide_view(channel_id, slide_id, **kw)

    @http.route()
    def slide_slide(self, slide_id, **kw):
        slide = request.env["slide.slide"].browse(int(slide_id))
        if slide.exists():
            user = request.env.user
            if not slide.is_unlocked_for(user):
                return _render_locked(slide)
        return super().slide_slide(slide_id, **kw)

    # Some routes call this one with typed params
    @http.route()
    def slide(self, channel=None, slide=None, **kw):
        s = slide if getattr(slide, "id", False) else None
        if not s and "slide_id" in kw:
            s = request.env["slide.slide"].browse(int(kw["slide_id"]))
        if s and s.exists():
            user = request.env.user
            if not s.is_unlocked_for(user):
                return _render_locked(s)
        return super().slide(channel=channel, slide=slide, **kw)

    @http.route(
        "/sequentiallearning/reset_progress",
        type="http",
        auth="user",
        methods=["POST"],
        website=True,
        csrf=True,
    )
    def reset_progress(self, channel_id, **kw):
        """
        Reset ALL slide completion records for the current user in the
        given channel. After reset, the learner is back at Day 1.
        """
        channel_id = int(channel_id)
        channel = request.env["slide.channel"].browse(channel_id)
        if not channel.exists():
            return request.redirect("/slides")

        user = request.env.user
        partner = user.partner_id

        # Find all slides in this channel
        slide_ids = channel.slide_ids.ids

        if slide_ids:
            # Delete all completion/progress records for this user in this channel
            records = request.env["slide.slide.partner"].sudo().search([
                ("slide_id", "in", slide_ids),
                ("partner_id", "=", partner.id),
            ])
            records.unlink()

            # Also reset the channel member's completion count
            channel_partner = request.env["slide.channel.partner"].sudo().search([
                ("channel_id", "=", channel_id),
                ("partner_id", "=", partner.id),
            ], limit=1)
            if channel_partner:
                channel_partner.write({
                    "completion": 0,
                })

        return request.redirect(channel.website_url or ("/slides/%s" % channel_id))
