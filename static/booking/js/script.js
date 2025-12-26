document.addEventListener("DOMContentLoaded", () => {
  const payBtn = document.getElementById("rzp-button");
  if (!payBtn) return console.error("❌ Razorpay button not found!");

  payBtn.addEventListener("click", function (e) {
    e.preventDefault();

    if (typeof razorpayData === "undefined") {
      console.error("❌ razorpayData is not defined!");
      return;
    }

    console.log("🧩 Razorpay options loaded:", razorpayData);

    const options = {
      key: razorpayData.key,
      amount: razorpayData.amount,
      currency: razorpayData.currency,
      name: "Rural Sports Hub",
      description: `Payment for Booking #${razorpayData.bookingId}`,
      order_id: razorpayData.orderId,

      // ⭐ Razorpay Success Handler
      handler: function (response) {
        console.log("✅ Payment success:", response);

        fetch("/booking/payment/handler/", {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest"
          },
          body: new URLSearchParams({
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_order_id: response.razorpay_order_id,
            razorpay_signature: response.razorpay_signature,
            app_order_id: razorpayData.bookingId
          })
        })
        .then((res) => res.json())
        .then((data) => {
          if (data.status === "success") {
            window.location.href = data.redirect_url;
          } else {
            alert("⚠️ Payment verification failed: " + data.message);
          }
        })
        .catch((err) => console.error("Verification error:", err));
      },

      prefill: {
        name: "User",
        email: "user@example.com",
        contact: "9999999999"
      },

      theme: { color: "#3399cc" }
    };

    const rzp = new Razorpay(options);

    // 🔴 Razorpay failure event
    rzp.on("payment.failed", function (response) {
      console.error("🔴 Payment failed:", response.error);
      alert("Payment failed: " + response.error.description);
    });

    rzp.open();
  });
});
