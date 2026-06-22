const navItems = document.querySelectorAll(".nav-item");
const views = document.querySelectorAll(".view");
const aiContext = document.getElementById("ai-context");

navItems.forEach((item) => {
  item.addEventListener("click", () => {
    const target = item.dataset.view;

    navItems.forEach((n) => n.classList.toggle("active", n === item));
    views.forEach((v) => v.classList.toggle("active", v.id === `view-${target}`));

    aiContext.style.display = target === "scan" ? "flex" : "none";
  });
});
