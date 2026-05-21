/* ═══════════════════════════════════════════════════════════
   RABIT Platform — Main JavaScript
   ═══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

  /* ── 1. THEME TOGGLE ── */
  const body = document.getElementById('body') || document.body;
  const themeToggle = document.getElementById('themeToggle');
  const saved = localStorage.getItem('rabit-theme') || 'light';
  body.className = (body.className || '').replace(/light-mode|dark-mode/g, '').trim();
  body.classList.add(saved + '-mode');

  if (themeToggle) {
    themeToggle.addEventListener('click', function () {
      const isDark = body.classList.contains('dark-mode');
      body.classList.toggle('dark-mode', !isDark);
      body.classList.toggle('light-mode', isDark);
      localStorage.setItem('rabit-theme', isDark ? 'light' : 'dark');
    });
  }

  /* ── 2. MOBILE HAMBURGER ── */
  const hamburger = document.getElementById('hamburger');
  const mobileMenu = document.getElementById('mobileMenu');
  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', function () {
      const isOpen = mobileMenu.classList.toggle('open');
      hamburger.classList.toggle('open', isOpen);
      body.style.overflow = isOpen ? 'hidden' : '';
    });
    document.querySelectorAll('.mobile-link').forEach(function (l) {
      l.addEventListener('click', function () {
        mobileMenu.classList.remove('open');
        hamburger.classList.remove('open');
        body.style.overflow = '';
      });
    });
  }

  /* ── 3. SMOOTH SCROLL ── */
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        window.scrollTo({ top: target.getBoundingClientRect().top + window.scrollY - 80, behavior: 'smooth' });
      }
    });
  });

  /* ── 4. HEADER SHADOW ON SCROLL ── */
  const header = document.getElementById('header');
  if (header) {
    window.addEventListener('scroll', function () {
      header.style.boxShadow = window.scrollY > 20 ? '0 4px 24px rgba(0,0,0,.1)' : 'none';
    }, { passive: true });
  }

  /* ── 5. FAQ ACCORDION ── */
  document.querySelectorAll('.faq-item').forEach(function (item) {
    const btn = item.querySelector('.faq-question');
    if (!btn) return;
    btn.addEventListener('click', function () {
      const isOpen = item.classList.contains('open');
      document.querySelectorAll('.faq-item').forEach(function (fi) {
        fi.classList.remove('open');
        const q = fi.querySelector('.faq-question');
        const a = fi.querySelector('.faq-answer');
        if (q) q.setAttribute('aria-expanded', 'false');
        if (a) a.classList.remove('open');
      });
      if (!isOpen) {
        item.classList.add('open');
        btn.setAttribute('aria-expanded', 'true');
        const ans = item.querySelector('.faq-answer');
        if (ans) ans.classList.add('open');
      }
    });
  });

  /* ── 6. FADE-UP INTERSECTION OBSERVER ── */
  body.classList.add('js-ready');
  const obs = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
  document.querySelectorAll('.fade-up').forEach(function (el) { obs.observe(el); });

  /* ── 7. ACTIVE NAV LINK ── */
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-desktop a[href^="#"]');
  if (sections.length && navLinks.length) {
    window.addEventListener('scroll', function () {
      let cur = '';
      sections.forEach(function (s) { if (window.scrollY >= s.offsetTop - 100) cur = '#' + s.id; });
      navLinks.forEach(function (l) { l.classList.toggle('active', l.getAttribute('href') === cur); });
    }, { passive: true });
  }

  /* ── 8. COUNTER ANIMATION ── */
  function animateCounter(el, target, prefix) {
    let start = null;
    const duration = 1500;
    function step(ts) {
      if (!start) start = ts;
      const p = Math.min((ts - start) / duration, 1);
      const ease = 1 - Math.pow(1 - p, 3);
      el.textContent = prefix + Math.round(ease * target);
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  const heroSection = document.getElementById('hero');
  if (heroSection) {
    const heroObs = new IntersectionObserver(function (entries) {
      if (entries[0].isIntersecting) {
        var counters = [
          ['.hero-stats .stat:nth-child(1) strong', 200, '+'],
          ['.hero-stats .stat:nth-child(3) strong', 85, '+'],
          ['.hero-stats .stat:nth-child(5) strong', 40, '+'],
        ];
        counters.forEach(function (c) {
          var el = document.querySelector(c[0]);
          if (el) animateCounter(el, c[1], c[2]);
        });
        heroObs.disconnect();
      }
    }, { threshold: 0.3 });
    heroObs.observe(heroSection);
  }

  /* ── 9. SCORECARD BAR ANIMATION ── */
  const scp = document.querySelector('.score-card-preview');
  if (scp) {
    let done = false;
    const scpObs = new IntersectionObserver(function (entries) {
      if (entries[0].isIntersecting && !done) {
        done = true;
        document.querySelectorAll('.scp-bar>div').forEach(function (b) {
          const w = b.style.width;
          b.style.width = '0%';
          setTimeout(function () {
            b.style.transition = 'width 1s ease';
            b.style.width = w;
          }, 100);
        });
      }
    }, { threshold: 0.3 });
    scpObs.observe(scp);
  }

  /* ── 10. CARD TILT EFFECT ── */
  document.querySelectorAll('.featured-card,.pricing-card').forEach(function (card) {
    card.addEventListener('mousemove', function (e) {
      const r = card.getBoundingClientRect();
      const mx = (e.clientX - r.left) / r.width - 0.5;
      const my = (e.clientY - r.top) / r.height - 0.5;
      card.style.transform = 'perspective(800px) rotateX(' + (my * -6) + 'deg) rotateY(' + (mx * 6) + 'deg) translateY(-4px)';
    });
    card.addEventListener('mouseleave', function () { card.style.transform = ''; });
  });

  /* ── 11. AUTO-DISMISS TOASTS ── */
  document.querySelectorAll('[data-auto-dismiss]').forEach(function (toast) {
    setTimeout(function () {
      toast.style.animation = 'slideOut .3s ease forwards';
      setTimeout(function () { toast.remove(); }, 300);
    }, 4000);
  });

  /* ── 12. PASSWORD TOGGLE EYE ── */
  document.querySelectorAll('.pw-eye').forEach(function (eye) {
    eye.addEventListener('click', function () {
      const input = document.getElementById('pw-field') || eye.previousElementSibling;
      if (!input) return;
      const isText = input.type === 'text';
      input.type = isText ? 'password' : 'text';
      eye.classList.toggle('ti-eye', isText);
      eye.classList.toggle('ti-eye-off', !isText);
    });
  });

});

/* CSS for slideOut */
const style = document.createElement('style');
style.textContent = '@keyframes slideOut{to{transform:translateX(120%);opacity:0}}';
document.head.appendChild(style);
