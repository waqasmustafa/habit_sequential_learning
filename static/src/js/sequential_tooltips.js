/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.SequentialTooltips = publicWidget.Widget.extend({
    selector: '.o_wslides_slides_list',

    start: function () {
        this._super.apply(this, arguments);
        this._initTooltips();
    },

    /**
     * Initialize tooltips for locked lessons specifically.
     * We use a slightly delayed scan to ensure Odoo's dynamic content is ready.
     */
    _initTooltips: function () {
        const self = this;
        setTimeout(() => {
            const $lockedLessons = self.$el.find('.br-locked-lesson');
            if (window.bootstrap && window.bootstrap.Tooltip) {
                $lockedLessons.each(function () {
                    new window.bootstrap.Tooltip(this, {
                        html: true,
                        container: 'body',
                        trigger: 'hover'
                    });
                });
            }
        }, 1000);
    }
});
