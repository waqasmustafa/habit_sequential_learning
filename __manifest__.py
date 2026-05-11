{
    "name": "Bright Ready Sequential Learning",
    "version": "1.1.1",
    "author": "Waqas Mustafa Developer",
    "website": "https://brightready.com",
    "summary": "Bright Ready Sequential Learning",
    "description": """
Bright Ready Sequential Learning
================================
Adds daily unlock logic to eLearning courses:
- Sequential access enforcement (next lesson unlocks after completion)
- User timezone–aware morning/evening unlock hours
- Per-day lesson limit
    """,
    "category": "eLearning",
    "license": "LGPL-3",
    "depends": ["website_slides", "website_slides_survey"],
    "data": [
        # security first
        "security/ir.model.access.csv",
        "security/slide_rules.xml",

        "views/slide_channel_views.xml",
        "views/slide_slide_views.xml",
        "views/locked_page.xml",
        "views/website_slides_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "habit_sequential_learning/static/src/css/sequential.css",
            "habit_sequential_learning/static/src/js/br_slides_sidebar_fullscreen.js",
            "habit_sequential_learning/static/src/js/br_slides_sidebar_normal.js",
            "habit_sequential_learning/static/src/js/sequential_tooltips.js",
            "habit_sequential_learning/static/src/js/journey_ui.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
