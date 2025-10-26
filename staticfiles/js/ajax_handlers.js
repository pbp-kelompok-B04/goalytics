document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ DOM loaded, GLOBAL AJAX handlers v3 active.");

    // --- Utilities ---
    // ✅ Proper CSRF cookie reader (Django official implementation)
    const getCSRFToken = () => {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith("csrftoken=")) {
                    cookieValue = decodeURIComponent(cookie.substring("csrftoken=".length));
                    break;
                }
            }
        }
        return cookieValue;
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



    // --- Standard Modal Logic ---
    const modal = document.getElementById("ajaxModal");
    // ✅ Support both ID naming conventions used across templates
    const modalContent = document.getElementById("ajaxModalContent") || document.getElementById("ajaxModalBody");
    const closeModalBtn = document.getElementById("closeModalBtn") || document.getElementById("ajaxModalClose");

    const openModal = () => { 
        if (!modal) return;
        modal.classList.remove("hidden"); 
    };
    const closeModal = () => { 
        if (!modal) return;
        modal.classList.add("hidden"); 
    };
    if (closeModalBtn) closeModalBtn.addEventListener("click", closeModal);
    if (modal) modal.addEventListener("click", e => { if (e.target === modal) closeModal(); });
    window.addEventListener("keydown", (e) => { if (e.key === "Escape") closeModal(); }); // Close on Escape

    // --- Main Container for Event Delegation ---
    const mainContentArea = document.body;

    mainContentArea.addEventListener("click", async (e) => {
        // --- Handle Modal Loading Buttons ---
        const loadModalButton = e.target.closest("button[data-ajax-url]:not([data-delete-url])");
        if (loadModalButton) {
            e.preventDefault();
            e.stopPropagation();
            const url = loadModalButton.getAttribute("data-ajax-url");
            if (!url) return console.error("Modal button missing data-ajax-url");

            console.log("Modal Load Button Clicked! URL:", url);
            openModal();
            if (!modalContent) return console.error("#ajaxModalContent or #ajaxModalBody not found");
            modalContent.innerHTML = '<div class="py-8 text-center text-sm text-slate-500">Loading…</div>';

            try {
                const resp = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } });
                if (!resp.ok) {
                    console.error("Failed to fetch form:", resp.status, await resp.text());
                    showToast("Failed to fetch form", "error");
                    modalContent.innerHTML = '<p class="text-red-500 text-center">Error loading content.</p>';
                    return;
                }
                modalContent.innerHTML = await resp.text();
            } catch (err) {
                console.error("Error loading modal:", err);
                showToast("Error loading form", "error");
                modalContent.innerHTML = '<p class="text-red-500 text-center">Error loading content.</p>';
            }
            return;
        }

        // --- Handle Deletion Buttons ---
        const deleteButton = e.target.closest("button[data-delete-url]");
        if (deleteButton) {
            e.preventDefault();
            e.stopPropagation();
            const url = deleteButton.getAttribute("data-delete-url");
            if (!url) return console.error("Delete button missing data-delete-url");

            console.log("Delete Button Clicked! URL:", url);
            if (!confirm("Are you sure you want to delete this item?")) return;

            const token = getCSRFToken();
            if (!token || token.length < 32) {
                alert("CSRF token missing or invalid. Please refresh and try again.");
                return;
            }

            try {
                const resp = await fetch(url, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": token,
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    credentials: "include",
                });

                if (resp.ok) {
                    const data = await resp.json();
                    console.log("Delete response:", data);
                    if (data.removeTarget) {
                        const target = document.querySelector(data.removeTarget);
                        if (target) {
                            console.log("Removing target:", data.removeTarget);
                            target.remove();
                        } else {
                            console.warn("Remove target not found:", data.removeTarget);
                            if (data.updateTarget && data.html) {
                                const listTarget = document.querySelector(data.updateTarget);
                                if (listTarget) listTarget.innerHTML = data.html;
                                console.log("Fallback: Refreshed list target:", data.updateTarget);
                            } else {
                                window.location.reload();
                            }
                        }
                    } else if (data.updateTarget && data.html) {
                        const listTarget = document.querySelector(data.updateTarget);
                        if (listTarget) listTarget.innerHTML = data.html;
                        console.log("Refreshed list target after delete:", data.updateTarget);
                    }
                    showToast(data.message || "Item deleted!", "success");
                } else {
                    console.error("Delete failed:", resp.status, await resp.text());
                    showToast("Delete failed", "error");
                }
            } catch (err) {
                console.error("Error deleting item:", err);
                showToast("Error deleting item", "error");
            }
            return;
        }
    });

    // --- Handle AJAX Form Submission ---
    document.body.addEventListener("submit", async (e) => {
        const form = e.target;
        // ✅ Support forms inside either #ajaxModalContent or #ajaxModalBody
        if (!form.matches("#ajaxModalContent form.ajax-form, #ajaxModalBody form.ajax-form")) return;

        e.preventDefault();
        const url = form.action;
        const method = form.method.toUpperCase();
        const formData = new FormData(form);

        console.log("Submitting AJAX form to:", url);

        const token = getCSRFToken();
        if (!token || token.length < 32) {
            alert("CSRF token missing or invalid. Please refresh and try again.");
            return;
        }

        try {
            const resp = await fetch(url, {
                method,
                body: formData,
                headers: {
                    "X-CSRFToken": token,
                    "X-Requested-With": "XMLHttpRequest",
                },
                credentials: "include",
            });

            if (resp.ok) {
                const data = await resp.json();
                console.log("Form submission success:", data);
                if (data.updateTarget && data.html) {
                    const target = document.querySelector(data.updateTarget);
                    if (target) {
                        console.log("Updating target:", data.updateTarget);
                        target.innerHTML = data.html;
                    } else {
                        console.warn("Update target not found:", data.updateTarget);
                    }
                }
                showToast(data.message || "Action successful!", "success");
                closeModal();
            } else {
                console.warn("Form submission failed:", resp.status);
                if (modalContent) modalContent.innerHTML = await resp.text();
            }
        } catch (err) {
            console.error("Error submitting form:", err);
            showToast("Something went wrong.", "error");
        }
    });

}); // End DOMContentLoaded
