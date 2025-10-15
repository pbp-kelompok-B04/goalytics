function getCookie(name){
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return decodeURIComponent(parts.pop().split(';').shift());
}
const csrftoken = getCookie('csrftoken');

function showToast(msg, ok=true){
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = msg;
  el.style.display = "block";
  el.style.borderColor = ok ? "#5cb85c" : "#d9534f";
  setTimeout(()=> el.style.display="none", 2500);
}

window.addEventListener("DOMContentLoaded", () => {
  // Register
  const reg = document.getElementById("register-form");
  if (reg){
    reg.addEventListener("submit", async (e)=>{
      e.preventDefault();
      const resp = await fetch(reg.dataset.endpoint, {
        method:"POST",
        headers:{"X-CSRFToken": csrftoken},
        body: new FormData(reg),
        credentials:"same-origin",
      });
      const j = await resp.json();
      if (j.ok){ showToast(j.message); location.href="/auth/login/"; }
      else { showToast(JSON.stringify(j.errors), false); }
    });
  }

  // Login
  const login = document.getElementById("login-form");
  if (login){
    login.addEventListener("submit", async (e)=>{
      e.preventDefault();
      const resp = await fetch(login.dataset.endpoint, {
        method:"POST",
        headers:{"X-CSRFToken": csrftoken},
        body: new FormData(login),
        credentials:"same-origin",
      });
      const j = await resp.json();
      if (j.ok){ showToast(j.message); location.href="/"; }
      else { showToast(JSON.stringify(j.errors), false); }
    });
  }

  // Logout
  const btnLogout = document.getElementById("btn-logout");
  if (btnLogout){
    btnLogout.addEventListener("click", async ()=>{
      const resp = await fetch(btnLogout.dataset.endpoint, {
        method:"POST",
        headers:{"X-CSRFToken": csrftoken},
        credentials:"same-origin",
      });
      const j = await resp.json();
      if (j.ok){ showToast(j.message); location.href="/auth/login/"; }
    });
  }

  // Profil: read
  const pv = document.getElementById("profile-view");
  if (pv){
    (async ()=>{
      const resp = await fetch(pv.dataset.endpoint, {credentials:"same-origin"});
      const j = await resp.json();
      if (j.ok){
        const d = j.data;
        pv.innerHTML = `
          <ul>
            <li><b>Username:</b> ${d.username}</li>
            <li><b>Email:</b> ${d.email || "-"}</li>
            <li><b>Preferensi Liga:</b> ${d.preferred_league || "-"}</li>
            <li><b>Klub Favorit:</b> ${d.favorite_club || "-"}</li>
            <li><b>Mode Tampilan:</b> ${d.display_mode}</li>
            <li><b>Bio:</b> ${d.bio ? d.bio.replace(/\n/g,"<br>") : "-"}</li>
          </ul>
        `;
      } else {
        pv.textContent = "Gagal memuat profil.";
      }
    })();
  }

  // Profil: update
  const pf = document.getElementById("profile-form");
  if (pf){
    pf.addEventListener("submit", async (e)=>{
      e.preventDefault();
      const resp = await fetch(pf.dataset.endpoint, {
        method:"POST",
        headers:{"X-CSRFToken": csrftoken},
        body: new FormData(pf),
        credentials:"same-origin",
      });
      const j = await resp.json();
      if (j.ok){ showToast(j.message); location.href="/"; }
      else { showToast(JSON.stringify(j.errors), false); }
    });
  }
});
