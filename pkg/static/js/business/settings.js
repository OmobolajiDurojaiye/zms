"use strict";

document.addEventListener("DOMContentLoaded", function () {
  // --- Initialize Choices.js for Business Type multiselect ---
  const businessTypeSelect = document.getElementById("business_type");
  if (businessTypeSelect) {
    new Choices(businessTypeSelect, {
      removeItemButton: true, // Adds a small 'x' to remove selected items
      placeholder: true,
      placeholderValue: "Select your business type(s)...",
      searchPlaceholderValue: "Search categories",
      allowHTML: false, // Security best practice
    });
  }

  // --- Settings Page Tab Functionality ---
  const navItems = document.querySelectorAll(".settings-nav-item");
  const sections = document.querySelectorAll(".settings-section");

  navItems.forEach((item) => {
    item.addEventListener("click", (e) => {
      e.preventDefault();

      // Get target section ID from data attribute
      const targetId = item.dataset.target;
      const targetSection = document.getElementById(targetId);

      // Update active state for nav items
      navItems.forEach((nav) => nav.classList.remove("active"));
      item.classList.add("active");

      // Show the target section and hide others
      sections.forEach((section) => section.classList.remove("active"));
      if (targetSection) {
        targetSection.classList.add("active");
        // Update URL hash without jumping
        history.pushState(null, null, `#${targetId}`);
      }
    });
  });

  // Check for a hash in the URL on page load to activate the correct tab
  const currentHash = window.location.hash.substring(1);
  if (currentHash) {
    const targetNavItem = document.querySelector(
      `.settings-nav-item[data-target="${currentHash}"]`
    );
    if (targetNavItem) {
      targetNavItem.click();
    }
  } else {
    // Default to the first nav item if no hash is present
    if (navItems.length > 0) {
      navItems[0].classList.add("active");
    }
    if (sections.length > 0) {
      sections[0].classList.add("active");
    }
  }

  // --- Edit Service Modal Functionality ---
  const editModal = document.getElementById("editServiceModal");
  if (editModal) {
    const editForm = document.getElementById("editServiceForm");
    const editButtons = document.querySelectorAll(".edit-service-btn");
    const closeButtons = document.querySelectorAll(
      ".close-button, .close-modal-btn"
    );

    // Function to open the modal
    const openModal = (e) => {
      const button = e.currentTarget;
      const serviceId = button.dataset.id;

      // Populate form fields
      editForm.action = `/business/settings/services/edit/${serviceId}`;
      document.getElementById("edit_service_name").value = button.dataset.name;
      document.getElementById("edit_service_description").value =
        button.dataset.description;
      document.getElementById("edit_service_duration").value =
        button.dataset.duration;
      document.getElementById("edit_service_price").value =
        button.dataset.price;
      document.getElementById("edit_is_active").checked =
        button.dataset.isActive === "true";

      editModal.style.display = "block";
      document.body.classList.add("modal-open");
    };

    // Function to close the modal
    const closeModal = () => {
      editModal.style.display = "none";
      document.body.classList.remove("modal-open");
    };

    // Attach event listeners
    editButtons.forEach((button) =>
      button.addEventListener("click", openModal)
    );
    closeButtons.forEach((button) =>
      button.addEventListener("click", closeModal)
    );

    // Close modal if clicking outside the content area
    window.addEventListener("click", (e) => {
      if (e.target === editModal) {
        closeModal();
      }
    });

    // Close modal with Escape key
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && editModal.style.display === "block") {
        closeModal();
      }
    });
  }
});
