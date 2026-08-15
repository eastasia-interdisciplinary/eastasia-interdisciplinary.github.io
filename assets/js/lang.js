(function () {
  function apply(lang) {
    document.documentElement.setAttribute("data-lang", lang);
    // mirrors the inline script in <head>: assistive tech needs the real
    // lang attribute, not just the styling hook
    document.documentElement.setAttribute("lang", lang === "en" ? "en" : "ko");
    document.querySelectorAll(".lang-btn").forEach(function (btn) {
      btn.classList.toggle("active", btn.dataset.setLang === lang);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".lang-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var lang = btn.dataset.setLang;
        localStorage.setItem("site-lang", lang);
        apply(lang);
      });
    });
    apply(document.documentElement.getAttribute("data-lang") || "ko");
  });
})();
