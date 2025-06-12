"use strict";

document.addEventListener("DOMContentLoaded", function () {
  const weeklyScheduleForm = document.getElementById("weeklyScheduleForm");
  const dateOverrideForm = document.getElementById("dateOverrideForm");
  const overrideDateInput = document.getElementById("overrideDate");
  const overrideTypeInput = document.getElementById("overrideType");
  const overrideSlotsContainer = document.getElementById(
    "overrideSlotsContainer"
  );
  const overrideAvailableSlotsWrapper = document.getElementById(
    "overrideAvailableSlotsWrapper"
  );
  const addOverrideSlotBtn = document.getElementById("addOverrideSlotBtn");
  const existingOverridesList = document.getElementById(
    "existingOverridesList"
  );
  const noOverridesMessage = document.getElementById("noOverridesMessage");
  const weeklyStatusDiv = document.getElementById("weeklyStatus");
  const overrideStatusDiv = document.getElementById("overrideStatus");

  // --- Helper Functions ---
  function displayMessage(element, message, isSuccess) {
    element.textContent = message;
    element.className = isSuccess
      ? "form-message-success"
      : "form-message-error";
    element.style.display = "block";
    setTimeout(() => {
      element.style.display = "none";
    }, 5000);
  }

  function getCsrfToken() {
    return (
      document.querySelector('input[name="csrf_token"]')?.value ||
      document.querySelector('meta[name="csrf-token"]')?.getAttribute("content")
    );
  }

  // --- Weekly Schedule Logic ---
  document.querySelectorAll(".add-slot-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const dayIndex = this.dataset.dayIndex;
      if (dayIndex === "override") return; // Handled by a separate listener

      const slotsContainer = document.getElementById(
        `slots_container_${dayIndex}`
      );
      const slotCount = slotsContainer.querySelectorAll(".time-slot").length;
      addSlotToContainer(slotsContainer, dayIndex, slotCount, true); // isWeekly = true
    });
  });

  function addSlotToContainer(
    container,
    dayIndexOrPrefix,
    slotIndex,
    isWeekly = true
  ) {
    const newSlot = document.createElement("div");
    newSlot.classList.add("time-slot");

    const prefix = isWeekly
      ? `days[${dayIndexOrPrefix}][slots][${slotIndex}]`
      : `override_slots[${slotIndex}]`;
    const idPrefix = isWeekly
      ? `weekly_${dayIndexOrPrefix}_${slotIndex}`
      : `override_${dayIndexOrPrefix}_${slotIndex}`;

    newSlot.innerHTML = `
      <input type="hidden" name="${prefix}[id]" value=""> <!-- For new slots, ID is empty -->
      <div class="form-group">
        <label for="start_time_${idPrefix}">Start Time</label>
        <input type="time" id="start_time_${idPrefix}" name="${prefix}[start_time]" value="09:00" required step="900">
      </div>
      <div class="form-group">
        <label for="end_time_${idPrefix}">End Time</label>
        <input type="time" id="end_time_${idPrefix}" name="${prefix}[end_time]" value="17:00" required step="900">
      </div>
      <div class="form-group">
        <label for="slot_type_${idPrefix}">Type</label>
        <select id="slot_type_${idPrefix}" name="${prefix}[slot_type]">
          <option value="available" selected>Available</option>
          <option value="break">Break</option>
        </select>
      </div>
      <button type="button" class="remove-slot-btn" title="Remove slot"><i class="fas fa-times-circle"></i></button>
    `;
    container.appendChild(newSlot);
    newSlot
      .querySelector(".remove-slot-btn")
      .addEventListener("click", function () {
        this.closest(".time-slot").remove();
        // Re-index if necessary, or let backend handle potentially gapped indices if it's simpler.
        // For now, backend should be robust to non-sequential slot indices.
      });
  }

  // Event delegation for removing slots (for initially loaded and dynamically added ones)
  document
    .getElementById("weeklyScheduleForm")
    .addEventListener("click", function (event) {
      if (event.target.closest(".remove-slot-btn")) {
        event.target.closest(".time-slot").remove();
      }
    });
  overrideSlotsContainer.addEventListener("click", function (event) {
    if (event.target.closest(".remove-slot-btn")) {
      event.target.closest(".time-slot").remove();
    }
  });

  // Toggle time slots based on "Closed" checkbox for weekly schedule
  document
    .querySelectorAll('input[name$="[is_closed]"]')
    .forEach((checkbox) => {
      const dayIndex = checkbox.closest(".day-schedule").dataset.dayIndex;
      const slotsContainer = document.getElementById(
        `slots_container_${dayIndex}`
      );
      const addSlotBtn = checkbox
        .closest(".day-schedule")
        .querySelector(".add-slot-btn");

      function toggleDaySlots() {
        if (checkbox.checked) {
          slotsContainer.style.display = "none";
          addSlotBtn.style.display = "none";
          // Optionally clear or disable inputs in hidden slots
          slotsContainer
            .querySelectorAll("input, select")
            .forEach((inp) => (inp.required = false));
        } else {
          slotsContainer.style.display = "flex";
          addSlotBtn.style.display = "inline-block"; // or 'block'
          slotsContainer
            .querySelectorAll('input[type="time"], select')
            .forEach((inp) => {
              if (!inp.name.includes("[id]")) inp.required = true; // Only require start/end/type if not an ID
            });
          // If no slots exist when unchecking "closed", add a default one
          if (slotsContainer.children.length === 0) {
            addSlotToContainer(slotsContainer, dayIndex, 0, true);
          }
        }
      }
      checkbox.addEventListener("change", toggleDaySlots);
      toggleDaySlots(); // Initial state
    });

  if (weeklyScheduleForm) {
    weeklyScheduleForm.addEventListener("submit", function (event) {
      event.preventDefault();
      const formData = new FormData(this);
      const submitButton = this.querySelector('button[type="submit"]');
      const originalButtonText = submitButton.innerHTML;
      submitButton.disabled = true;
      submitButton.innerHTML =
        '<i class="fas fa-spinner fa-spin"></i> Saving...';

      // Filter out data for closed days if slots are still in FormData
      // Or, ensure disabled inputs are not part of FormData (browsers usually do this)
      // For robustness, could iterate formData and remove entries for closed days.

      fetch(saveWeeklyUrl, {
        method: "POST",
        body: formData,
        headers: { "X-CSRFToken": getCsrfToken() },
      })
        .then((response) => response.json())
        .then((data) => {
          displayMessage(weeklyStatusDiv, data.message, data.success);
          if (data.success) {
            // Optionally reload or update UI with new slot IDs if needed for editing
          }
        })
        .catch((error) => {
          console.error("Error saving weekly schedule:", error);
          displayMessage(weeklyStatusDiv, "A network error occurred.", false);
        })
        .finally(() => {
          submitButton.disabled = false;
          submitButton.innerHTML = originalButtonText;
        });
    });
  }

  // --- Date Override Logic ---
  function setupOverrideSlots() {
    if (overrideTypeInput.value === "available") {
      overrideAvailableSlotsWrapper.style.display = "block";
      // If the container is empty when switching to 'available', add a default slot
      if (overrideSlotsContainer.children.length === 0) {
        addSlotToContainer(overrideSlotsContainer, "new_override", 0, false);
      }
    } else {
      // 'blocked_override'
      overrideAvailableSlotsWrapper.style.display = "none";
      // Clear the slots to ensure they are not submitted with the form
      overrideSlotsContainer.innerHTML = "";
    }
  }

  if (overrideTypeInput) {
    overrideTypeInput.addEventListener("change", setupOverrideSlots);
    setupOverrideSlots(); // Initial call to set the correct state on page load
  }

  if (addOverrideSlotBtn) {
    addOverrideSlotBtn.addEventListener("click", function () {
      const slotCount =
        overrideSlotsContainer.querySelectorAll(".time-slot").length;
      addSlotToContainer(
        overrideSlotsContainer,
        "new_override",
        slotCount,
        false
      );
    });
  }

  if (dateOverrideForm) {
    dateOverrideForm.addEventListener("submit", function (event) {
      event.preventDefault();
      const formData = new FormData(this);
      const submitButton = this.querySelector('button[type="submit"]');
      const originalButtonText = submitButton.innerHTML;
      submitButton.disabled = true;
      submitButton.innerHTML =
        '<i class="fas fa-spinner fa-spin"></i> Saving...';

      fetch(saveOverrideUrl, {
        method: "POST",
        body: formData,
        headers: { "X-CSRFToken": getCsrfToken() },
      })
        .then((response) => response.json())
        .then((data) => {
          displayMessage(overrideStatusDiv, data.message, data.success);
          if (data.success && data.overrides_html) {
            if (noOverridesMessage) noOverridesMessage.style.display = "none";
            existingOverridesList.innerHTML = data.overrides_html; // Update list
            dateOverrideForm.reset();
            overrideDateInput.value = todayISO; // Reset date to today
            setupOverrideSlots(); // Reset override slots view
          } else if (data.success) {
            // Fallback if overrides_html is not sent
            window.location.reload(); // Simple reload
          }
        })
        .catch((error) => {
          console.error("Error saving date override:", error);
          displayMessage(overrideStatusDiv, "A network error occurred.", false);
        })
        .finally(() => {
          submitButton.disabled = false;
          submitButton.innerHTML = originalButtonText;
        });
    });
  }

  // Delete Availability Slot (for overrides and potentially weekly in future)
  existingOverridesList.addEventListener("click", function (event) {
    const deleteButton = event.target.closest(".delete-availability-btn");
    if (deleteButton) {
      const availabilityId = deleteButton.dataset.id;
      if (confirm(`Are you sure you want to delete this availability slot?`)) {
        const deleteUrl = `${deleteAvailabilityUrlBase}/${availabilityId}`;
        fetch(deleteUrl, {
          method: "DELETE", // Or POST if DELETE is problematic with proxies/CSRF
          headers: { "X-CSRFToken": getCsrfToken() },
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              displayMessage(overrideStatusDiv, data.message, true);
              const itemToRemove = existingOverridesList.querySelector(
                `li[data-id="${availabilityId}"]`
              );
              if (itemToRemove) itemToRemove.remove();
              if (
                existingOverridesList.children.length === 0 &&
                noOverridesMessage
              ) {
                noOverridesMessage.style.display = "block";
              }
            } else {
              displayMessage(
                overrideStatusDiv,
                data.message || "Failed to delete slot.",
                false
              );
            }
          })
          .catch((error) => {
            console.error("Error deleting availability:", error);
            displayMessage(
              overrideStatusDiv,
              "A network error occurred while deleting.",
              false
            );
          });
      }
    }
  });
});
