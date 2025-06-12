"use strict';";

document.addEventListener("DOMContentLoaded", function () {
  const ctxNewCustomers = document.getElementById("newCustomersChart");
  const ctxGender = document.getElementById("genderDemographicsChart");

  // --- Chart.js Global Defaults ---
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.color = "#6c757d"; // text-secondary color
  Chart.defaults.borderColor = "#dee2e6"; // border-color

  // --- 1. New Customers Growth Chart (Bar) ---
  if (ctxNewCustomers && typeof newCustomersChartData !== "undefined") {
    new Chart(ctxNewCustomers, {
      type: "bar",
      data: {
        labels: newCustomersChartData.labels,
        datasets: [
          {
            label: "New Customers",
            data: newCustomersChartData.data,
            backgroundColor: "rgba(0, 71, 165, 0.7)", // primary-blue with opacity
            borderColor: "rgba(0, 71, 165, 1)",
            borderWidth: 1,
            borderRadius: 4,
            hoverBackgroundColor: "rgba(0, 71, 165, 0.9)",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            backgroundColor: "#212529", // text-primary
            titleFont: { size: 14, weight: "600" },
            bodyFont: { size: 12 },
            padding: 10,
            cornerRadius: 6,
            displayColors: false,
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              drawBorder: false,
            },
            ticks: {
              // Ensure ticks are integers
              precision: 0,
            },
          },
          x: {
            grid: {
              display: false, // Hide vertical grid lines
            },
          },
        },
      },
    });
  }

  // --- 2. Customer Demographics Chart (Doughnut) ---
  if (
    ctxGender &&
    typeof genderChartData !== "undefined" &&
    genderChartData.data.length > 0
  ) {
    new Chart(ctxGender, {
      type: "doughnut",
      data: {
        labels: genderChartData.labels,
        datasets: [
          {
            label: "Gender",
            data: genderChartData.data,
            backgroundColor: [
              "rgba(0, 71, 165, 0.8)", // Primary Blue
              "rgba(232, 62, 140, 0.8)", // Accent Pink
              "rgba(111, 66, 193, 0.8)", // Accent Purple
              "rgba(32, 201, 151, 0.8)", // Accent Teal
              "rgba(253, 126, 20, 0.8)", // Accent Orange
            ],
            borderColor: "var(--bg-card)", // Match card background for a "cutout" look
            borderWidth: 3,
            hoverOffset: 8,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "70%",
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              padding: 20,
              boxWidth: 12,
              usePointStyle: true,
              pointStyle: "circle",
            },
          },
          tooltip: {
            backgroundColor: "#212529",
            titleFont: { size: 14, weight: "600" },
            bodyFont: { size: 12 },
            padding: 10,
            cornerRadius: 6,
            callbacks: {
              label: function (context) {
                let label = context.label || "";
                let value = context.parsed;
                let sum = context.dataset.data.reduce((a, b) => a + b, 0);
                let percentage = ((value / sum) * 100).toFixed(1) + "%";
                return `${label}: ${value} (${percentage})`;
              },
            },
          },
        },
      },
    });
  } else if (ctxGender) {
    // If the chart canvas exists but there's no data, show a placeholder message.
    const wrapper = ctxGender.parentElement;
    wrapper.innerHTML = `<div class="chart-no-data">
                               <i class="fas fa-chart-pie"></i>
                               <p>No demographic data is available for your customers yet.</p>
                             </div>`;
  }
});
