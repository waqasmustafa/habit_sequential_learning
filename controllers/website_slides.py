from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.addons.website_slides.controllers.main import WebsiteSlides

def _check_gate(slide):
    if not slide.exists():
        return
    user = request.env.user
    # Do NOT sudo; enforce for the real learner
    if not slide.is_unlocked_for(user):
        raise AccessError("This lesson is locked until your next daily unlock.")

class WebsiteSlidesGate(WebsiteSlides):
    # Odoo 18 builds vary. We hook the three common endpoints and gate before delegating.

    @http.route()
    def slide_slide_view(self, channel_id, slide_id, **kw):
        slide = request.env["slide.slide"].browse(int(slide_id))
        _check_gate(slide)
        return super().slide_slide_view(channel_id, slide_id, **kw)

    @http.route()
    def slide_slide(self, slide_id, **kw):
        slide = request.env["slide.slide"].browse(int(slide_id))
        _check_gate(slide)
        return super().slide_slide(slide_id, **kw)

    @http.route()
    def slide(self, channel=None, slide=None, **kw):
        # Some themes route with typed params
        s = slide if hasattr(slide, "id") else None
        if not s and "slide_id" in kw:
            s = request.env["slide.slide"].browse(int(kw["slide_id"]))
        if s:
            _check_gate(s)
        return super().slide(channel=channel, slide=slide, **kw)
