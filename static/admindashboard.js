document.addEventListener("DOMContentLoaded", function () {
    // Smooth fade-in effect for content
    const elements = document.querySelectorAll(".admin-container, h1, p, table");
    elements.forEach((el, index) => {
        el.style.opacity = "0";
        el.style.transform = "translateY(20px)";
        setTimeout(() => {
            el.style.transition = "opacity 0.6s ease-out, transform 0.6s ease-out";
            el.style.opacity = "1";
            el.style.transform = "translateY(0)";
        }, index * 150);
    });

    // Hover effect on table rows
    document.querySelectorAll("tr").forEach(row => {
        row.addEventListener("mouseover", () => {
            row.style.backgroundColor = "#f1f1f1";
            row.style.transition = "background 0.3s ease";
        });
        row.addEventListener("mouseleave", () => {
            row.style.backgroundColor = "transparent";
        });
    });

    // Click animation for buttons
    document.querySelectorAll("button, .button").forEach(btn => {
        btn.addEventListener("click", function () {
            this.style.transform = "scale(0.95)";
            setTimeout(() => {
                this.style.transform = "scale(1)";
            }, 150);
        });
    });
});
