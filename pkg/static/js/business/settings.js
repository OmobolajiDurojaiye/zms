"use strict";

document.addEventListener("DOMContentLoaded", function () {
  // --- Initialize Choices.js for Business Type multiselect ---
  const businessTypeSelect = document.getElementById("business_type");
  if (businessTypeSelect) {
    new Choices(businessTypeSelect, {
      removeItemButton: true,
      placeholder: true,
      placeholderValue: "Select your business type(s)...",
      searchPlaceholderValue: "Search categories",
      allowHTML: false,
    });
  }

  // --- Settings Page Tab Functionality ---
  const navItems = document.querySelectorAll(".settings-nav-item");
  const sections = document.querySelectorAll(".settings-section");

  navItems.forEach((item) => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const targetId = item.dataset.target;
      const targetSection = document.getElementById(targetId);

      navItems.forEach((nav) => nav.classList.remove("active"));
      item.classList.add("active");

      sections.forEach((section) => section.classList.remove("active"));
      if (targetSection) {
        targetSection.classList.add("active");
        history.pushState(null, null, `#${targetId}`);
      }
    });
  });

  const currentHash = window.location.hash.substring(1);
  if (currentHash) {
    const targetNavItem = document.querySelector(
      `.settings-nav-item[data-target="${currentHash}"]`
    );
    if (targetNavItem) targetNavItem.click();
  } else {
    if (navItems.length > 0) navItems[0].classList.add("active");
    if (sections.length > 0) sections[0].classList.add("active");
  }

  // --- Edit Service Modal Functionality ---
  const editModal = document.getElementById("editServiceModal");
  if (editModal) {
    const editForm = document.getElementById("editServiceForm");
    const editButtons = document.querySelectorAll(".edit-service-btn");
    const closeButtons = document.querySelectorAll(
      ".close-button, .close-modal-btn"
    );

    const openModal = (e) => {
      const button = e.currentTarget;
      const serviceId = button.dataset.id;

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

      // Set the current image preview in the modal
      const imagePreview = document.getElementById(
        "edit_service_image_preview"
      );
      imagePreview.src = button.dataset.imageUrl;

      editModal.style.display = "block";
      document.body.classList.add("modal-open");
    };

    const closeModal = () => {
      editModal.style.display = "none";
      document.body.classList.remove("modal-open");

      // Reset the file input and preview display in the modal
      const fileInput = document.getElementById("edit_service_image");
      const fileNameDisplay = fileInput.nextElementSibling.nextElementSibling;
      fileInput.value = ""; // Clear the file input
      fileNameDisplay.textContent = "No new file chosen";
    };

    editButtons.forEach((button) =>
      button.addEventListener("click", openModal)
    );
    closeButtons.forEach((button) =>
      button.addEventListener("click", closeModal)
    );

    window.addEventListener("click", (e) => {
      if (e.target === editModal) closeModal();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && editModal.style.display === "block")
        closeModal();
    });
  }

  // --- Universal Image Preview Functionality ---
  function setupImagePreview(fileInputId, previewImgId, fileNameDisplayClass) {
    const fileInput = document.getElementById(fileInputId);
    const previewImg = document.getElementById(previewImgId);
    if (!fileInput || !previewImg) return;

    const fileNameDisplay =
      fileInput.parentElement.querySelector(fileNameDisplayClass);

    fileInput.addEventListener("change", function () {
      const file = this.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
          previewImg.src = e.target.result;
        };
        reader.readAsDataURL(file);
        if (fileNameDisplay) fileNameDisplay.textContent = file.name;
      } else {
        // Handle case where user cancels file selection
        if (fileNameDisplay) fileNameDisplay.textContent = "No file chosen";
      }
    });
  }

  // --- Universal Duration Preset Button Functionality ---
  function setupDurationPresets(containerId, inputId) {
    const container = document.getElementById(containerId);
    const input = document.getElementById(inputId);
    if (!container || !input) return;

    container.addEventListener("click", (e) => {
      if (e.target.classList.contains("btn-preset")) {
        input.value = e.target.dataset.value;
      }
    });
  }

  // Initialize for "Add Service" form
  setupImagePreview(
    "new_service_image",
    "new_service_image_preview",
    ".file-name-display"
  );
  setupDurationPresets("new_duration_group", "new_service_duration");

  // Initialize for "Edit Service" modal
  setupImagePreview(
    "edit_service_image",
    "edit_service_image_preview",
    ".file-name-display"
  );
  setupDurationPresets("edit_duration_group", "edit_service_duration");
});
