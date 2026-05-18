# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import timedelta
import pytz


class SlideChannel(models.Model):
    _inherit = "slide.channel"

    # --- Helper: AM/PM hour selection ---
    def _get_hour_selection(self):
        labels = [
            "12:00 AM", "1:00 AM", "2:00 AM", "3:00 AM", "4:00 AM", "5:00 AM",
            "6:00 AM", "7:00 AM", "8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM",
            "12:00 PM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM",
            "6:00 PM", "7:00 PM", "8:00 PM", "9:00 PM", "10:00 PM", "11:00 PM",
        ]
        res = [(str(i), labels[i]) for i in range(24)]
        res.append(("-1", "1 Minute (TEST MODE)"))
        return res

    # === Settings ===
    allow_sequential = fields.Boolean(
        "Sequential Learning",
        help="Force learners to complete lessons in order."
    )

    night_unlock_hour = fields.Selection(
        selection=_get_hour_selection,
        string="Daily Night Unlock Time",
        default="20",  # 8:00 PM
        help="Local time when Night lectures unlock."
    )

    tz_mode = fields.Selection(
        [("user", "User Timezone"), ("course", "Course (Website) TZ"), ("utc", "UTC")],
        default="user",
        string="Timezone Mode",
        help="Which timezone to use for unlock calculations."
    )
    fallback_tz = fields.Char("Fallback TZ", default="UTC")

    # --- Journey UI Helpers ---
    def _get_journey_nights(self):
        self.ensure_one()
        return self.slide_ids.filtered(lambda s: s.lecture_type == 'night' and not s.is_category).sorted('sequence')

    def _get_active_night(self, user):
        self.ensure_one()
        nights = self._get_journey_nights()
        partner_id = user.partner_id.id if user and hasattr(user, 'partner_id') else False
        if not partner_id:
            return nights[0] if nights else self.env['slide.slide']
            
        for night in nights:
            if not night.is_unlocked_for(user):
                return night # Return the first locked one as the target
            # Check if COMPLETED
            completed = self.env['slide.slide.partner'].search_count([
                ('slide_id', '=', night.id),
                ('partner_id', '=', partner_id),
                ('completed', '=', True)
            ])
            if not completed:
                return night # The first unlocked but NOT completed is the active one
        return nights[-1] if nights else self.env['slide.slide']

    def _get_mornings(self):
        self.ensure_one()
        # Filter slides that are NOT night and belong to a category containing 'Morning'
        return self.slide_ids.filtered(lambda s: s.lecture_type == 'morning' and 'Morning' in (s.category_id.name or '') and not s.is_category)

    def _get_before_meals(self):
        self.ensure_one()
        return self.slide_ids.filtered(lambda s: 'Meal' in (s.category_id.name or '') and not s.is_category)

    def _get_mindsets(self):
        self.ensure_one()
        return self.slide_ids.filtered(lambda s: 'Mindset' in (s.category_id.name or '') and not s.is_category)

    # --- Timezone resolver ---
    def _get_tz(self, user):
        """Return a pytz timezone according to tz_mode with safe fallback."""
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

    lecture_type = fields.Selection([
        ('morning', 'Morning Lecture'),
        ('night', 'Night Lecture')
    ], string="Lecture Type", default='morning', required=True)

    is_morning = fields.Boolean("Day", compute="_compute_is_morning_night", inverse="_inverse_is_morning")
    is_night = fields.Boolean("Night", compute="_compute_is_morning_night", inverse="_inverse_is_night")

    @api.depends('lecture_type')
    def _compute_is_morning_night(self):
        for slide in self:
            slide.is_morning = (slide.lecture_type == 'morning')
            slide.is_night = (slide.lecture_type == 'night')

    def _inverse_is_morning(self):
        for slide in self:
            if slide.is_morning:
                slide.lecture_type = 'morning'
                slide.is_night = False
            else:
                slide.lecture_type = 'night'
                slide.is_night = True

    def _inverse_is_night(self):
        for slide in self:
            if slide.is_night:
                slide.lecture_type = 'night'
                slide.is_morning = False
            else:
                slide.lecture_type = 'morning'
                slide.is_morning = True

    # ---------- Helpers ----------
    def _get_ordered_categories(self, channel):
        """Return categories in display order."""
        return self.search([
            ("channel_id", "=", channel.id),
            ("is_category", "=", True),
            ("website_published", "=", True),
        ], order="sequence asc, id asc")

    def _get_parent_category(self):
        """Find the category this slide belongs to."""
        self.ensure_one()
        return self.search([
            ("channel_id", "=", self.channel_id.id),
            ("is_category", "=", True),
            ("sequence", "<=", self.sequence),
        ], order="sequence desc", limit=1)

    def _get_night_lesson_for_category(self, category):
        """Return the 'Night' lecture within a specific category."""
        if not category:
            return self.env['slide.slide']
        # Find next category to bound the search
        next_cat = self.search([
            ("channel_id", "=", category.channel_id.id),
            ("is_category", "=", True),
            ("sequence", ">", category.sequence),
        ], order="sequence asc", limit=1)
        
        domain = [
            ("channel_id", "=", category.channel_id.id),
            ("is_category", "=", False),
            ("lecture_type", "=", "night"),
            ("sequence", ">=", category.sequence),
            ("website_published", "=", True),
        ]
        if next_cat:
            domain.append(("sequence", "<", next_cat.sequence))
            
        return self.search(domain, order="sequence desc", limit=1)

    def _get_all_night_lectures(self):
        """Return all night lectures for the channel in sequence."""
        self.ensure_one()
        return self.search([
            ("channel_id", "=", self.channel_id.id),
            ("is_category", "=", False),
            ("lecture_type", "=", "night"),
            ("website_published", "=", True)
        ], order="sequence asc, id asc")

    def is_completed_by(self, user):
        """Check if a specific user has completed this slide."""
        self.ensure_one()
        if not user or not hasattr(user, 'partner_id'):
            return False
        return bool(self.env["slide.slide.partner"].search_count([
            ("slide_id", "=", self.id),
            ("partner_id", "=", user.partner_id.id),
            ("completed", "=", True),
        ]))

    # ---------- Core Gate ----------
    def is_unlocked_for(self, user):
        """
        Refined Logic for 'Journey' UI:
        - Staff bypass.
        - Morning, Before Meal, Mindset lectures (Day) are ALWAYS open.
        - Night Session lectures:
            * Night 1: Always Open.
            * Night N+1: Unlocked ONLY if Night N is Completed AND Time/Day rules met.
        """
        self.ensure_one()
        channel = self.channel_id

        # Bypass for staff
        if (
            user.has_group('base.group_system')
            or user.has_group('website_slides.group_website_slides_manager')
            or user.has_group('website.group_website_publisher')
        ):
            return True

        if not channel.allow_sequential:
            return True

        # Open non-night lectures immediately
        if self.lecture_type != 'night':
            return True

        # If already completed, it's obviously unlocked
        link_self = self.env["slide.slide.partner"].search([
            ("slide_id", "=", self.id),
            ("partner_id", "=", user.partner_id.id),
            ("completed", "=", True),
        ], limit=1)
        if link_self:
            return True

        # Sequential check for Night lectures
        all_nights = self._get_all_night_lectures()
        if not all_nights or self.id == all_nights[0].id:
            return True # Night 1 is open

        # Find previous night lecture in the course-wide sequence
        prev_night = self.env['slide.slide']
        for i, night in enumerate(all_nights):
            if night.id == self.id and i > 0:
                prev_night = all_nights[i-1]
                break
        
        if not prev_night:
            return True # Edge case fallback
            
        # Check completion of previous session's Night lecture
        link_prev_night = self.env["slide.slide.partner"].search([
            ("slide_id", "=", prev_night.id),
            ("partner_id", "=", user.partner_id.id),
            ("completed", "=", True),
        ], limit=1)
        
        if not link_prev_night:
            return False # Locked until Night N-1 done

        # Time and Frequency checks for Night lectures
        user_tz = channel._get_tz(user)
        now_utc = fields.Datetime.now()
        now_local = pytz.utc.localize(now_utc).astimezone(user_tz)
        
        # Frequency: Different day than previous night lesson completion
        prev_comp_local = pytz.utc.localize(link_prev_night.create_date).astimezone(user_tz)
        
        # --- TEST MODE BYPASS ---
        if channel.night_unlock_hour == "-1":
            return now_local >= prev_comp_local + timedelta(minutes=1)

        # Same calendar day as completion -> Always Locked
        if now_local.date() == prev_comp_local.date():
            return False

        # If it is 2 or more days after the completion day -> Always Unlocked
        if now_local.date() > prev_comp_local.date() + timedelta(days=1):
            return True

        # Clock Rule: Check Night Unlock Hour (Exactly on the next day)
        night_hour = int(channel.night_unlock_hour or 20)
        night_today_local = now_local.replace(hour=night_hour, minute=0, second=0, microsecond=0)
        
        return now_local >= night_today_local

    # ---------- UI Unlock Info ----------
    def next_unlock_info(self, user):
        """Provide status strings for the Hero Card UI."""
        if not self:
            return {"unlock_dt_local": None, "tz_name": "UTC", "unlock_message": "Please join the course to start your journey."}
        self.ensure_one()
        channel = self.channel_id
        user_tz = channel._get_tz(user)
        now_utc = fields.Datetime.now()
        now_local = pytz.utc.localize(now_utc).astimezone(user_tz)
        tz_name = getattr(user_tz, 'zone', 'UTC')
        night_hour = int(channel.night_unlock_hour or 20)
        
        if self.lecture_type != 'night':
            return {"unlock_dt_local": None, "tz_name": tz_name, "unlock_message": "Available Now"}

        all_nights = self._get_all_night_lectures()
        if not all_nights or self.id == all_nights[0].id:
            return {"unlock_dt_local": None, "tz_name": tz_name, "unlock_message": "Available Now"}

        # Find previous night
        prev_night = self.env['slide.slide']
        index = 0
        for i, night in enumerate(all_nights):
            if night.id == self.id and i > 0:
                prev_night = all_nights[i-1]
                index = i
                break
        
        if not prev_night:
             return {"unlock_dt_local": None, "tz_name": tz_name, "unlock_message": "Available Now"}

        link_prev_night = self.env["slide.slide.partner"].search([
            ("slide_id", "=", prev_night.id),
            ("partner_id", "=", user.partner_id.id),
            ("completed", "=", True),
        ], limit=1)
        
        if not link_prev_night:
            return {
                "unlock_dt_local": None,
                "tz_name": tz_name,
                "unlock_message": "Please complete Day %s first." % (index)
            }

        # Time/Day Gate
        prev_comp_local = pytz.utc.localize(link_prev_night.create_date).astimezone(user_tz)

        # --- TEST MODE UI ---
        if channel.night_unlock_hour == "-1":
            unlock_at = prev_comp_local + timedelta(minutes=1)
            if now_local < unlock_at:
                return {
                    "unlock_dt_local": unlock_at,
                    "tz_name": tz_name,
                    "unlock_message": "Available in 1 Minute (TEST)"
                }
            return {"unlock_dt_local": None, "tz_name": tz_name, "unlock_message": "Available Now"}

        # If it is 2 or more days after the completion day -> Always Available
        if now_local.date() > prev_comp_local.date() + timedelta(days=1):
            return {"unlock_dt_local": None, "tz_name": tz_name, "unlock_message": "Available Now"}

        labels = ["12 AM", "1 AM", "2 AM", "3 AM", "4 AM", "5 AM", "6 AM", "7 AM", "8 AM", "9 AM", "10 AM", "11 AM", "12 PM", "1 PM", "2 PM", "3 PM", "4 PM", "5 PM", "6 PM", "7 PM", "8 PM", "9 PM", "10 PM", "11 PM"]
        night_time_str = labels[night_hour] if night_hour < len(labels) else "Night"

        if prev_comp_local.date() >= now_local.date():
            return {
                "unlock_dt_local": None,
                "tz_name": tz_name,
                "unlock_message": "Available next day at %s" % night_time_str
            }

        night_today_local = now_local.replace(hour=night_hour, minute=0, second=0, microsecond=0)
        if now_local < night_today_local:
             return {
                "unlock_dt_local": night_today_local,
                "tz_name": tz_name,
                "unlock_message": "Available today at %s" % night_time_str
            }

        return {"unlock_dt_local": None, "tz_name": tz_name, "unlock_message": "Available Now"}
