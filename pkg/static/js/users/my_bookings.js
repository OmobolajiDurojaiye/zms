"use strict";

document.addEventListener("DOMContentLoaded", () => {
  // --- Globals & Panel Elements ---
  const listPanel = document.getElementById("bookingsListPanel");
  const detailsPanel = document.getElementById("bookingDetailsPanel");
  const chatPanel = document.getElementById("chatPanel");

  const detailsPlaceholder = document.getElementById("detailsPlaceholder");
  const detailsContentWrapper = document.getElementById(
    "detailsContentWrapper"
  );
  const chatPlaceholder = document.getElementById("chatPlaceholder");
  const chatContentWrapper = document.getElementById("chatContentWrapper");

  let activeListItem = null;
  let currentBookingId = null;
  let currentOwnerId = null;

  const socket = io("/business");

  // --- Socket.IO Event Handlers ---
  socket.on("connect", () => console.log("Connected to chat server."));
  socket.on("disconnect", () => console.log("Disconnected from chat server."));

  socket.on("message_received", (data) => {
    // If chat is visible for this business owner, append the message
    if (
      !chatPanel.classList.contains("panel-hidden") &&
      currentOwnerId == data.business_owner_id
    ) {
      appendMessage(data);
      // Mark as read immediately
      fetchMessages(data.business_owner_id, false); // false = don't show loader
    } else {
      // Otherwise, update the badge on the list item
      const item = document.querySelector(
        `.booking-list-item[data-owner-id='${data.business_owner_id}']`
      );
      if (item) {
        let badge = item.querySelector(".item-unread-badge");
        if (!badge) {
          badge = document.createElement("div");
          badge.className = "item-unread-badge";
          badge.innerHTML = `<span>0</span>`;
          item.appendChild(badge);
        }
        const badgeSpan = badge.querySelector("span");
        const currentCount = parseInt(badgeSpan.textContent || "0", 10);
        badgeSpan.textContent = currentCount + 1;
      }
    }
  });

  // --- Tab Functionality ---
  document.querySelectorAll(".tab-link").forEach((link) => {
    link.addEventListener("click", () => {
      document
        .querySelectorAll(".tab-link")
        .forEach((l) => l.classList.remove("active"));
      link.classList.add("active");

      document.querySelectorAll(".tab-content").forEach((content) => {
        content.classList.remove("active");
        if (content.id === link.dataset.tab) {
          content.classList.add("active");
        }
      });
      // Deselect any active booking when changing tabs
      deselectBooking();
    });
  });

  // --- Main Event Delegation for Booking Selection ---
  listPanel.addEventListener("click", (e) => {
    const targetItem = e.target.closest(".booking-list-item");
    if (!targetItem) return;

    // Prevent re-rendering if already selected
    if (targetItem === activeListItem) return;

    handleBookingSelect(targetItem);
  });

  function handleBookingSelect(item) {
    if (activeListItem) {
      activeListItem.classList.remove("active");
    }
    activeListItem = item;
    activeListItem.classList.add("active");

    currentBookingId = item.dataset.bookingId;
    currentOwnerId = item.dataset.ownerId;

    // Hide placeholders and show content wrappers
    detailsPlaceholder.classList.add("hidden");
    chatPlaceholder.classList.add("hidden");
    detailsContentWrapper.classList.remove("hidden");
    chatContentWrapper.classList.remove("hidden");

    // Render content
    renderBookingDetails(item.dataset);
    renderChat(item.dataset.businessName, item.dataset.ownerId);

    // Handle responsive view
    if (window.innerWidth <= 992) {
      listPanel.classList.add("panel-hidden");
      detailsPanel.classList.remove("panel-hidden");
      chatPanel.classList.remove("panel-hidden");
    }

    // Clear unread badge
    const badge = item.querySelector(".item-unread-badge");
    if (badge) {
      badge.remove();
    }
  }

  function deselectBooking() {
    if (activeListItem) {
      activeListItem.classList.remove("active");
      activeListItem = null;
    }
    currentBookingId = null;
    currentOwnerId = null;

    // Show placeholders and hide content wrappers
    detailsPlaceholder.classList.remove("hidden");
    chatPlaceholder.classList.remove("hidden");
    detailsContentWrapper.classList.add("hidden");
    chatContentWrapper.classList.add("hidden");

    // Handle responsive view
    if (window.innerWidth <= 992) {
      listPanel.classList.remove("panel-hidden");
      detailsPanel.classList.add("panel-hidden");
      chatPanel.classList.add("panel-hidden");
    }
  }

  // --- Content Rendering Functions ---

  function renderBookingDetails(data) {
    let actionButton = "";
    if (data.statusRaw === "confirmed") {
      actionButton = `<button id="initCancelBtn" class="btn btn-danger-outline"><i class="fas fa-times-circle"></i> Cancel Booking</button>`;
    }

    const detailsHTML = `
      <div class="details-header">
        <span class="booking-status">${data.status}</span>
        <div class="details-price">₦${data.price}</div>
      </div>
      <div class="details-body">
        <h3 class="service-name">${data.serviceName}</h3>
        <div class="detail-item">
          <i class="fas fa-calendar-alt"></i>
          <span>${data.date}</span>
        </div>
        <div class="detail-item">
          <i class="fas fa-clock"></i>
          <span>${data.time}</span>
        </div>
        <div class="details-actions">${actionButton}</div>
        <div class="details-divider"></div>
        <h4>Business Information</h4>
        <div class="business-details-loader" id="businessDetailsLoader">
            <div class="loader"></div>
        </div>
        <div id="businessDetailsContent"></div>
      </div>
    `;
    detailsContentWrapper.innerHTML = detailsHTML;
    fetchBusinessDetails(data.ownerId);

    // Add event listener for the cancel button if it exists
    const initCancelBtn = document.getElementById("initCancelBtn");
    if (initCancelBtn) {
      initCancelBtn.addEventListener("click", () =>
        showCancelConfirmation(data)
      );
    }
  }

  function renderChat(businessName, ownerId) {
    document.getElementById(
      "chatWithBusinessName"
    ).textContent = `Chat with ${businessName}`;
    document.getElementById("chatBusinessOwnerId").value = ownerId;
    fetchMessages(ownerId, true); // true = show loader
    socket.emit("join_chat", { business_owner_id: ownerId });
  }

  // --- Cancellation Flow (No Modal) ---

  function showCancelConfirmation(data) {
    const confirmationHTML = `
        <div class="details-body confirmation-view">
            <div class="confirmation-icon"><i class="fas fa-exclamation-triangle"></i></div>
            <h4>Confirm Cancellation</h4>
            <p>Are you sure you want to cancel your booking for <strong>${data.serviceName}</strong>? This action cannot be undone.</p>
            <div class="confirmation-actions">
                <button id="declineCancelBtn" class="btn btn-secondary">No, Keep It</button>
                <button id="confirmCancelBtn" class="btn btn-danger">Yes, Cancel Booking</button>
            </div>
        </div>
      `;
    detailsContentWrapper.innerHTML = confirmationHTML;

    document
      .getElementById("confirmCancelBtn")
      .addEventListener("click", handleConfirmCancel);
    document
      .getElementById("declineCancelBtn")
      .addEventListener("click", () => renderBookingDetails(data));
  }

  async function handleConfirmCancel() {
    if (!currentBookingId) return;

    const confirmBtn = document.getElementById("confirmCancelBtn");
    confirmBtn.disabled = true;
    confirmBtn.innerHTML =
      '<i class="fas fa-spinner fa-spin"></i> Cancelling...';

    try {
      const response = await fetch(
        `/users/api/bookings/${currentBookingId}/cancel`,
        { method: "POST" }
      );
      const result = await response.json();

      if (response.ok && result.success) {
        showToast(result.message, "success");
        window.location.reload();
      } else {
        throw new Error(result.message || "Failed to cancel booking.");
      }
    } catch (error) {
      showToast(error.message, "error");
      // Restore the previous view on failure
      if (activeListItem) renderBookingDetails(activeListItem.dataset);
    }
  }

  // --- API Calls & DOM Manipulation ---

  async function fetchMessages(ownerId, showLoader = true) {
    const chatMessages = document.getElementById("chatMessages");
    if (showLoader) {
      chatMessages.innerHTML = `<div class="loader-container"><div class="loader"></div></div>`;
    }

    try {
      const response = await fetch(
        `/users/api/conversations/${ownerId}/messages`
      );
      if (!response.ok) throw new Error("Failed to fetch messages.");
      const messages = await response.json();

      chatMessages.innerHTML = "";
      if (messages.length === 0) {
        chatMessages.innerHTML =
          '<p class="no-messages">No messages yet. Start the conversation!</p>';
      } else {
        messages.forEach(appendMessage);
      }
    } catch (error) {
      console.error(error);
      chatMessages.innerHTML =
        '<p class="error-message">Could not load conversation.</p>';
    }
  }

  function appendMessage(msg) {
    const chatMessages = document.getElementById("chatMessages");
    // Remove "no messages" placeholder if it exists
    const noMessagesEl = chatMessages.querySelector(".no-messages");
    if (noMessagesEl) noMessagesEl.remove();

    const messageEl = document.createElement("div");
    messageEl.classList.add(
      "message",
      msg.sender_role === "client" ? "sent" : "received"
    );

    const timestamp = new Date(msg.timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    messageEl.innerHTML = `
      <div class="message-content">${msg.content}</div>
      <div class="message-timestamp">${timestamp}</div>
    `;
    chatMessages.appendChild(messageEl);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  async function fetchBusinessDetails(ownerId) {
    const loader = document.getElementById("businessDetailsLoader");
    const content = document.getElementById("businessDetailsContent");
    loader.style.display = "flex";
    content.innerHTML = "";
    try {
      const response = await fetch(`/users/api/business/${ownerId}/details`);
      if (!response.ok) throw new Error("Failed to fetch business details.");
      const owner = await response.json();

      content.innerHTML = `
        <div class="detail-item">
            <i class="fas fa-envelope"></i>
            <div><strong>Email</strong><span>${owner.email}</span></div>
        </div>
        <div class="detail-item">
            <i class="fas fa-phone-alt"></i>
            <div><strong>Phone</strong><span>${owner.phone_number}</span></div>
        </div>
        <div class="detail-item">
            <i class="fas fa-map-marker-alt"></i>
            <div><strong>Address</strong><span>${owner.full_address}, ${
        owner.lga_province || ""
      }, ${owner.state}, ${owner.country}</span></div>
        </div>
      `;
    } catch (error) {
      console.error(error);
      content.innerHTML =
        '<p class="error-message">Could not load business details.</p>';
    } finally {
      loader.style.display = "none";
    }
  }

  // --- Message Form Submission ---
  document.getElementById("messageForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const input = document.getElementById("messageInput");
    const content = input.value.trim();
    const ownerId = document.getElementById("chatBusinessOwnerId").value;
    if (!content || !ownerId) return;

    socket.emit("send_message", {
      business_owner_id: ownerId,
      content: content,
    });

    // Add optimistic message to UI
    appendMessage({
      content: content,
      sender_role: "client",
      timestamp: new Date().toISOString(),
    });

    input.value = "";
    input.focus();
  });

  // --- Responsive View Handling ---
  const backBtn = document.getElementById("backToListBtn");
  backBtn.addEventListener("click", () => {
    deselectBooking();
  });

  // Initialize with no booking selected
  deselectBooking();
});
