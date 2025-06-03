"use strict";

// Mobile Navigation
const hamburger = document.getElementById("hamburger");
const navMenu = document.getElementById("nav-menu");

if (hamburger && navMenu) {
  hamburger.addEventListener("click", () => {
    hamburger.classList.toggle("active");
    navMenu.classList.toggle("active");
  });
}

// Close mobile menu when clicking on a link
document.querySelectorAll(".nav-link").forEach((link) => {
  link.addEventListener("click", () => {
    if (hamburger && navMenu) {
      hamburger.classList.remove("active");
      navMenu.classList.remove("active");
    }
  });
});

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    const targetId = this.getAttribute("href");
    // Ensure targetId is not just "#" and is a valid selector
    if (targetId && targetId.length > 1 && document.querySelector(targetId)) {
      document.querySelector(targetId).scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  });
});

// Intersection Observer for animations
const observerOptions = {
  threshold: 0.1,
  rootMargin: "0px 0px -50px 0px",
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add("visible");
    }
  });
}, observerOptions);

// Add animation classes and observe elements (on DOMContentLoaded)
document.addEventListener("DOMContentLoaded", () => {
  const featureCards = document.querySelectorAll(".feature-card");
  featureCards.forEach((card, index) => {
    card.classList.add("fade-in");
    card.style.transitionDelay = `${index * 0.1}s`;
    observer.observe(card);
  });

  const storySections = document.querySelectorAll(".story-section");
  storySections.forEach((section) => {
    const content = section.querySelector(".story-content");
    const visual = section.querySelector(".story-visual");
    if (content && visual) {
      if (section.classList.contains("reverse")) {
        content.classList.add("slide-in-right");
        visual.classList.add("slide-in-left");
      } else {
        content.classList.add("slide-in-left");
        visual.classList.add("slide-in-right");
      }
      observer.observe(content);
      observer.observe(visual);
    }
  });

  const pricingCards = document.querySelectorAll(".pricing-card");
  pricingCards.forEach((card, index) => {
    card.classList.add("fade-in");
    card.style.transitionDelay = `${index * 0.15}s`;
    observer.observe(card);
  });

  const sectionHeaders = document.querySelectorAll(".section-header");
  sectionHeaders.forEach((header) => {
    header.classList.add("fade-in");
    observer.observe(header);
  });
});

// Hero stats counter animation
const animateCounter = (element, target, duration = 2000) => {
  let start = 0;
  const originalText = element.textContent;
  const suffix = originalText.replace(/[0-9.,]/g, "");
  const actualTarget = parseInt(String(target).replace(/[^0-9]/g, ""));

  if (isNaN(actualTarget)) return;

  const increment = actualTarget / (duration / 16);
  const timer = setInterval(() => {
    start += increment;
    if (start >= actualTarget) {
      element.textContent = actualTarget.toLocaleString() + suffix;
      clearInterval(timer);
    } else {
      element.textContent = Math.floor(start).toLocaleString() + suffix;
    }
  }, 16);
};

const heroStatsObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const statNumbers = entry.target.querySelectorAll(".stat-number");
        statNumbers.forEach((stat) => {
          const text = stat.textContent;
          const number = parseInt(text.replace(/[^0-9]/g, ""), 10);
          if (!isNaN(number)) {
            stat.textContent = "0" + text.replace(/[0-9.,]/g, "");
            animateCounter(stat, number);
          }
        });
        heroStatsObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.5 }
);

const heroStats = document.querySelector(".hero-stats");
if (heroStats) {
  heroStatsObserver.observe(heroStats);
}

// Dashboard mockup interactive elements
const sidebarItems = document.querySelectorAll(".sidebar-item");
sidebarItems.forEach((item) => {
  item.addEventListener("click", () => {
    sidebarItems.forEach((i) => i.classList.remove("active"));
    item.classList.add("active");
    const chart = document.querySelector(".chart-placeholder");
    if (chart) {
      chart.style.transform = "scale(0.95)";
      setTimeout(() => {
        chart.style.transform = "scale(1)";
      }, 150);
    }
  });
});

// Button click effects (Ripple)
const buttons = document.querySelectorAll(
  "button, .btn-outline, .btn-primary, .btn-primary-large, .btn-secondary-large"
);
buttons.forEach((button) => {
  // Ensure it's not a link styled as a button
  if (button.tagName.toLowerCase() === "button") {
    button.addEventListener("click", (e) => {
      const ripple = document.createElement("span");
      const rect = button.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const x = e.clientX - rect.left - size / 2;
      const y = e.clientY - rect.top - size / 2;
      ripple.style.cssText = `
        position: absolute; width: ${size}px; height: ${size}px;
        left: ${x}px; top: ${y}px; background: rgba(255, 255, 255, 0.4);
        border-radius: 50%; transform: scale(0);
        animation: ripple 0.6s linear; pointer-events: none;`;
      const currentPosition = window.getComputedStyle(button).position;
      if (currentPosition === "static") button.style.position = "relative";
      button.style.overflow = "hidden";
      button.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  }
});

const style = document.createElement("style");
style.textContent = `
  @keyframes ripple { to { transform: scale(4); opacity: 0; } }
  .hamburger.active .bar:nth-child(1) { transform: rotate(-45deg) translate(-5px, 6px); }
  .hamburger.active .bar:nth-child(2) { opacity: 0; }
  .hamburger.active .bar:nth-child(3) { transform: rotate(45deg) translate(-5px, -6px); }`;
document.head.appendChild(style);

// Scroll to top functionality
let scrollToTopBtn = document.createElement("button");
scrollToTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
scrollToTopBtn.className = "scroll-to-top";
scrollToTopBtn.style.cssText = `
  position: fixed; bottom: 20px; right: 20px; width: 50px; height: 50px;
  background: var(--blue-gradient); color: white; border: none; border-radius: 50%;
  cursor: pointer; box-shadow: var(--card-shadow-light); opacity: 0; visibility: hidden;
  transition: opacity 0.3s ease, visibility 0.3s ease, transform 0.3s ease;
  z-index: 1000; font-size: 18px; display: flex; align-items: center; justify-content: center;`;

function appendScrollToTop() {
  if (document.body) {
    document.body.appendChild(scrollToTopBtn);
    scrollToTopBtn.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  } else {
    window.addEventListener("DOMContentLoaded", appendScrollToTop);
  }
}
appendScrollToTop();


// --- VIDEO MODAL FUNCTIONALITY ---
const watchDemoBtn = document.getElementById("watchDemoBtn");
const videoModal = document.getElementById("videoModal");
const closeVideoModalBtn = document.getElementById("closeVideoModal");
const demoVideoPlayer = document.getElementById("demoVideoPlayer");

function openVideoModal() {
  if (videoModal) {
    videoModal.classList.add("active");
    document.body.style.overflow = "hidden";
  }
}
function closeVideoModal() {
  if (videoModal) {
    videoModal.classList.remove("active");
    if (demoVideoPlayer) {
      demoVideoPlayer.pause();
      demoVideoPlayer.currentTime = 0;
    }
    document.body.style.overflow = "";
  }
}
if (watchDemoBtn)
  watchDemoBtn.addEventListener("click", (e) => {
    e.preventDefault();
    openVideoModal();
  });
if (closeVideoModalBtn)
  closeVideoModalBtn.addEventListener("click", closeVideoModal);
if (videoModal)
  videoModal.addEventListener("click", (e) => {
    if (e.target === videoModal) closeVideoModal();
  });
document.addEventListener("keydown", (e) => {
  if (
    e.key === "Escape" &&
    videoModal &&
    videoModal.classList.contains("active")
  )
    closeVideoModal();
});


// Performance optimization: Debounce scroll events
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

const debouncedNavbarChange = debounce(() => {
  const navbar = document.querySelector(".navbar");
  if (navbar) {
    if (window.scrollY > 50) {
      navbar.style.background = "rgba(255, 255, 255, 0.98)";
      navbar.style.boxShadow = "0 2px 20px rgba(0, 0, 0, 0.1)";
    } else {
      navbar.style.background = "rgba(255, 255, 255, 0.95)";
      navbar.style.boxShadow = "none";
    }
  }
}, 16);

const debouncedScrollToTopVisibility = debounce(() => {
  if (scrollToTopBtn) { // Check if scrollToTopBtn exists
    if (window.scrollY > 500) {
      scrollToTopBtn.style.opacity = "1";
      scrollToTopBtn.style.visibility = "visible";
    } else {
      scrollToTopBtn.style.opacity = "0";
      scrollToTopBtn.style.visibility = "hidden";
    }
  }
}, 16);

window.addEventListener("scroll", () => {
  debouncedNavbarChange();
  debouncedScrollToTopVisibility();
});

// General page load message and flash message handling
document.addEventListener("DOMContentLoaded", () => {
  console.log("ZITOPY Landing Page loaded successfully!");
  // Check for flash messages and remove them after a delay
  const flashMessagesContainer = document.querySelector(
    ".flash-messages-container"
  );
  if (flashMessagesContainer && flashMessagesContainer.children.length > 0) {
    setTimeout(() => {
      flashMessagesContainer.style.transition = "opacity 0.5s ease";
      flashMessagesContainer.style.opacity = "0";
      setTimeout(() => flashMessagesContainer.remove(), 500);
    }, 5000); // Remove after 5 seconds
  }
});