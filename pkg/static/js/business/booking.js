"use strict";
document.addEventListener("DOMContentLoaded", function () {
  const newBookingBtn = document.getElementById("newBookingBtn");
  const newBookingModal = document.getElementById("newBookingModal");
  const closeNewBookingModalBtn = document.getElementById(
    "closeNewBookingModal"
  );
  const cancelNewBookingModalBtn = document.getElementById(
    "cancelNewBookingModal"
  );
  const newBookingForm = document.getElementById("newBookingForm");
  const newBookingErrorDiv = document.getElementById("newBookingError");
  const bookingDateInput = document.getElementById("bookingDate");

  // Set min date for bookingDate input to today and default to today
  if (bookingDateInput) {
    bookingDateInput.setAttribute("min", initialTodayISO);
    bookingDateInput.value = initialTodayISO;
  }

  // Modal Handling
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

  if (newBookingBtn) {
    newBookingBtn.addEventListener("click", () => {
      if (newBookingForm) newBookingForm.reset();
      if (bookingDateInput) bookingDateInput.value = initialTodayISO; // Reset date to today on open
      if (newBookingErrorDiv) {
        newBookingErrorDiv.style.display = "none";
        newBookingErrorDiv.textContent = "";
      }
      openModal(newBookingModal);
    });
  }

  if (closeNewBookingModalBtn) {
    closeNewBookingModalBtn.addEventListener("click", () =>
      closeModal(newBookingModal)
    );
  }
  if (cancelNewBookingModalBtn) {
    cancelNewBookingModalBtn.addEventListener("click", () =>
      closeModal(newBookingModal)
    );
  }

  window.addEventListener("click", (event) => {
    if (event.target === newBookingModal) {
      closeModal(newBookingModal);
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      if (newBookingModal && newBookingModal.style.display === "block") {
        closeModal(newBookingModal);
      }
    }
  });

  // New Booking Form Submission
  if (newBookingForm) {
    newBookingForm.addEventListener("submit", function (event) {
      event.preventDefault();
      if (newBookingErrorDiv) {
        newBookingErrorDiv.style.display = "none";
        newBookingErrorDiv.textContent = "";
      }

      const formData = new FormData(this);
      const submitButton = this.querySelector('button[type="submit"]');
      const originalButtonText = submitButton.innerHTML;
      submitButton.disabled = true;
      submitButton.innerHTML =
        '<i class="fas fa-spinner fa-spin"></i> Creating...';

      fetch(createBookingUrl, {
        method: "POST",
        body: formData,
        headers: {
          "X-CSRFToken":
            formData.get("csrf_token") ||
            document
              .querySelector('meta[name="csrf-token"]')
              ?.getAttribute("content"),
        },
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            closeModal(newBookingModal);
            alert(data.message || "Booking created successfully!");
            window.location.reload(); // Reload to see changes and flash messages
          } else {
            if (newBookingErrorDiv) {
              newBookingErrorDiv.textContent =
                data.message || "An unknown error occurred.";
              newBookingErrorDiv.style.display = "block";
            } else {
              alert("Error: " + (data.message || "An unknown error occurred."));
            }
          }
        })
        .catch((error) => {
          console.error("Error creating booking:", error);
          if (newBookingErrorDiv) {
            newBookingErrorDiv.textContent =
              "A network error occurred. Please try again.";
            newBookingErrorDiv.style.display = "block";
          } else {
            alert("A network error occurred. Please try again.");
          }
        })
        .finally(() => {
          submitButton.disabled = false;
          submitButton.innerHTML = originalButtonText;
        });
    });
  }

  // FullCalendar Integration
  const calendarEl = document.getElementById("calendarView");
  let calendar;

  if (calendarEl) {
    calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: "dayGridMonth",
      headerToolbar: false,
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
      select: function (info) {
        openModal(newBookingModal);
        if (newBookingForm) newBookingForm.reset();

        const selectedDate = dayjs(info.start).format("YYYY-MM-DD");
        const selectedTime = dayjs(info.start).format("HH:mm");

        if (bookingDateInput) bookingDateInput.value = selectedDate;
        const bookingTimeInput = document.getElementById("bookingTime");
        if (bookingTimeInput && !info.allDay) {
          // If a time slot is clicked in timeGrid view
          bookingTimeInput.value = selectedTime;
        } else if (bookingTimeInput) {
          // Default if only date is clicked
          bookingTimeInput.value = ""; // Or a default time like '09:00'
        }

        if (newBookingErrorDiv) newBookingErrorDiv.style.display = "none";
        calendar.unselect();
      },
      eventClick: function (info) {
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
        // TODO: Implement edit functionality (e.g., openEditBookingModal(info.event.id))
      },
      dayMaxEvents: true,
    });
    calendar.render();

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

    // Initial header update using FullCalendar's date, not necessarily server's today
    if (calendarMonthYearEl && calendar) updateCalendarHeader();
  } else {
    console.warn("Calendar element #calendarView not found.");
  }

  // Appointment Actions
  document.querySelectorAll(".btn-cancel-booking").forEach((button) => {
    button.addEventListener("click", function () {
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
              // Option 1: Reload page (simple, shows flash messages)
              window.location.reload();
              // Option 2: Update UI dynamically (more SPA-like)
              // this.closest('.appointment-item').remove();
              // if (calendar) calendar.refetchEvents();
              // updateAppointmentListIfEmpty();
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
    button.addEventListener("click", function () {
      const bookingId = this.dataset.bookingId;
      alert(`Edit booking ID ${bookingId} - Feature to be implemented.`);
      // TODO: Implement edit booking modal and functionality
    });
  });

  document.querySelectorAll(".btn-contact-client").forEach((button) => {
    button.addEventListener("click", function () {
      const phone = this.dataset.phone;
      const email = this.dataset.email;
      let contactInfo = "Client Contact Info:\n";
      contactInfo += `Phone: ${phone || "N/A"}\n`;
      contactInfo += `Email: ${email || "N/A"}`;
      alert(contactInfo);
    });
  });

  function updateAppointmentListIfEmpty() {
    const appointmentList = document.getElementById("appointmentList");
    if (
      (appointmentList && appointmentList.children.length === 0) ||
      (appointmentList.children.length === 1 &&
        appointmentList.children[0].classList.contains("no-appointments"))
    ) {
      appointmentList.innerHTML =
        '<p class="no-appointments">No appointments scheduled for today.</p>';
    }
  }

  // TODO: Implement appointment list filtering based on bookingDateFilter dropdown
  // const bookingDateFilter = document.getElementById('bookingDateFilter');
  // if (bookingDateFilter) {
  //     bookingDateFilter.addEventListener('change', function() {
  //         const filterValue = this.value;
  //         // This would typically involve an AJAX call to fetch and re-render the appointment list
  //         // and potentially update the calendar's date/view.
  //         alert(`Filter changed to: ${filterValue}. Dynamic list update is a TODO.`);
  //     });
  // }
});
