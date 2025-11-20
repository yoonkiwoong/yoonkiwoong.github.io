document.addEventListener('DOMContentLoaded', function () {
    const headings = document.querySelectorAll('h2[id], h3[id]');

    headings.forEach(function (heading) {
        const anchor = document.createElement('a');
        anchor.className = 'anchor-link';
        anchor.href = '#' + heading.id;
        anchor.textContent = '#';

        heading.appendChild(anchor);

        heading.addEventListener('click', function (e) {
            if (e.target === anchor) return;

            anchor.classList.toggle('visible');

            if (anchor.classList.contains('visible')) {
                setTimeout(function () {
                    anchor.classList.remove('visible');
                }, 2000);
            }
        });
    });
});
