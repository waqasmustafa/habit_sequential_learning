/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.JourneyUI = publicWidget.Widget.extend({
    selector: ".br-journey-wrapper",
    events: {
        "click .br-category-card": "_onCategoryClick",
        "click .br-timeline-item": "_onDayClick",
    },

    start: function () {
        this._super.apply(this, arguments);
    },

    /**
     * Handle clicking on a category box to reveal lesson list.
     * On mobile, the list appears below the category section.
     * We scroll to just below the clicked card so it stays in view.
     */
    _onCategoryClick: function (ev) {
        const $card = $(ev.currentTarget);
        const targetId = $card.data("toggle-target");
        const $target = this.$("#" + targetId);

        if ($target.length) {
            const isOpen = $target.hasClass("open");

            // Close all first
            this.$(".br-lecture-list-reveal").removeClass("open");

            if (!isOpen) {
                $target.addClass("open");

                // Scroll to just below the clicked card (works on both mobile and desktop)
                const scrollTarget = $card.offset().top - 60;
                $('html, body').animate({ scrollTop: scrollTarget }, 400);
            }
        }
    },

    /**
     * Handle clicking on a Day in the sidebar.
     * Instead of going directly to fullscreen, update the hero card to show
     * that night's info with the appropriate action button.
     */
    _onDayClick: function (ev) {
        const $item = $(ev.currentTarget);
        const nightId = $item.data("night-id");
        const nightName = $item.data("night-name");
        const nightUrl = $item.data("night-url");
        const nightStatus = $item.data("night-status"); // 'done', 'active', 'locked'
        const nightMessage = $item.data("night-message");

        if (!nightId) return;

        // Update hero badge
        this.$(".br-status-badge").text(nightMessage);

        // Update hero title
        this.$(".br-hero-card h1").text(nightName);

        // Update hero button area
        const $btnArea = this.$(".br-hero-btn-area");
        $btnArea.empty();

        if (nightStatus === "locked") {
            $btnArea.html('<div class="text-muted d-flex align-items-center justify-content-center"><i class="fa fa-lock me-2"></i> Locked</div>');
        } else if (nightStatus === "done") {
            $btnArea.html('<a href="' + nightUrl + '" class="btn br-start-btn br-replay-btn"><i class="fa fa-undo me-2"></i> Replay Session</a>');
        } else {
            $btnArea.html('<a href="' + nightUrl + '" class="btn br-start-btn">Start Session</a>');
        }

        // Update active class in sidebar
        this.$(".br-timeline-item").removeClass("active");
        $item.addClass("active");

        // Close any open category lists
        this.$(".br-lecture-list-reveal").removeClass("open");
    },
});

export default publicWidget.registry.JourneyUI;
