// site.js: Add your custom scripts here
document.addEventListener('DOMContentLoaded', function() {
    // Example: Highlight active nav link
    var links = document.querySelectorAll('.nav-link');
    links.forEach(function(link) {
        if (link.href === window.location.href) {
            link.classList.add('active');
        }
    });
});
