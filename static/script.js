document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('h2[id], h3[id]').forEach(function (heading) {
        const link = document.createElement('a');
        link.href = `#${heading.id}`;
        link.textContent = '🔗';
        link.className = 'anchor-link';
        link.setAttribute('aria-label', `Link to ${heading.textContent}`);

        heading.appendChild(document.createTextNode(' '));
        heading.appendChild(link);
    });
});
