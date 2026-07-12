/* ==========================================================================
   LibraryHub 2.0 — Razorpay Payment Handler
   Runs on /pay/<fine_id> page.
   Reads razorpayConfig object injected by template.
   ========================================================================== */

(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    const payButton = document.getElementById("pay-button");
    const callbackForm = document.getElementById("razorpay-callback-form");
    const failedForm = document.getElementById("razorpay-failed-form");

    if (!payButton || !callbackForm || !failedForm) {
      return;
    }

    // razorpayConfig is injected globally by pay_fine.html template
    if (typeof razorpayConfig === "undefined") {
      console.error("[Payment] razorpayConfig not found in template");
      return;
    }

    /**
     * Posts to the /failed route with an error description.
     * The server sends the WhatsApp declined message and redirects to /my-fines.
     */
    function submitFailure(description) {
      document.getElementById("rp-failed-desc").value =
        description || "Payment could not be completed.";
      failedForm.submit();
    }

    /* ─── Build Razorpay options ─────────────────────────────────────── */
    const options = {
      key: razorpayConfig.key,
      amount: razorpayConfig.amount,
      currency: razorpayConfig.currency,
      order_id: razorpayConfig.order_id,
      name: "LibraryHub 2.0",
      description: "Library Fine Payment",
      image: "/static/img/logo.png",

      prefill: {
        name: razorpayConfig.student_name,
        email: razorpayConfig.student_email,
        contact: razorpayConfig.student_phone
      },

      theme: {
        color: "#4c6fff"
      },

      /* ─── Success handler ─────────────────────────────────────────── */
      handler: function (response) {
        // Populate hidden fields
        document.getElementById("rp-payment-id").value =
          response.razorpay_payment_id;
        document.getElementById("rp-order-id").value =
          response.razorpay_order_id;
        document.getElementById("rp-signature").value =
          response.razorpay_signature;

        // Disable button to prevent double submission
        payButton.disabled = true;
        payButton.innerHTML =
          '<span class="spinner-border spinner-border-sm me-2"></span>' +
          "Processing...";

        // Submit form to backend for verification
        callbackForm.submit();
      },

      /* ─── Modal close handler ─────────────────────────────────────── */
      modal: {
        ondismiss: function () {
          // User closed the Razorpay modal without completing payment
          console.log("[Payment] Razorpay modal dismissed by user");
          payButton.disabled = false;
          // No WhatsApp on simple dismiss — user didn't even attempt
        },
        escape: true,
        backdropclose: false
      },

      /* ─── Notes for tracking ──────────────────────────────────────── */
      notes: {
        source: "LibraryHub 2.0 Web",
        student: razorpayConfig.student_name
      }
    };

    /* ─── Click handler ──────────────────────────────────────────────── */
    payButton.addEventListener("click", function () {
      if (typeof Razorpay === "undefined") {
        alert(
          "Payment gateway failed to load. Please check your internet connection and try again."
        );
        return;
      }

      try {
        const rzp = new Razorpay(options);

        /* ─── payment.failed fires when Razorpay itself reports failure ─ */
        rzp.on("payment.failed", function (response) {
          console.error("[Payment] Failed:", response.error);
          const desc =
            response.error.description ||
            response.error.reason ||
            "Payment could not be processed.";
          // POST to server → WhatsApp notification + redirect to /my-fines
          submitFailure(desc);
        });

        rzp.open();
      } catch (err) {
        console.error("[Payment] Error opening Razorpay:", err);
        alert("Could not open payment window. Please refresh and try again.");
      }
    });
  });
})();