/** @odoo-module **/

const LOGOUT_BUTTON_ID = "lesotho_logout_button";

function addLogoutButton() {
  const navbar = document.querySelector(".o_main_navbar");
  const systray = navbar && navbar.querySelector(".o_menu_systray");

  if (!systray || document.getElementById(LOGOUT_BUTTON_ID)) {
    return;
  }

  const logoutButton = document.createElement("a");
  logoutButton.id = LOGOUT_BUTTON_ID;
  logoutButton.className = "lesotho_logout_button";
  logoutButton.href = "/web/session/logout?redirect=/web/login";
  logoutButton.textContent = "Logout";

  systray.appendChild(logoutButton);
}

function watchForNavbar() {
  addLogoutButton();

  const observer = new MutationObserver(addLogoutButton);
  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", watchForNavbar);
} else {
  watchForNavbar();
}
