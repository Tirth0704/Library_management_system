/* ==========================================================================
   LibraryHub 2.0 — Main JavaScript
   Runs on all pages. Handles global behavior.
   ========================================================================== */

(function () {
  "use strict";

  /* ─── DOM Ready ──────────────────────────────────────────────────────── */
  document.addEventListener("DOMContentLoaded", function () {
    initFlashAutoDismiss();
    initTooltips();
    initConfirmDialogs();
    initFormValidation();
    logGreeting();
  });

  /* ─── Auto-dismiss flash messages after 5s ───────────────────────────── */
  function initFlashAutoDismiss() {
    const flashes = document.querySelectorAll(
      ".alert.alert-dismissible:not(.alert-permanent)"
    );

    flashes.forEach(function (alert) {
      setTimeout(function () {
        // Use Bootstrap's dismissal API if available
        if (window.bootstrap && bootstrap.Alert) {
          const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
          bsAlert.close();
        } else {
          alert.style.display = "none";
        }
      }, 5000);
    });
  }

  /* ─── Enable all Bootstrap tooltips ──────────────────────────────────── */
  function initTooltips() {
    const tooltipTriggers = document.querySelectorAll(
      '[data-bs-toggle="tooltip"]'
    );

    tooltipTriggers.forEach(function (el) {
      if (window.bootstrap && bootstrap.Tooltip) {
        new bootstrap.Tooltip(el);
      }
    });
  }

  /* ─── Extra confirmation for destructive actions ─────────────────────── */
  function initConfirmDialogs() {
    // Any form with data-confirm attribute
    const forms = document.querySelectorAll("form[data-confirm]");
    forms.forEach(function (form) {
      form.addEventListener("submit", function (e) {
        const msg = form.getAttribute("data-confirm");
        if (!confirm(msg)) {
          e.preventDefault();
          return false;
        }
      });
    });
  }

  /* ─── Basic client-side form validation ──────────────────────────────── */
  function initFormValidation() {
    // Bootstrap 5 style validation on submit
    const forms = document.querySelectorAll(".needs-validation");
    forms.forEach(function (form) {
      form.addEventListener(
        "submit",
        function (event) {
          if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
          }
          form.classList.add("was-validated");
        },
        false
      );
    });
  }

  /* ─── Dev greeting ───────────────────────────────────────────────────── */
  function logGreeting() {
    if (window.console && console.log) {
      console.log(
        "%cLibraryHub 2.0",
        "color:#4c6fff; font-size:16px; font-weight:bold;"
      );
      console.log(
        "%cBuilt by Tirth Acharya · Flask + MySQL + Bootstrap 5",
        "color:#94a3b8; font-size:11px;"
      );
    }
  }

  /* ─── Global helper: format currency ─────────────────────────────────── */
  window.formatCurrency = function (amount) {
    return "₹" + parseFloat(amount).toFixed(2);
  };

  /* ─── Global helper: debounce ────────────────────────────────────────── */
  window.debounce = function (fn, delay) {
    let timerId;
    return function (...args) {
      clearTimeout(timerId);
      timerId = setTimeout(function () {
        fn.apply(this, args);
      }, delay);
    };
  };
})();