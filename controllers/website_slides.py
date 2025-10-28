from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.addons.website_slides.controllers.main import WebsiteSlides

class WebsiteSlidesGate(WebsiteSlides):
    # Inherit the same route method so the original routing stays intact
    @http.route()
    def slide_slide_view(self, channel_id, slide_id, **kw):
        slide = request.env["slide.slide"].browse(int(slide_id))
        if slide.exists():
            user = request.env.user
            # IMPORTANT: do not sudo, check with real user
            if not slide.is_unlocked_for(user):
                raise AccessError("This lesson is locked until your next daily unlock.")
        return super().slide_slide_view(channel_id, slide_id, **kw)
