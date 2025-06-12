"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const searchForm = document.getElementById("searchForm");
  const categoryChips = document.querySelectorAll(".category-chip");
  const categoryInput = document.getElementById("categoryInput");

  if (categoryChips && categoryInput && searchForm) {
    categoryChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        // Update active state visual
        document
          .querySelector(".category-chip.active")
          ?.classList.remove("active");
        chip.classList.add("active");

        // Set hidden input and submit
        categoryInput.value = chip.dataset.category;
        searchForm.submit();
      });
    });
  }
});
