document.addEventListener('DOMContentLoaded', function () {
    const headings = document.querySelectorAll('h2[id], h3[id]');
    const canHover = window.matchMedia('(hover: hover)').matches;

    const AnchorManager = {
        createAnchor: (heading) => {
            if (heading.querySelector('.anchor-link')) return;
            const anchor = document.createElement('a');
            anchor.className = 'anchor-link';
            anchor.href = '#' + heading.id;
            anchor.innerHTML = '<ion-icon name="link-outline"></ion-icon>';
            heading.appendChild(anchor);
        },
        removeAnchor: (heading) => {
            const anchor = heading.querySelector('.anchor-link');
            if (anchor) anchor.remove();
        },
        clearAnchors: () => {
            document.querySelectorAll('.anchor-link').forEach(anchor => anchor.remove());
        }
    };

    const HoverInteraction = {
        init() {
            headings.forEach(heading => {
                heading.addEventListener('mouseenter', () => this.onHoverIn(heading));
                heading.addEventListener('mouseleave', () => this.onHoverOut(heading));
            });
        },
        onHoverIn: (heading) => AnchorManager.createAnchor(heading),
        onHoverOut: (heading) => AnchorManager.removeAnchor(heading)
    };

    const TouchInteraction = {
        init() {
            document.addEventListener('click', (touchEvent) => {
                const heading = touchEvent.target.closest('h2[id], h3[id]');

                if (!heading) {
                    this.onOutsideClick();
                    return;
                }

                const isAnchor = touchEvent.target.classList.contains('anchor-link');
                if (isAnchor) return;

                this.onHeadingClick(heading);
            });
        },
        onHeadingClick: (heading) => {
            const exists = heading.querySelector('.anchor-link');
            AnchorManager.clearAnchors();
            if (!exists) AnchorManager.createAnchor(heading);
        },
        onOutsideClick: () => {
            AnchorManager.clearAnchors();
        }
    };

    const currentInteraction = canHover ? HoverInteraction : TouchInteraction;
    currentInteraction.init();
});
