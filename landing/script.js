const appUrl = window.DATANOTES_APP_URL || "http://localhost:5173"
document.querySelectorAll("[data-app-link]").forEach((link) => {
  link.href = appUrl
})

const items = document.querySelectorAll(".reveal")