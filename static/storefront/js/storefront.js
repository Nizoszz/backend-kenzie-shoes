const menuButton = document.querySelector("[data-menu-toggle]");
const menu = document.querySelector("[data-menu]");
if (menuButton && menu) {
  menuButton.addEventListener("click", () => {
    const open = menu.classList.toggle("is-open");
    menuButton.setAttribute("aria-expanded", String(open));
  });
}

const drawer = document.querySelector("[data-cart-drawer]");
const backdrop = document.querySelector(".drawer-backdrop");
const setDrawer = (open) => {
  if (!drawer) return;
  drawer.classList.toggle("is-open", open);
  backdrop?.classList.toggle("is-open", open);
  drawer.setAttribute("aria-hidden", String(!open));
  document.body.classList.toggle("drawer-open", open);
};
document.querySelector("[data-cart-open]")?.addEventListener("click", () => setDrawer(true));
document.querySelectorAll("[data-cart-close]").forEach((button) => button.addEventListener("click", () => setDrawer(false)));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") setDrawer(false);
});

const filterForm = document.querySelector("[data-auto-filter-form]");
if (filterForm) {
  const searchInput = filterForm.querySelector("[data-filter-search]");
  const categoryInput = filterForm.querySelector("[data-filter-category]");
  const filterStatus = filterForm.querySelector("[data-filter-status]");
  let filterTimer;

  const submitFilters = () => {
    if (filterStatus) filterStatus.textContent = "Atualizando resultados";
    filterForm.requestSubmit();
  };

  const debounceFilter = (delay) => {
    window.clearTimeout(filterTimer);
    if (filterStatus) filterStatus.textContent = "Aguardando pesquisa";
    filterTimer = window.setTimeout(submitFilters, delay);
  };

  searchInput?.addEventListener("input", () => debounceFilter(400));
  categoryInput?.addEventListener("change", () => debounceFilter(150));
  filterForm.addEventListener("submit", () => window.clearTimeout(filterTimer));
}
