/* ==========================================================================
   LibraryHub 2.0 — Chart.js Integration
   Renders behaviour score history + payment trends on dashboards.
   Currently reserved for future dashboard analytics.
   ========================================================================== */

(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    // Detect if Chart.js is loaded
    if (typeof Chart === "undefined") {
      // Chart.js is optional — only load on pages that need it
      return;
    }

    initBehaviourChart();
    initPaymentTrendChart();
    initFineTypeChart();
  });

  /* ─── Behaviour Score History ────────────────────────────────────── */
  function initBehaviourChart() {
    const canvas = document.getElementById("behaviour-chart");
    if (!canvas) return;

    // Data comes from data-* attributes on canvas
    const labels = JSON.parse(canvas.dataset.labels || "[]");
    const scores = JSON.parse(canvas.dataset.scores || "[]");

    if (labels.length === 0) return;

    new Chart(canvas, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Behaviour Score",
            data: scores,
            borderColor: "#4c6fff",
            backgroundColor: "rgba(76, 111, 255, 0.1)",
            borderWidth: 2,
            tension: 0.3,
            fill: true,
            pointRadius: 4,
            pointHoverRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "#1a202c",
            padding: 10
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: { stepSize: 20 }
          }
        }
      }
    });
  }

  /* ─── Monthly Payments Bar ───────────────────────────────────────── */
  function initPaymentTrendChart() {
    const canvas = document.getElementById("payment-trend-chart");
    if (!canvas) return;

    const labels = JSON.parse(canvas.dataset.labels || "[]");
    const amounts = JSON.parse(canvas.dataset.amounts || "[]");

    if (labels.length === 0) return;

    new Chart(canvas, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Total Collected (₹)",
            data: amounts,
            backgroundColor: "#22c55e",
            borderRadius: 6,
            barThickness: 30
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: function (value) {
                return "₹" + value;
              }
            }
          }
        }
      }
    });
  }

  /* ─── Fine Type Distribution (Donut) ─────────────────────────────── */
  function initFineTypeChart() {
    const canvas = document.getElementById("fine-type-chart");
    if (!canvas) return;

    const labels = JSON.parse(canvas.dataset.labels || "[]");
    const values = JSON.parse(canvas.dataset.values || "[]");

    if (labels.length === 0) return;

    new Chart(canvas, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [
          {
            data: values,
            backgroundColor: [
              "#4c6fff", // rent
              "#f59e0b", // late
              "#3b82f6", // damage
              "#ef4444"  // lost
            ],
            borderWidth: 2,
            borderColor: "#ffffff"
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "60%",
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              padding: 12,
              boxWidth: 12,
              font: { size: 11 }
            }
          }
        }
      }
    });
  }
})();