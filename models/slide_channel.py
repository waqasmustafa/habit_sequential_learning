from odoo import api, fields, models
from datetime import timedelta
import pytz

class SlideChannel(models.Model):
    _inherit = "slide.channel"

    allow_sequential = fields.Boolean("Sequential Learning", help="Force order.")
    unlock_hour = fields.Integer("Daily Unlock Hour", default=4, help="0–23 in learner's local time.")
    lessons_per_day = fields.Integer("Lessons per Day", default=1)
    catchup_allowed = fields.Boolean("Allow Catch-up", default=False)
    tz_mode = fields.Selection(
        [("user", "User Timezone"), ("course", "Course (Website) TZ"), ("utc", "UTC")],
        default="user", string="Timezone Mode",
        help="Which timezone to use for unlock calculations."
    )
    fallback_tz = fields.Char("Fallback TZ", default="UTC")

    # Get timezone
    def _get_tz(self, user):
        self.ensure_one()
        if self.tz_mode == "user":
            tzname = user.tz or user.partner_id.tz or self.fallback_tz or "UTC"
        elif self.tz_mode == "course":
            tzname = self.fallback_tz or "UTC"
        else:
            tzname = "UTC"
        try:
            return pytz.timezone(tzname)
        except Exception:
            return pytz.timezone("UTC")


class SlideSlide(models.Model):
    _inherit = "slide.slide"

    def is_unlocked_for(self, user):
        """Return True if THIS slide is open for THIS user right now."""
        self.ensure_one()
        channel = self.channel_id

        # ===== ADMIN / TEACHER BYPASS =====
        if (
            user.has_group('base.group_system')
            or user.has_group('website_slides.group_website_slides_manager')
            or user.has_group('website.group_website_publisher')
        ):
            return True

        # If sequential not required, allow all
        if not channel.allow_sequential:
            return True

        # ===== FIND PREVIOUS PUBLISHED SLIDE =====
        prev = self.search([
            ("channel_id", "=", channel.id),
            ("sequence", "<", self.sequence),
            ("is_category", "=", False),          # skip chapter headers
            ("website_published", "=", True),     # only real lessons
        ], order="sequence desc, id desc", limit=1)

        # ===== FIRST SLIDE ALWAYS OPEN =====
        if not prev:
            return True

        # ===== CHECK IF USER COMPLETED PREVIOUS =====
        link_prev = self.env["slide.slide.partner"].search([
            ("slide_id", "=", prev.id),
            ("partner_id", "=", user.partner_id.id),
            ("completed", "=", True),
        ], limit=1)
        if not link_prev:
            return False

        # ===== DAILY LIMIT (LESSONS PER DAY) =====
        user_tz = channel._get_tz(user)
        now_utc = fields.Datetime.now()
        now_local = pytz.utc.localize(now_utc).astimezone(user_tz)
        day_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end_local = day_start_local + timedelta(days=1)
        day_start_utc = day_start_local.astimezone(pytz.utc).replace(tzinfo=None)
        day_end_utc = day_end_local.astimezone(pytz.utc).replace(tzinfo=None)

        completed_today = self.env["slide.slide.partner"].search_count([
            ("partner_id", "=", user.partner_id.id),
            ("completed", "=", True),
            ("slide_id.channel_id", "=", channel.id),
            ("create_date", ">=", day_start_utc),
            ("create_date", "<", day_end_utc),
        ])
        if completed_today >= max(channel.lessons_per_day, 1):
            return False

        # ===== NEXT UNLOCK TIME (after previous completion) =====
        anchor_utc = link_prev.create_date  # UTC-naive in DB
        anchor_local = pytz.utc.localize(anchor_utc).astimezone(user_tz)

        unlock_local = anchor_local.replace(
            hour=(channel.unlock_hour or 4), minute=0, second=0, microsecond=0
        )
        if anchor_local >= unlock_local:
            unlock_local += timedelta(days=1)

        unlock_utc = unlock_local.astimezone(pytz.utc).replace(tzinfo=None)
        return fields.Datetime.now() >= unlock_utc
