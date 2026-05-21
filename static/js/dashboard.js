/* ═══════════════════════════════════════════════════════════
   RABIT — Dashboard JavaScript
   ═══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');

  /* ── SIDEBAR TOGGLE ── */
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function () {
      if (window.innerWidth <= 768) {
        sidebar.classList.toggle('mobile-open');
      } else {
        sidebar.classList.toggle('collapsed');
      }
    });
  }

  /* ── DASHBOARD PAGE TABS (SPA-style within Django page) ── */
  function showDashPage(pageId) {
    document.querySelectorAll('.db-page').forEach(function (p) {
      p.classList.remove('on');
    });
    document.querySelectorAll('.db-na').forEach(function (a) {
      a.classList.remove('on');
    });
    const page = document.getElementById('dp-' + pageId);
    if (page) {
      page.classList.add('on');
    } else {
      const home = document.getElementById('dp-home');
      if (home) home.classList.add('on');
    }

    const navItem = document.querySelector('[data-page="' + pageId + '"]');
    if (navItem) navItem.classList.add('on');

    const titleEl = document.getElementById('topbarTitle');
    if (titleEl && navItem) {
      titleEl.textContent = navItem.querySelector('.db-na-lbl') ?
        navItem.querySelector('.db-na-lbl').textContent : '';
    }
  }
  window.showDashPage = showDashPage;

  window.openUserProfile = function () {
    var role = (document.body && document.body.getAttribute('data-user-role')) || '';
    var profilePages = { startup: 'profile', investor: 'profile', advisor: 'profile' };
    var pageId = profilePages[role] || 'profile';
    if (document.getElementById('dp-' + pageId) && typeof window.showDashPage === 'function') {
      window.showDashPage(pageId);
      return;
    }
    if (role === 'startup' && document.getElementById('dp-settings') && typeof window.showDashPage === 'function') {
      window.showDashPage('settings');
      return;
    }
    var urls = {
      startup: '/dashboard/startup/?page=profile',
      investor: '/dashboard/investor/?page=profile',
      advisor: '/dashboard/advisor/?page=profile'
    };
    if (urls[role]) {
      window.location.href = urls[role];
    }
  };

  // Wire up nav items
  document.querySelectorAll('[data-page]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const pageId = btn.getAttribute('data-page');
      showDashPage(pageId);
    });
  });

  // Respect ?page= in URL; otherwise keep the page marked .on in HTML
  var pageParam = new URLSearchParams(window.location.search).get('page');
  if (pageParam && document.getElementById('dp-' + pageParam)) {
    showDashPage(pageParam);
  }

  /* ── SIDEBAR PROGRESS BAR ANIMATION ── */
  const dbFill = document.querySelector('.db-fill');
  if (dbFill) {
    const target = dbFill.getAttribute('data-width') || '0%';
    dbFill.style.width = '0%';
    setTimeout(function () {
      dbFill.style.width = target;
    }, 300);
  }

  /* ── ONBOARDING WIZARD ── */
  let currentStep = 1;
  const totalSteps = document.querySelectorAll('.ob-step').length;

  function goToStep(step) {
    if (step < 1 || step > totalSteps) return;
    currentStep = step;

    document.querySelectorAll('.ob-panel-step').forEach(function (p, i) {
      p.style.display = (i + 1 === step) ? 'block' : 'none';
    });

    document.querySelectorAll('.ob-step-dot').forEach(function (dot, i) {
      dot.classList.remove('done', 'curr');
      const lbl = dot.parentElement.querySelector('.ob-step-lbl');
      if (lbl) lbl.classList.remove('done', 'curr');

      if (i + 1 < step) {
        dot.classList.add('done');
        dot.innerHTML = '<i class="ti ti-check" style="font-size:.7rem"></i>';
        if (lbl) lbl.classList.add('done');
      } else if (i + 1 === step) {
        dot.classList.add('curr');
        dot.textContent = i + 1;
        if (lbl) lbl.classList.add('curr');
      } else {
        dot.textContent = i + 1;
      }
    });

    const prog = document.getElementById('ob-progress');
    if (prog) prog.textContent = 'خطوة ' + step + ' من ' + totalSteps;
  }

  const nextBtns = document.querySelectorAll('[data-ob-next]');
  const prevBtns = document.querySelectorAll('[data-ob-prev]');

  nextBtns.forEach(function (btn) {
    btn.addEventListener('click', function () { goToStep(currentStep + 1); });
  });
  prevBtns.forEach(function (btn) {
    btn.addEventListener('click', function () { goToStep(currentStep - 1); });
  });

  if (document.querySelector('.ob-step')) goToStep(1);

  /* ── FILE UPLOAD PREVIEW ── */
  document.querySelectorAll('.upload-zone input[type="file"]').forEach(function (input) {
    input.addEventListener('change', function () {
      const zone = input.closest('.upload-zone');
      if (!zone || !input.files[0]) return;
      const name = zone.querySelector('.upload-filename');
      if (name) name.textContent = input.files[0].name;
      zone.classList.add('has-file');
    });
  });

});
