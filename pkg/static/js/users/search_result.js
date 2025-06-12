"use strict";

document.addEventListener("DOMContentLoaded", () => {
  // --- FORM FILTER SUBMISSION LOGIC ---
  const searchForm = document.getElementById("searchForm");
  const filters = [
    document.getElementById("locationFilter"),
    document.getElementById("categoryFilter"),
    document.getElementById("dateFilter"),
    document.getElementById("sortBy"),
  ];

  const sortBySelect = document.getElementById("sortBy");
  const sortByInput = document.getElementById("sortByInput");

  filters.forEach((filter) => {
    if (filter) {
      filter.addEventListener("change", () => {
        if (filter.id === "sortBy" && sortByInput) {
          sortByInput.value = filter.value;
        }
        if (searchForm) searchForm.submit();
      });
    }
  });

  // ##### FIX APPLIED HERE: Function to get CSRF token from the hidden input #####
  function getCsrfToken() {
    const tokenInput = document.querySelector('input[name="csrf_token"]');
    return tokenInput ? tokenInput.value : null;
  }

  // --- MODAL INTERACTIVITY ---
  const bookingModal = document.getElementById("bookingModal");
  const closeModalBtn = document.getElementById("closeModal");
  const serviceCards = document.querySelectorAll(".service-card");

  let currentServiceId = null;
  let selectedTime = null;

  const openModal = () => (bookingModal.style.display = "flex");
  const closeModal = () => {
    bookingModal.style.display = "none";
    resetModal();
  };

  const resetModal = () => {
    document.getElementById("modalBody").style.display = "none";
    document.getElementById("modalLoader").style.display = "block";
    document.getElementById("timeSlotsContainer").innerHTML = "";
    document.getElementById("timeSlotsMessage").textContent =
      "Please select a date to see available times.";
    document.getElementById("bookingDate").value = "";
    const bookNowBtn = document.getElementById("bookNowBtn");
    bookNowBtn.disabled = true;
    bookNowBtn.textContent = "Select a time slot to book";
    currentServiceId = null;
    selectedTime = null;
  };

  const showToast = (type, title, message) => {
    const container = document.getElementById("toastContainer");
    if (!container) {
      // Fallback if toast container is not on the page
      alert(`${title}: ${message}`);
      return;
    }
    const icon =
      type === "success" ? "fa-check-circle" : "fa-exclamation-circle";
    const toastHTML = `
      <div class="toast ${type}">
        <i class="fas ${icon} toast-icon"></i>
        <div class="toast-body">
          <h4>${title}</h4>
          <p>${message}</p>
        </div>
      </div>`;
    const toast = document.createElement("div");
    toast.innerHTML = toastHTML;
    container.appendChild(toast);
    setTimeout(() => {
      toast.remove();
    }, 5000);
  };

  serviceCards.forEach((card) => {
    card.addEventListener("click", async () => {
      currentServiceId = card.dataset.serviceId;
      openModal();

      try {
        const response = await fetch(
          `/users/service/${currentServiceId}/details`
        );
        if (!response.ok) throw new Error("Service not found");
        const service = await response.json();

        // Populate modal
        document.getElementById("modalServiceName").textContent = service.name;
        document.getElementById("modalServiceDescription").textContent =
          service.description || "No description provided.";
        document.getElementById(
          "modalServicePrice"
        ).textContent = `$${parseFloat(service.price).toFixed(2)}`;
        document.getElementById(
          "modalServiceDuration"
        ).textContent = `${service.duration_minutes} minutes`;
        document.getElementById("modalBusinessName").textContent =
          service.business.name;
        document.getElementById(
          "modalBusinessAddress"
        ).textContent = `${service.business.lga_province}, ${service.business.state}`;

        // Set min date for date picker
        const datePicker = document.getElementById("bookingDate");
        datePicker.min = new Date().toISOString().split("T")[0];

        document.getElementById("modalLoader").style.display = "none";
        document.getElementById("modalBody").style.display = "grid";
      } catch (error) {
        console.error("Error fetching service details:", error);
        closeModal();
        showToast("error", "Error", "Could not load service details.");
      }
    });
  });

  if (closeModalBtn) closeModalBtn.addEventListener("click", closeModal);
  if (bookingModal)
    bookingModal.addEventListener("click", (e) => {
      if (e.target === bookingModal) closeModal();
    });

  // --- AVAILABILITY CHECKER LOGIC ---
  const datePicker = document.getElementById("bookingDate");
  const availabilityLoader = document.getElementById("availabilityLoader");
  const timeSlotsContainer = document.getElementById("timeSlotsContainer");
  const timeSlotsMessage = document.getElementById("timeSlotsMessage");
  const bookNowBtn = document.getElementById("bookNowBtn");

  if (datePicker) {
    datePicker.addEventListener("change", async () => {
      const selectedDate = datePicker.value;
      if (!selectedDate || !currentServiceId) return;

      timeSlotsContainer.innerHTML = "";
      timeSlotsMessage.style.display = "none";
      availabilityLoader.style.display = "flex";
      bookNowBtn.disabled = true;
      bookNowBtn.textContent = "Checking availability...";

      try {
        const response = await fetch(
          `/users/service/${currentServiceId}/availability?date=${selectedDate}`
        );
        const availableTimes = await response.json();

        availabilityLoader.style.display = "none";

        if (availableTimes.length > 0) {
          availableTimes.forEach((time) => {
            const btn = document.createElement("button");
            btn.className = "time-slot-btn";
            btn.textContent = time;
            btn.dataset.time = time;
            btn.addEventListener("click", () => {
              // Deselect other buttons
              document
                .querySelectorAll(".time-slot-btn.selected")
                .forEach((b) => b.classList.remove("selected"));
              btn.classList.add("selected");
              selectedTime = btn.dataset.time;
              bookNowBtn.disabled = false;
              bookNowBtn.textContent = `Book for ${selectedTime}`;
            });
            timeSlotsContainer.appendChild(btn);
          });
        } else {
          timeSlotsMessage.textContent =
            "No available slots for this date. Please try another day.";
          timeSlotsMessage.style.display = "block";
        }
      } catch (error) {
        console.error("Error fetching availability:", error);
        availabilityLoader.style.display = "none";
        timeSlotsMessage.textContent =
          "Could not fetch availability. Please try again.";
        timeSlotsMessage.style.display = "block";
      }
    });
  }

  // --- BOOKING SUBMISSION ---
  if (bookNowBtn) {
    bookNowBtn.addEventListener("click", async () => {
      if (!currentServiceId || !datePicker.value || !selectedTime) {
        showToast(
          "error",
          "Missing Info",
          "Please ensure you have selected a date and time."
        );
        return;
      }

      bookNowBtn.disabled = true;
      bookNowBtn.innerHTML = '<div class="spinner-small"></div>Booking...';

      try {
        const response = await fetch("/users/book", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            // ##### FIX APPLIED HERE: Added CSRF token to request header #####
            "X-CSRFToken": getCsrfToken(),
          },
          body: JSON.stringify({
            service_id: currentServiceId,
            date: datePicker.value,
            time: selectedTime,
          }),
        });

        // The response MUST be parsed as JSON, if it's not, it will throw an error.
        const result = await response.json();

        if (response.ok) {
          closeModal();
          showToast("success", "Success!", result.message);
        } else {
          // Throw an error with the message from the server's JSON response
          throw new Error(result.message || "An unknown error occurred.");
        }
      } catch (error) {
        // This catch block will now handle both network errors and JSON parsing errors
        showToast("error", "Booking Failed", error.message);
        // Optionally, refresh availability
        datePicker.dispatchEvent(new Event("change"));
      } finally {
        // Reset button state even on failure, but only if a time is still selected
        if (selectedTime) {
          bookNowBtn.disabled = false;
          bookNowBtn.textContent = `Book for ${selectedTime}`;
        } else {
          bookNowBtn.disabled = true;
          bookNowBtn.textContent = "Select a time slot to book";
        }
      }
    });
  }
});
