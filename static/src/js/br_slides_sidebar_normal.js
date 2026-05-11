/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.BrSlidesSidebarFilterNormal = publicWidget.Widget.extend({
    selector: '.o_wslides_lesson_aside',

    start() {
        const res = this._super(...arguments);

        // Hide prev/next buttons immediately when widget starts
        this._hideNavButtons(this.el);

        // Then run the completed-only filter after DOM paint
        window.requestAnimationFrame(() => this._filterSidebarCompletedOnly());
        return res;
    },

    _filterSidebarCompletedOnly() {
        try {
            const root = this.el;
            if (!root) {
                return;
            }

            const normalRows = root.querySelectorAll('.o_wslides_lesson_aside_list_link[data-id]');

            normalRows.forEach((row) => {
                const isCompleted = row.getAttribute('data-completed') === 'True';

                if (!isCompleted) {
                    const li = row.closest('li');
                    if (li) {
                        li.style.display = 'none';
                    } else {
                        row.style.display = 'none';
                    }
                }
            });

            // Hide empty sections
            const sections = root.querySelectorAll('.o_wslides_lesson_aside_category');
            sections.forEach((section) => {
                const lessonRows = section.querySelectorAll('.o_wslides_lesson_aside_list_link');
                let hasVisible = false;

                lessonRows.forEach((row) => {
                    const li = row.closest('li');
                    const style = li ? window.getComputedStyle(li) : window.getComputedStyle(row);
                    if (style.display !== 'none') {
                        hasVisible = true;
                    }
                });

                section.style.display = hasVisible ? '' : 'none';
            });

        } catch (err) {
            // Silent fail in production
        }
    },

    /**
     * Hide the "Previous" and "Next" buttons in normal lesson view.
     */
    _hideNavButtons(root) {
        const wrap = root.closest('.o_wslides_wrap') || document;
        const navButtons = wrap.querySelectorAll('.o_wslides_nav_button');

        navButtons.forEach((btn) => {
            btn.style.display = 'none';
        });
    },
});
