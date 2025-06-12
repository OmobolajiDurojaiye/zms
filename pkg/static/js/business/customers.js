"use strict";

document.addEventListener("DOMContentLoaded", () => {
  // --- STATE ---
  let currentClientId = null;
  let lastMessageDate = null;

  // --- SOCKET.IO ---
  const socket = io("/business");

  // --- DOM ELEMENTS ---
  const messagingContainer = document.getElementById("messaging-container");
  const customerListPanel = document.querySelector(".customer-list-panel");
  const customerItems = document.querySelectorAll(".customer-item");
  const customerSearchInput = document.getElementById("customer-search-input");

  const chatPlaceholder = document.getElementById("chat-placeholder");
  const chatWindow = document.getElementById("chat-window");
  const chatHeaderName = document.getElementById("chat-with-name");
  const messagesContainer = document.getElementById("chat-messages");
  const messageForm = document.getElementById("message-form");
  const messageInput = document.getElementById("message-input");

  const customerDetailsPanel = document.getElementById(
    "customer-details-panel"
  );
  const customerInfoToggleBtn = document.getElementById("customer-info-toggle");
  const customerDetailsCloseBtn = document.getElementById(
    "customer-details-close"
  );
  const detailsContentArea = document.getElementById("details-content-area");

  // --- UTILITY FUNCTIONS ---
  const scrollToBottom = () => {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  };

  const addDateSeparator = (date) => {
    const dateObj = new Date(date);
    const today = new Date();
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);

    let dateText;
    if (dateObj.toDateString() === today.toDateString()) {
      dateText = "Today";
    } else if (dateObj.toDateString() === yesterday.toDateString()) {
      dateText = "Yesterday";
    } else {
      dateText = dateObj.toLocaleDateString([], {
        year: "numeric",
        month: "long",
        day: "numeric",
      });
    }

    const separator = document.createElement("div");
    separator.className = "date-separator";
    separator.textContent = `─── ${dateText} ───`;
    messagesContainer.appendChild(separator);
  };

  const appendMessage = (msg) => {
    const msgDate = new Date(msg.timestamp).toDateString();
    if (lastMessageDate !== msgDate) {
      addDateSeparator(msg.timestamp);
      lastMessageDate = msgDate;
    }

    const messageElement = document.createElement("div");
    messageElement.classList.add(
      "message-bubble",
      msg.sender_role === "owner" ? "owner-message" : "client-message"
    );

    const timestamp = new Date(msg.timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    messageElement.innerHTML = `
      <div class="message-content">${msg.content}</div>
      <div class="message-timestamp">${timestamp}</div>
    `;
    messagesContainer.appendChild(messageElement);
    scrollToBottom();
  };

  const renderCustomerDetails = (data) => {
    detailsContentArea.innerHTML = `
        <div class="details-profile-header">
            <div class="details-avatar">${data.full_name[0].toUpperCase()}</div>
            <h3 class="details-name">${data.full_name}</h3>
            <p class="details-email">${data.email}</p>
        </div>
        <div class="details-section">
            <h4>Contact Information</h4>
            <div class="detail-item">
                <i class="fas fa-phone fa-fw"></i>
                <span><a href="tel:${data.phone_number}">${
      data.phone_number
    }</a></span>
            </div>
             <div class="detail-item">
                <i class="fas fa-map-marker-alt fa-fw"></i>
                <span>${data.state}, ${data.country}</span>
            </div>
        </div>
        <div class="details-section">
            <h4>Statistics</h4>
             <div class="detail-item">
                <i class="fas fa-calendar-check fa-fw"></i>
                <span>${data.stats.total_bookings} Total Bookings</span>
            </div>
            <div class="detail-item">
                <i class="fas fa-clock fa-fw"></i>
                <span>Last booking: ${data.stats.last_booking_date}</span>
            </div>
             <div class="detail-item">
                <i class="fas fa-user-plus fa-fw"></i>
                <span>Member since ${data.stats.member_since}</span>
            </div>
        </div>
    `;
  };

  // --- CORE LOGIC ---
  const loadMessages = async (clientId) => {
    messagesContainer.innerHTML =
      '<div class="loading-messages">Loading messages...</div>';
    lastMessageDate = null; // Reset for new chat
    try {
      const response = await fetch(
        `/business/api/customers/${clientId}/messages`
      );
      if (!response.ok)
        throw new Error(`HTTP error! Status: ${response.status}`);
      const messages = await response.json();
      messagesContainer.innerHTML = "";

      if (messages.length === 0) {
        messagesContainer.innerHTML =
          '<div class="no-messages">No messages yet. Start the conversation!</div>';
      } else {
        messages.forEach(appendMessage);
      }
    } catch (error) {
      console.error("Failed to load messages:", error);
      messagesContainer.innerHTML =
        '<div class="error-messages">Could not load messages. Please try again.</div>';
    }
  };

  const loadCustomerDetails = async (clientId) => {
    try {
      const response = await fetch(
        `/business/api/customers/${clientId}/details`
      );
      if (!response.ok) throw new Error("Failed to load details");
      const data = await response.json();
      renderCustomerDetails(data);
    } catch (error) {
      console.error("Error loading customer details:", error);
      detailsContentArea.innerHTML =
        '<div class="error-messages">Could not load details.</div>';
    }
  };

  const selectCustomer = (customerElement) => {
    customerItems.forEach((item) => item.classList.remove("active"));
    customerElement.classList.add("active");

    const clientId = customerElement.dataset.clientId;
    currentClientId = clientId;

    // Update chat header
    chatHeaderName.textContent = customerElement.dataset.clientName;

    // Show chat window
    chatPlaceholder.classList.remove("active");
    chatWindow.classList.add("active");
    messageInput.focus();

    // Remove unread badge on click
    const unreadBadge = customerElement.querySelector(".unread-badge");
    if (unreadBadge) unreadBadge.style.display = "none";

    socket.emit("join_chat", { client_id: currentClientId });
    loadMessages(currentClientId);
    loadCustomerDetails(currentClientId);
  };

  // --- EVENT LISTENERS ---
  customerItems.forEach((item) => {
    item.addEventListener("click", () => selectCustomer(item));
  });

  messageForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const content = messageInput.value.trim();
    if (content && currentClientId) {
      socket.emit("send_message", {
        client_id: currentClientId,
        content: content,
      });
      messageInput.value = "";
    }
  });

  customerSearchInput.addEventListener("keyup", () => {
    const searchTerm = customerSearchInput.value.toLowerCase();
    customerItems.forEach((item) => {
      const name = item.dataset.clientName.toLowerCase();
      item.style.display = name.includes(searchTerm) ? "flex" : "none";
    });
  });

  customerInfoToggleBtn.addEventListener("click", () => {
    customerDetailsPanel.classList.toggle("open");
  });

  customerDetailsCloseBtn.addEventListener("click", () => {
    customerDetailsPanel.classList.remove("open");
  });

  // --- SOCKET.IO EVENT HANDLERS ---
  socket.on("connect", () => console.log("Connected to messaging server."));

  socket.on("message_received", (msg) => {
    // If chat is currently open for this client, append message directly
    if (msg.client_id == currentClientId) {
      const noMessagesEl = messagesContainer.querySelector(".no-messages");
      if (noMessagesEl) noMessagesEl.remove();
      appendMessage(msg);
    } else {
      // Otherwise, update the customer list item with new message and badge
      const customerItem = document.querySelector(
        `.customer-item[data-client-id='${msg.client_id}']`
      );
      if (customerItem) {
        // Update last message preview
        const lastMessageSpan = customerItem.querySelector(
          ".customer-last-message"
        );
        lastMessageSpan.textContent = msg.content;

        // Update timestamp
        const timestampSpan = customerItem.querySelector(".message-timestamp");
        const timestamp = new Date(msg.timestamp);
        timestampSpan.textContent = timestamp.toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        });

        // Update or add unread badge
        let unreadBadge = customerItem.querySelector(".unread-badge");
        if (!unreadBadge) {
          unreadBadge = document.createElement("span");
          unreadBadge.className = "unread-badge";
          customerItem.querySelector(".customer-meta").appendChild(unreadBadge);
        }
        unreadBadge.textContent = (parseInt(unreadBadge.textContent) || 0) + 1;
        unreadBadge.style.display = "flex";

        // Move this customer to the top of the list
        const list = document.getElementById("customer-list");
        list.prepend(customerItem);
      }
    }
  });

  socket.on("disconnect", () =>
    console.log("Disconnected from messaging server.")
  );
});
