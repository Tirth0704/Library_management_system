/* ==========================================================================
   LibraryHub 2.0 — Live Search
   Powers the book search input on /books page.
   Calls /books/search API and shows dropdown results.
   ========================================================================== */

(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("live-search");
    const resultsContainer = document.getElementById("live-results");

    if (!searchInput || !resultsContainer) {
      return;
    }

    // Create dropdown container
    const dropdown = document.createElement("div");
    dropdown.className = "card shadow-sm border-0 mt-2";
    dropdown.style.display = "none";
    dropdown.id = "live-dropdown";
    resultsContainer.appendChild(dropdown);

    /* ─── Fetch results ───────────────────────────────────────────────── */
    async function fetchResults(query) {
      try {
        const url = `/books/search?q=${encodeURIComponent(query)}`;
        const response = await fetch(url, {
          headers: { Accept: "application/json" }
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        return data.books || [];
      } catch (err) {
        console.error("[LiveSearch] Fetch failed:", err);
        return [];
      }
    }

    /* ─── Render results in dropdown ─────────────────────────────────── */
    function renderResults(books) {
      if (books.length === 0) {
        dropdown.innerHTML =
          '<div class="p-3 text-center text-muted small">' +
          '<i class="bi bi-inbox"></i> No books match your search' +
          "</div>";
        dropdown.style.display = "block";
        return;
      }

      const html = books
        .map(function (book) {
          const statusBadge =
            book.available_copies > 0
              ? '<span class="badge bg-success">Available</span>'
              : '<span class="badge bg-secondary">Unavailable</span>';

          return `
            <a
              href="/books/${book.id}"
              class="list-group-item list-group-item-action live-search-item
                     d-flex justify-content-between align-items-center"
            >
              <div>
                <div class="fw-semibold">${escapeHtml(book.title)}</div>
                <small class="text-muted">
                  by ${escapeHtml(book.author)}
                  · ${escapeHtml(book.category)}
                </small>
              </div>
              <div class="text-end">
                ${statusBadge}
                <div class="small text-muted mt-1">
                  Rent: ₹${(book.price * 0.1).toFixed(2)}
                </div>
              </div>
            </a>
          `;
        })
        .join("");

      dropdown.innerHTML = `<div class="list-group list-group-flush">${html}</div>`;
      dropdown.style.display = "block";
    }

    /* ─── Escape HTML for safety ─────────────────────────────────────── */
    function escapeHtml(str) {
      const div = document.createElement("div");
      div.textContent = str;
      return div.innerHTML;
    }

    /* ─── Hide dropdown ──────────────────────────────────────────────── */
    function hideDropdown() {
      dropdown.style.display = "none";
      dropdown.innerHTML = "";
    }

    /* ─── Handle input with debounce ─────────────────────────────────── */
    const handleInput = window.debounce
      ? window.debounce(async function (e) {
          const query = e.target.value.trim();
          if (query.length < 2) {
            hideDropdown();
            return;
          }
          const books = await fetchResults(query);
          renderResults(books);
        }, 300)
      : async function (e) {
          const query = e.target.value.trim();
          if (query.length < 2) {
            hideDropdown();
            return;
          }
          const books = await fetchResults(query);
          renderResults(books);
        };

    searchInput.addEventListener("input", handleInput);

    /* ─── Hide dropdown on outside click ─────────────────────────────── */
    document.addEventListener("click", function (e) {
      if (
        !searchInput.contains(e.target) &&
        !dropdown.contains(e.target)
      ) {
        hideDropdown();
      }
    });

    /* ─── Show dropdown again on focus (if query exists) ────────────── */
    searchInput.addEventListener("focus", function () {
      if (searchInput.value.trim().length >= 2 && dropdown.innerHTML) {
        dropdown.style.display = "block";
      }
    });

    /* ─── ESC to close ───────────────────────────────────────────────── */
    searchInput.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        hideDropdown();
        searchInput.blur();
      }
    });
  });
})();