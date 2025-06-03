"use strict";

// Flash Message System
class FlashMessage {
  constructor() {
    this.container = null;
    this.init();
  }

  init() {
    // Create flash messages container if it doesn't exist
    this.container = document.querySelector(".flash-messages");
    if (!this.container) {
      this.container = document.createElement("div");
      this.container.className = "flash-messages";
      document.body.appendChild(this.container);
    }

    // Process existing flash messages from server
    this.processServerMessages();
  }

  processServerMessages() {
    // Look for server-rendered flash messages
    const serverMessages = document.querySelectorAll(".server-flash-message");
    serverMessages.forEach((msg) => {
      const type = msg.dataset.type || "info";
      const text = msg.textContent.trim();
      if (text) {
        this.show(text, type);
      }
      msg.remove(); // Remove the server message element
    });
  }

  show(message, type = "info", duration = 5000) {
    const flashElement = this.createFlashElement(message, type);
    this.container.appendChild(flashElement);

    // Trigger show animation
    setTimeout(() => {
      flashElement.classList.add("show");
    }, 100);

    // Auto dismiss after duration
    const dismissTimer = setTimeout(() => {
      this.dismiss(flashElement);
    }, duration);

    // Store timer reference for manual dismissal
    flashElement.dismissTimer = dismissTimer;

    return flashElement;
  }

  createFlashElement(message, type) {
    const flashDiv = document.createElement("div");
    flashDiv.className = `flash-message ${type}`;

    const iconMap = {
      success: "fas fa-check-circle",
      error: "fas fa-exclamation-circle",
      warning: "fas fa-exclamation-triangle",
      info: "fas fa-info-circle",
    };

    flashDiv.innerHTML = `
        <div class="flash-content">
          <i class="flash-icon ${iconMap[type] || iconMap.info}"></i>
          <span class="flash-text">${message}</span>
          <button class="flash-close" aria-label="Close">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="flash-progress"></div>
      `;

    // Add click handler for close button
    const closeBtn = flashDiv.querySelector(".flash-close");
    closeBtn.addEventListener("click", () => {
      this.dismiss(flashDiv);
    });

    // Add progress bar animation
    const progressBar = flashDiv.querySelector(".flash-progress");
    setTimeout(() => {
      progressBar.style.width = "100%";
      progressBar.style.transition = "width 5s linear";
    }, 100);

    return flashDiv;
  }

  dismiss(flashElement) {
    if (flashElement.dismissTimer) {
      clearTimeout(flashElement.dismissTimer);
    }

    flashElement.classList.remove("show");
    flashElement.classList.add("hide");

    setTimeout(() => {
      if (flashElement.parentNode) {
        flashElement.parentNode.removeChild(flashElement);
      }
    }, 300);
  }

  success(message, duration) {
    return this.show(message, "success", duration);
  }

  error(message, duration) {
    return this.show(message, "error", duration);
  }

  warning(message, duration) {
    return this.show(message, "warning", duration);
  }

  info(message, duration) {
    return this.show(message, "info", duration);
  }

  clear() {
    const messages = this.container.querySelectorAll(".flash-message");
    messages.forEach((msg) => this.dismiss(msg));
  }
}

// Enhanced Contact Form Handler
class ContactFormHandler {
  constructor() {
    this.form = document.getElementById("contactForm");
    this.flashMessage = new FlashMessage();
    this.init();
  }

  init() {
    if (!this.form) return;

    this.form.addEventListener("submit", (e) => {
      this.handleSubmit(e);
    });
  }

  async handleSubmit(e) {
    e.preventDefault();

    const submitBtn = this.form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;

    // Show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';

    try {
      const formData = new FormData(this.form);
      const data = Object.fromEntries(formData);

      // Use AJAX for better UX
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      const result = await response.json();

      if (result.success) {
        this.flashMessage.success(result.message);
        this.form.reset();
      } else {
        this.flashMessage.error(result.message);
      }
    } catch (error) {
      console.error("Contact form error:", error);

      // Fallback to regular form submission if AJAX fails
      this.form.action = "/contact";
      this.form.method = "POST";
      this.form.submit();
      return;
    }

    // Restore button state
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalBtnText;
  }
}

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  // Initialize flash message system
  window.flashMessage = new FlashMessage();

  // Initialize contact form handler
  new ContactFormHandler();
});

// Global function for manual flash messages
window.showFlash = (message, type = "info", duration = 5000) => {
  if (window.flashMessage) {
    return window.flashMessage.show(message, type, duration);
  }
};
