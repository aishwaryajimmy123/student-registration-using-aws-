// Lightweight client-side sanity checks. Server-side validation in app.py
// is the actual security boundary; this only improves user experience.
document.addEventListener("DOMContentLoaded", function () {
  var form = document.querySelector("form");
  if (!form) return;

  var photoInput = document.getElementById("photo");
  var MAX_BYTES = 5 * 1024 * 1024;

  form.addEventListener("submit", function (event) {
    if (photoInput && photoInput.files && photoInput.files.length > 0) {
      var file = photoInput.files[0];
      if (file.size > MAX_BYTES) {
        event.preventDefault();
        alert("Photo is too large. Maximum upload size is 5 MB.");
      }
    }
  });
});
