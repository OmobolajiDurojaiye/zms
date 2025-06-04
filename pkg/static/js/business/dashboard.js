"use strict";

document.addEventListener("DOMContentLoaded", function () {
  const sidebar = document.getElementById("sidebar");
  const sidebarToggle = document.getElementById("sidebarToggle");

  // --- Sidebar Toggle Functionality (for mobile/tablet) ---
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", () => {
      sidebar.classList.toggle("open");
      // Optional: Add a class to body to prevent scrolling when sidebar is open on mobile
      // document.body.classList.toggle('sidebar-open-no-scroll');
    });
  }

  // --- Optional: Close sidebar on nav item click (for mobile experience) ---
  // This is less critical with full page loads but can provide a slightly smoother UX on mobile
  // by ensuring the sidebar closes before or as the new page starts loading.
  const navLinks = document.querySelectorAll(".sidebar-nav .nav-item");
  navLinks.forEach((link) => {
    link.addEventListener("click", function () {
      // DO NOT call event.preventDefault() here. We want the navigation to happen.
      if (
        sidebar &&
        sidebar.classList.contains("open") &&
        window.innerWidth < 992
      ) {
        // This attempts to close the sidebar. The page will reload anyway.
        sidebar.classList.remove("open");
      }
    });
  });

  // The following client-side logic has been removed or is now handled server-side:
  // - Active class management for navigation items (handled by Jinja using request.endpoint).
  // - Showing/hiding of content sections (each page now loads its own content,
  //   and child templates set their main section to 'active').
  // - Page title updates (handled by Jinja blocks like {% block page_title %}).
  // - Scroll to top (default browser behavior on page load).
  // - URL hash updates for section linking (not applicable for MPA in this way).

  // Chart.js initialization for the main dashboard overview page
  // is located in the <script> tag within the dashboard.html template,
  // inside the {% block page_scripts %}.
  // If other pages (e.g., analytics.html) require charts, their specific
  // Chart.js setup should be included in their respective {% block page_scripts %}.
});
