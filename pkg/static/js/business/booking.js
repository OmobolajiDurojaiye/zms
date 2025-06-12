"use strict";
document.addEventListener("DOMContentLoaded", function () {
  // --- Modal Elements ---
  const viewAvailabilityModal = document.getElementById(
    "viewAvailabilityModal"
  );
  const closeViewAvailabilityModalBtn = document.getElementById(
    "closeViewAvailabilityModal"
  );
  const cancelViewAvailabilityModalBtn = document.getElementById(
    "cancelViewAvailabilityModal"
  );
  const availabilityModalDateSpan = document.getElementById(
    "availabilityModalDate"
  );
  const availabilitySlotsContainer = document.getElementById(
    "availabilitySlotsContainer"
  );
  // MODIFIED: Add a handle for the new booking list container in the modal
  const dailyBookingListContainer = document.getElementById("dailyBookingList");

  // --- Generic Modal Handling ---
  function openModal(modal) {
    if (modal) {
      modal.style.display = "block";
      document.body.classList.add("modal-open");
    }
  }

  function closeModal(modal) {
    if (modal) {
      modal.style.display = "none";
      document.body.classList.remove("modal-open");
    }
  }

  // View Availability Modal Event Listeners
  if (closeViewAvailabilityModalBtn) {
    closeViewAvailabilityModalBtn.addEventListener("click", () =>
      closeModal(viewAvailabilityModal)
    );
  }
  if (cancelViewAvailabilityModalBtn) {
    cancelViewAvailabilityModalBtn.addEventListener("click", () =>
      closeModal(viewAvailabilityModal)
    );
  }

  window.addEventListener("click", (event) => {
    if (event.target === viewAvailabilityModal) {
      closeModal(viewAvailabilityModal);
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      if (
        viewAvailabilityModal &&
        viewAvailabilityModal.style.display === "block"
      ) {
        closeModal(viewAvailabilityModal);
      }
    }
  });

  // --- MODIFIED: Function to open and populate View Schedule Modal ---
  function openViewAvailabilityModal(dateStr) {
    if (
      !viewAvailabilityModal ||
      !availabilityModalDateSpan ||
      !availabilitySlotsContainer ||
      !dailyBookingListContainer
    )
      return;

    const formattedDate = dayjs(dateStr).format("dddd, MMMM D, YYYY");
    availabilityModalDateSpan.textContent = formattedDate;

    // Reset both containers to a loading state
    availabilitySlotsContainer.innerHTML = "<p>Loading availability...</p>";
    dailyBookingListContainer.innerHTML =
      '<p class="no-bookings-message">Loading appointments...</p>';

    openModal(viewAvailabilityModal);

    // Fetch both availability and bookings for the given date
    fetch(`${getAvailabilityOnDateUrl}?date=${dateStr}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          // --- 1. Populate Availability Slots ---
          availabilitySlotsContainer.innerHTML = ""; // Clear loading message

          if (data.message) {
            const messageP = document.createElement("p");
            messageP.textContent = data.message;
            availabilitySlotsContainer.appendChild(messageP);
          }

          if (data.slots && data.slots.length > 0) {
            data.slots.forEach((slot) => {
              const slotDiv = document.createElement("div");
              slotDiv.classList.add("availability-slot");
              slotDiv.classList.add(
                `type-${slot.slot_type.toLowerCase().replace("_", "-")}`
              );
              const timeSpan = document.createElement("span");
              timeSpan.textContent = `${slot.start_time} - ${slot.end_time}`;
              const typeText = document.createTextNode(
                ` (${slot.slot_type
                  .replace("_", " ")
                  .replace(/\b\w/g, (l) => l.toUpperCase())})`
              );
              slotDiv.appendChild(timeSpan);
              slotDiv.appendChild(typeText);
              availabilitySlotsContainer.appendChild(slotDiv);
            });
          } else if (
            !data.message &&
            (!data.slots || data.slots.length === 0)
          ) {
            const noSlotsP = document.createElement("p");
            noSlotsP.classList.add("no-availability");
            noSlotsP.textContent =
              "No specific availability slots defined for this day.";
            availabilitySlotsContainer.appendChild(noSlotsP);
          }

          // --- 2. Populate Daily Bookings List ---
          dailyBookingListContainer.innerHTML = ""; // Clear loading message

          if (data.bookings && data.bookings.length > 0) {
            data.bookings.forEach((booking) => {
              const itemDiv = document.createElement("div");
              itemDiv.className = "appointment-item";
              itemDiv.dataset.bookingId = booking.id;

              const startTime = dayjs(booking.start_datetime).format("hh:mm A");
              const statusClass = booking.status
                .toLowerCase()
                .replace(/_/g, "-");
              const statusText = booking.status
                .replace(/_/g, " ")
                .replace(/\b\w/g, (l) => l.toUpperCase());

              // Simple display for the modal - no action buttons
              itemDiv.innerHTML = `
                <div class="appointment-time-status">
                  <div class="appointment-time">${startTime}</div>
                  <span class="appointment-status status-${statusClass}">${statusText}</span>
                </div>
                <div class="appointment-details">
                  <h4>${booking.client_display_name}</h4>
                  <p>Service: ${
                    booking.service ? booking.service.name : "N/A"
                  }</p>
                </div>
              `;
              dailyBookingListContainer.appendChild(itemDiv);
            });
          } else {
            const noBookingsP = document.createElement("p");
            noBookingsP.className = "no-bookings-message";
            noBookingsP.textContent = "No appointments scheduled for this day.";
            dailyBookingListContainer.appendChild(noBookingsP);
          }
        } else {
          // Handle fetch error
          const errorMessage = `<p class="form-error-message">Error: ${
            data.message || "Could not fetch schedule."
          }</p>`;
          availabilitySlotsContainer.innerHTML = errorMessage;
          dailyBookingListContainer.innerHTML = errorMessage;
        }
      })
      .catch((error) => {
        console.error("Error fetching daily schedule:", error);
        const networkError = `<p class="form-error-message">A network error occurred. Please try again.</p>`;
        availabilitySlotsContainer.innerHTML = networkError;
        dailyBookingListContainer.innerHTML = networkError;
      });
  }

  // --- FullCalendar Integration ---
  const calendarEl = document.getElementById("calendarView");
  let calendar;

  if (calendarEl) {
    calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: "dayGridMonth",
      headerToolbar: false, // Custom header controls are used
      height: "auto",
      events: {
        url: getCalendarBookingsUrl,
        failure: function (error) {
          console.error("Error fetching calendar events:", error.message);
          alert(
            "Could not load calendar appointments. Please try again later."
          );
        },
      },
      eventTimeFormat: {
        hour: "numeric",
        minute: "2-digit",
        meridiem: "short",
      },
      editable: false,
      selectable: true,
      selectMirror: true,
      // MODIFIED: Open schedule modal on day click
      select: function (info) {
        const selectedDate = dayjs(info.start).format("YYYY-MM-DD");
        openViewAvailabilityModal(selectedDate);
        calendar.unselect();
      },
      // MODIFIED: Open schedule modal on event click
      eventClick: function (info) {
        info.jsEvent.preventDefault(); // Prevent default link behavior
        const selectedDate = dayjs(info.event.start).format("YYYY-MM-DD");
        openViewAvailabilityModal(selectedDate);
      },
      dayMaxEvents: true, // True: allow "more" link when too many events
    });
    calendar.render();

    // Calendar navigation controls
    const prevMonthBtn = document.getElementById("prevMonthBtn");
    const nextMonthBtn = document.getElementById("nextMonthBtn");
    const todayBtn = document.getElementById("todayBtn");
    const calendarMonthYearEl = document.getElementById("calendarMonthYear");

    function updateCalendarHeader() {
      const currentDate = calendar.getDate();
      if (calendarMonthYearEl) {
        calendarMonthYearEl.textContent = `${currentDate.toLocaleString(
          "default",
          { month: "long" }
        )} ${currentDate.getFullYear()}`;
      }
    }

    if (prevMonthBtn)
      prevMonthBtn.addEventListener("click", () => {
        calendar.prev();
        updateCalendarHeader();
      });
    if (nextMonthBtn)
      nextMonthBtn.addEventListener("click", () => {
        calendar.next();
        updateCalendarHeader();
      });
    if (todayBtn)
      todayBtn.addEventListener("click", () => {
        calendar.today();
        updateCalendarHeader();
      });

    if (calendarMonthYearEl && calendar) updateCalendarHeader(); // Initial header
  } else {
    console.warn("Calendar element #calendarView not found.");
  }

  // --- Appointment Action Buttons (for the right-side list) ---
  document.querySelectorAll(".btn-call-client").forEach((button) => {
    button.addEventListener("click", function (e) {
      e.stopPropagation();
      const phone = this.dataset.phone;
      if (phone) {
        alert(`Client Phone: ${phone}`);
      } else {
        alert("Client phone number not available.");
      }
    });
  });

  document.querySelectorAll(".btn-message-client").forEach((button) => {
    button.addEventListener("click", function (e) {
      e.stopPropagation();
      const email = this.dataset.email;
      if (email) {
        alert(
          `Client Email: ${email}\n\n(This will trigger the messaging feature in the future)`
        );
      } else {
        alert("Client email not available.");
      }
    });
  });

  document.querySelectorAll(".btn-cancel-booking").forEach((button) => {
    button.addEventListener("click", function (e) {
      e.stopPropagation();
      const bookingId = this.dataset.bookingId;
      const clientName = this.closest(".appointment-item")
        .querySelector("h4")
        .textContent.trim();

      if (
        confirm(
          `Are you sure you want to cancel the booking for ${clientName}?`
        )
      ) {
        const cancelUrl = `${cancelBookingBaseUrl.replace(
          /\/$/,
          ""
        )}/${bookingId}/cancel`;

        fetch(cancelUrl, {
          method: "POST",
          headers: {
            "X-CSRFToken":
              document.querySelector('input[name="csrf_token"]')?.value ||
              document
                .querySelector('meta[name="csrf-token"]')
                ?.getAttribute("content"),
          },
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              alert(data.message || "Booking cancelled successfully.");
              window.location.reload(); // Reload to see the change
            } else {
              alert(
                "Failed to cancel booking: " + (data.message || "Unknown error")
              );
            }
          })
          .catch((err) => {
            console.error("Cancel booking error:", err);
            alert(
              "Error cancelling booking. Please check the console for details."
            );
          });
      }
    });
  });

  document.querySelectorAll(".btn-edit-booking").forEach((button) => {
    button.addEventListener("click", function (e) {
      e.stopPropagation();
      const bookingId = this.dataset.bookingId;
      alert(`Edit booking ID ${bookingId} - Feature to be implemented.`);
      // TODO: Implement edit booking modal and functionality
    });
  });
});
