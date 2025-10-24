document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ DOM fully loaded, AJAX handlers active.");

  // --- Utilities ---
  const getCSRFToken = () => {
    const name = 'csrftoken';
    return document.cookie.split(';').map(c => c.trim()).find(c => c.startsWith(name + '='))?.split('=')[1] || '';
  };

  const showToast = (message, type = "info") => {
    const container = document.createElement("div");
    container.className = `
      fixed bottom-4 right-4 px-4 py-3 rounded-lg text-white shadow-lg
      ${type === "success" ? "bg-green-500" :
        type === "error" ? "bg-red-500" :
        "bg-blue-500"}
      transition transform duration-500 ease-out opacity-0 translate-x-10
    `;
    container.textContent = message;
    document.body.appendChild(container);

    setTimeout(() => {
      container.classList.remove("opacity-0", "translate-x-10");
      container.classList.add("opacity-100", "translate-x-0");
    }, 50);

    setTimeout(() => {
      container.classList.add("opacity-0", "translate-y-2");
      setTimeout(() => container.remove(), 500);
    }, 3000);
  };

  // --- Modal Logic ---
  const modal = document.getElementById("ajaxModal");
  const modalContent = document.getElementById("ajaxModalContent");
  const closeModalBtn = document.getElementById("closeModalBtn");

  const openModal = () => modal && (modal.classList.remove("hidden"), modal.classList.add("flex"));
  const closeModal = () => modal && (modal.classList.add("hidden"), modal.classList.remove("flex"), modalContent.innerHTML = "");

  if (closeModalBtn) closeModalBtn.addEventListener("click", closeModal);
  if (modal) modal.addEventListener("click", e => e.target === modal && closeModal());

  // --- Open Modal via AJAX ---
  document.addEventListener("click", async e => {
    const btn = e.target.closest("[data-ajax-url]");
    if (!btn) return;
    e.preventDefault();

    const url = btn.getAttribute("data-ajax-url");
    try {
      const resp = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } });
      if (!resp.ok) return showToast("Failed to fetch form", "error");
      modalContent.innerHTML = await resp.text();
      openModal();
    } catch (err) {
      console.error(err);
      showToast("Error loading form", "error");
    }
  });

  // --- Handle AJAX Form Submission ---
  document.addEventListener("submit", async e => {
    const form = e.target;
    if (!form.classList.contains("ajax-form")) return;
    e.preventDefault();

    const url = form.action;
    const method = form.method.toUpperCase();
    const formData = new FormData(form);

    try {
      const resp = await fetch(url, {
        method,
        body: formData,
        headers: { "X-CSRFToken": getCSRFToken(), "X-Requested-With": "XMLHttpRequest" }
      });

      if (resp.ok) {
        const data = await resp.json();

        // Update match list or prediction list dynamically
        if (data.updateTarget && data.html) {
          const target = document.querySelector(data.updateTarget);
          if (target) target.innerHTML = data.html;
        }

        showToast(data.message || "Action successful!", "success");
        closeModal();
      } else {
        modalContent.innerHTML = await resp.text(); // render form with errors
      }
    } catch (err) {
      console.error(err);
      showToast("Something went wrong.", "error");
    }
  });

  // --- AJAX Delete ---
  document.addEventListener("click", async e => {
    const delBtn = e.target.closest("[data-delete-url]");
    if (!delBtn) return;
    e.preventDefault();

    if (!confirm("Are you sure you want to delete this item?")) return;

    const url = delBtn.getAttribute("data-delete-url");
    try {
      const resp = await fetch(url, {
        method: "POST",
        headers: { "X-CSRFToken": getCSRFToken(), "X-Requested-With": "XMLHttpRequest" }
      });

      if (resp.ok) {
        const data = await resp.json();
        if (data.removeTarget) {
          const target = document.querySelector(data.removeTarget);
          if (target) target.remove();
        }
        showToast(data.message || "Item deleted!", "success");
      } else {
        showToast("Delete failed", "error");
      }
    } catch (err) {
      console.error(err);
      showToast("Error deleting item", "error");
    }
  });

});
