"use strict";
document.addEventListener("DOMContentLoaded", function () {
  // Removed variables related to New Booking Modal:
  // newBookingBtn, newBookingModal, closeNewBookingModalBtn,
  // cancelNewBookingModalBtn, newBookingForm, newBookingErrorDiv, bookingDateInput (specific one from new booking modal)

  // New View Availability Modal elements
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

  // Generic Modal Handling
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

  // Function to open and populate View Availability Modal
  function openViewAvailabilityModal(dateStr) {
    if (
      !viewAvailabilityModal ||
      !availabilityModalDateSpan ||
      !availabilitySlotsContainer
    )
      return;

    const formattedDate = dayjs(dateStr).format("dddd, MMMM D, YYYY");
    availabilityModalDateSpan.textContent = formattedDate;
    availabilitySlotsContainer.innerHTML = "<p>Loading availability...</p>";
    openModal(viewAvailabilityModal);

    fetch(`${getAvailabilityOnDateUrl}?date=${dateStr}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          availabilitySlotsContainer.innerHTML = ""; // Clear loading

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
            // If no slots and no specific message (e.g. weekly_closed already showed message)
            const noSlotsP = document.createElement("p");
            noSlotsP.classList.add("no-availability");
            noSlotsP.textContent =
              "No specific availability slots defined for this day.";
            availabilitySlotsContainer.appendChild(noSlotsP);
          }
        } else {
          availabilitySlotsContainer.innerHTML = `<p class="form-error-message">Error: ${
            data.message || "Could not fetch availability."
          }</p>`;
        }
      })
      .catch((error) => {
        console.error("Error fetching availability:", error);
        availabilitySlotsContainer.innerHTML = `<p class="form-error-message">A network error occurred. Please try again.</p>`;
      });
  }

  // FullCalendar Integration
  const calendarEl = document.getElementById("calendarView");
  let calendar;

  if (calendarEl) {
    calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: "dayGridMonth",
      headerToolbar: false, // Custom header controls are used
      height: "auto", // Adjusts height to content
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
      select: function (info) {
        // MODIFIED: Open View Availability Modal instead of New Booking Modal
        const selectedDate = dayjs(info.start).format("YYYY-MM-DD");
        openViewAvailabilityModal(selectedDate);
        calendar.unselect();
      },
      eventClick: function (info) {
        // Existing eventClick logic for showing booking details
        let details = `Service: ${
          info.event.extendedProps.serviceName || info.event.title
        }\n`;
        details += `Client: ${info.event.extendedProps.clientName || "N/A"}\n`;
        details += `Time: ${dayjs(info.event.start).format("h:mm A")} - ${dayjs(
          info.event.end
        ).format("h:mm A")}\n`;
        details += `Status: ${
          info.event.extendedProps.status
            ? info.event.extendedProps.status
                .replace(/_/g, " ")
                .replace(/\b\w/g, (l) => l.toUpperCase())
            : "N/A"
        }\n`;
        if (info.event.extendedProps.notes) {
          details += `Notes: ${info.event.extendedProps.notes}\n`;
        }
        alert(details);
        // TODO: Implement edit booking modal if needed, triggered differently
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

  // MODIFIED: Appointment Actions (Call, Message, Cancel, Edit)
  document.querySelectorAll(".btn-call-client").forEach((button) => {
    button.addEventListener("click", function (e) {
      e.stopPropagation(); // Prevent triggering other click events on the parent
      const phone = this.dataset.phone;
      if (phone) {
        // A simple alert is used for now. On mobile, `window.location.href = 'tel:' + phone;` could be used.
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
          `Client Email: ${email}\n\n(This will trigger the messaging/email feature in the future)`
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

  // Function to update appointment list (e.g., after a cancellation) - kept as is
  function updateAppointmentListIfEmpty() {
    const appointmentList = document.getElementById("appointmentList");
    if (
      (appointmentList && appointmentList.children.length === 0) ||
      (appointmentList.children.length === 1 &&
        appointmentList.children[0].classList.contains("no-appointments"))
    ) {
      // If list is empty or only contains the "no appointments" message
      if (appointmentList.querySelector(".no-appointments") === null) {
        appointmentList.innerHTML =
          '<p class="no-appointments">No appointments scheduled for today.</p>';
      }
    }
  }

  // TODO: Implement appointment list filtering based on bookingDateFilter dropdown
  // const bookingDateFilter = document.getElementById('bookingDateFilter');
  // if (bookingDateFilter) {
  //     bookingDateFilter.addEventListener('change', function() {
  //         const filterValue = this.value;
  //         alert(`Filter changed to: ${filterValue}. Dynamic list update is a TODO.`);
  //     });
  // }
});
