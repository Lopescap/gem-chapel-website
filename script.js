/* ============================================================
   GEM Chapel — Catch The Fire
   Scripts
   ============================================================ */

(function () {
  'use strict';

  // ─── NAV SCROLL EFFECT ───
  const navbar = document.getElementById('navbar');
  let lastScroll = 0;

  window.addEventListener('scroll', () => {
    const y = window.scrollY;
    navbar.classList.toggle('scrolled', y > 60);
    lastScroll = y;
  }, { passive: true });

  // ─── MOBILE NAV TOGGLE ───
  const navToggle = document.getElementById('navToggle');
  const navLinks = document.getElementById('navLinks');

  navToggle.addEventListener('click', () => {
    const isOpen = navLinks.classList.toggle('open');
    navToggle.classList.toggle('active', isOpen);
    document.body.style.overflow = isOpen ? 'hidden' : '';
  });

  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      navLinks.classList.remove('open');
      navToggle.classList.remove('active');
      document.body.style.overflow = '';
    });
  });

  // ─── ACTIVE NAV HIGHLIGHTING ───
  const sections = document.querySelectorAll('section[id]');
  const navItems = document.querySelectorAll('.nav-links a[href^="#"]');

  function updateActiveNav() {
    const scrollY = window.scrollY + 120;

    let currentId = '';
    sections.forEach(section => {
      if (section.offsetTop <= scrollY) {
        currentId = section.id;
      }
    });

    navItems.forEach(a => {
      a.classList.toggle('active', a.getAttribute('href') === '#' + currentId);
    });
  }

  window.addEventListener('scroll', updateActiveNav, { passive: true });

  // ─── FLAME PARTICLES ───
  const heroFlames = document.getElementById('heroFlames');

  function createParticles() {
    const count = window.innerWidth < 768 ? 25 : 50;
    for (let i = 0; i < count; i++) {
      const p = document.createElement('div');
      p.className = 'flame-particle';
      const x = Math.random() * 100;
      const size = 2 + Math.random() * 5;
      const duration = 5 + Math.random() * 10;
      const delay = Math.random() * 12;
      const hue = 25 + Math.random() * 25;
      const lightness = 50 + Math.random() * 30;

      p.style.cssText =
        'left:' + x + '%;' +
        'bottom:-10px;' +
        'width:' + size + 'px;' +
        'height:' + size + 'px;' +
        'background:hsl(' + hue + ',100%,' + lightness + '%);' +
        'animation-duration:' + duration + 's;' +
        'animation-delay:' + delay + 's;' +
        'filter:blur(' + (Math.random() > 0.6 ? '1px' : '0') + ');';

      heroFlames.appendChild(p);
    }
  }

  createParticles();

  // ─── SCROLL REVEAL ───
  const reveals = document.querySelectorAll('.reveal');
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

  reveals.forEach(el => revealObserver.observe(el));

  // ─── COUNTER ANIMATION ───
  function animateCounter(el, target, suffix) {
    suffix = suffix || '';
    const duration = 2000;
    const start = performance.now();

    function step(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(eased * target);
      el.textContent = current + suffix;

      if (progress < 1) {
        requestAnimationFrame(step);
      }
    }

    requestAnimationFrame(step);
  }

  // Observe stat numbers for counter animation
  const statElements = document.querySelectorAll('[data-count]');
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseInt(el.getAttribute('data-count'), 10);
        const suffix = el.getAttribute('data-suffix') || '';
        animateCounter(el, target, suffix);
        counterObserver.unobserve(el);
      }
    });
  }, { threshold: 0.5 });

  statElements.forEach(el => counterObserver.observe(el));

  // ─── SMOOTH SCROLL ───
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const href = this.getAttribute('href');
      if (href === '#') return;
      const target = document.querySelector(href);
      if (target) {
        const offset = navbar.offsetHeight + 10;
        const top = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top: top, behavior: 'smooth' });
      }
    });
  });

  // ─── FORM INTERACTION ───
  const formSubmit = document.querySelector('.form-submit');
  if (formSubmit) {
    formSubmit.addEventListener('click', function (e) {
      e.preventDefault();
      const name = document.getElementById('name');
      const email = document.getElementById('email');

      if (!name.value || !email.value) {
        // Subtle shake on empty required fields
        [name, email].forEach(function (input) {
          if (!input.value) {
            input.style.borderColor = 'var(--flame-deep)';
            input.style.animation = 'shake 0.4s ease';
            setTimeout(function () {
              input.style.borderColor = '';
              input.style.animation = '';
            }, 600);
          }
        });
        return;
      }

      // Visual success feedback
      this.textContent = 'Message Sent!';
      this.style.background = 'linear-gradient(135deg, #2d8a4e, #1a6b35)';
      setTimeout(function () {
        formSubmit.textContent = 'Send Message \u2192';
        formSubmit.style.background = '';
      }, 3000);
    });
  }

})();
