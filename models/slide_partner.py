from odoo import api, fields, models
from odoo.exceptions import AccessError

class SlideSlidePartner(models.Model):
    _inherit = "slide.slide.partner"

    @api.model_create_multi
    def create(self, vals_list):
        # When a slide is "started" or "completed", Odoo creates a slide.slide.partner row.
        # Block creation if the slide is not yet unlocked for this user.
        user = self.env.user
        for vals in vals_list:
            slide_id = vals.get("slide_id")
            partner_id = vals.get("partner_id")
            if not slide_id or not partner_id:
                continue
            # only enforce on the current user (avoid back-office imports/teachers)
            if partner_id != user.partner_id.id:
                continue
            slide = self.env["slide.slide"].browse(slide_id)
            if slide and not slide.is_unlocked_for(user):
                raise AccessError("This lesson is locked until your next daily unlock.")
        return super().create(vals_list)

    def write(self, vals):
        # If something tries to flip 'completed' later, enforce again.
        user = self.env.user
        if "completed" in vals and vals["completed"]:
            for rec in self:
                # only enforce for the current user’s own record
                if rec.partner_id.id != user.partner_id.id:
                    continue
                if not rec.slide_id.is_unlocked_for(user):
                    raise AccessError("This lesson is locked until your next daily unlock.")
        return super().write(vals)
