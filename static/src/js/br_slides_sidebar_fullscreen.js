/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.BrSlidesSidebarFilterFullscreen = publicWidget.Widget.extend({
    // FULLSCREEN sidebar only
    selector: '.o_wslides_fs_sidebar_content',

    start() {
        const res = this._super(...arguments);

        // Inject CSS only once (for !important hide)
        this._ensureHideStyle();

        // Run immediately after paint
        window.requestAnimationFrame(() => this._filterSidebarCompletedOnly());

        // Run again after a short delay to catch late DOM changes
        setTimeout(() => this._filterSidebarCompletedOnly(), 600);

        return res;
    },

    /**
     * Add CSS class used to hide lessons with !important
     */
    _ensureHideStyle() {
        const styleId = 'br-fs-hide-lessons-style';
        if (document.getElementById(styleId)) {
            return;
        }
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .br-fs-hidden-lesson {
                display: none !important;
            }
        `;
        document.head.appendChild(style);
    },

    /**
     * Hide all FULLSCREEN lessons that are NOT completed.
     *
     * Fullscreen rows:
     *   li.o_wslides_fs_sidebar_list_item[data-id]
     *
     * Completed if:
     *   - data-completed="True" OR
     *   - contains .o_wslides_slide_completed icon
     */
    _filterSidebarCompletedOnly() {
        try {
            const root = this.el;
            if (!root) {
                return;
            }

            const rows = root.querySelectorAll(
                '.o_wslides_fs_sidebar_list_item[data-id]'
            );

            const visibleIds = [];

            rows.forEach((row) => {
                const id = row.getAttribute('data-id');
                const completedAttr = row.getAttribute('data-completed');
                const hasCompletedIcon = !!row.querySelector('.o_wslides_slide_completed');

                const isCompleted =
                    completedAttr === 'True' || hasCompletedIcon === true;

                if (!isCompleted) {
                    row.classList.add('br-fs-hidden-lesson');
                } else {
                    row.classList.remove('br-fs-hidden-lesson');
                    visibleIds.push(id);
                }
            });

            this._hideEmptySections();

        } catch (err) {
            // Silent fail in production
        }
    },

    /**
     * Hide sections that have no visible lessons (fullscreen only)
     */
    _hideEmptySections() {
        const root = this.el;
        const sections = root.querySelectorAll('.o_wslides_fs_sidebar_section');

        sections.forEach((section) => {
            const lessonLis = section.querySelectorAll(
                '.o_wslides_fs_sidebar_list_item'
            );

            let hasVisible = false;

            lessonLis.forEach((li) => {
                const style = window.getComputedStyle(li);
                const isHiddenByClass = li.classList.contains('br-fs-hidden-lesson');
                if (style.display !== 'none' && !isHiddenByClass) {
                    hasVisible = true;
                }
            });

            if (!hasVisible) {
                section.style.display = 'none';
            } else {
                section.style.display = '';
            }
        });
    },
});
