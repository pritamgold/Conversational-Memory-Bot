document.addEventListener("DOMContentLoaded", function () {
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll(".nav-link");

  navLinks.forEach((link) => {
    const linkPath = link.getAttribute("href").replace(/\/$/, "");
    const normalizedCurrentPath = currentPath.replace(/\/$/, "");

    if (linkPath === normalizedCurrentPath) {
      link.classList.add("active-link"); // Add the active-link class
    } else {
      link.classList.remove("active-link"); // Remove the active-link class
    }
  });
});