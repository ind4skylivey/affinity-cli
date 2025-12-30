// ============================================
// Affinity CLI - Premium Interactive Effects
// ============================================

// Copy to clipboard functionality
const copyButtons = document.querySelectorAll('[data-copy]');
copyButtons.forEach((btn) => {
  const label = btn.textContent;
  btn.addEventListener('click', async () => {
    const payload = btn.getAttribute('data-copy');
    try {
      await navigator.clipboard.writeText(payload);
      btn.textContent = '✓ Copied!';
      btn.classList.add('copied');
    } catch (err) {
      console.error('Copy failed', err);
      btn.textContent = '✗ Failed';
    }
    setTimeout(() => {
      btn.textContent = label;
      btn.classList.remove('copied');
    }, 2000);
  });
});

// Smooth scrolling for anchor links
const smoothLinks = document.querySelectorAll('a[href^="#"]');
smoothLinks.forEach((link) => {
  link.addEventListener('click', (e) => {
    const target = document.querySelector(link.getAttribute('href'));
    if (!target) return;
    e.preventDefault();
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});

// Scroll button handlers
const scrollButtons = document.querySelectorAll('[data-scroll]');
scrollButtons.forEach((btn) => {
  btn.addEventListener('click', () => {
    const target = document.querySelector(btn.getAttribute('data-scroll'));
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});

// ============================================
// Theme Toggle
// ============================================
const body = document.body;
const toggle = document.getElementById('theme-toggle');
const savedTheme = localStorage.getItem('affinity-theme');

function applyTheme(mode) {
  if (mode === 'light') {
    body.classList.add('theme-light');
    toggle.textContent = '◐ Dark';
  } else {
    body.classList.remove('theme-light');
    toggle.textContent = '◑ Light';
  }
  localStorage.setItem('affinity-theme', mode);
}

if (savedTheme === 'light') {
  applyTheme('light');
} else {
  applyTheme('dark');
}

if (toggle) {
  toggle.addEventListener('click', () => {
    const next = body.classList.contains('theme-light') ? 'dark' : 'light';
    applyTheme(next);
  });
}

// ============================================
// Scroll Animations (Intersection Observer)
// ============================================
const observerOptions = {
  root: null,
  rootMargin: '0px 0px -80px 0px',
  threshold: 0.1
};

const animateOnScroll = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      // Optional: unobserve after animation
      // animateOnScroll.unobserve(entry.target);
    }
  });
}, observerOptions);

// Animate sections
document.querySelectorAll('.section, .grid, .front-hero, .hero, .faq, .media').forEach((el) => {
  el.classList.add('animate-on-scroll');
  animateOnScroll.observe(el);
});

// Animate cards with stagger effect
document.querySelectorAll('.card, .matrix-card, .profile-card, .trading-card, .step, .qa').forEach((el, index) => {
  el.classList.add('animate-on-scroll', 'animate-card');
  el.style.setProperty('--stagger-delay', `${index * 0.08}s`);
  animateOnScroll.observe(el);
});

// ============================================
// Active Navigation Highlight
// ============================================
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav a[href^="#"], .subnav-chip[href^="#"]');

const highlightNav = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      const id = entry.target.getAttribute('id');
      navLinks.forEach((link) => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${id}`) {
          link.classList.add('active');
        }
      });
    }
  });
}, { rootMargin: '-20% 0px -60% 0px', threshold: 0 });

sections.forEach((section) => highlightNav.observe(section));

// ============================================
// Parallax Effect on Hero Banner
// ============================================
const heroBanner = document.querySelector('.front-hero__banner img');
if (heroBanner) {
  let ticking = false;
  window.addEventListener('scroll', () => {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        const scrolled = window.scrollY;
        const rate = scrolled * 0.3;
        if (scrolled < 600) {
          heroBanner.style.transform = `translateY(${rate}px) scale(1.02)`;
        }
        ticking = false;
      });
      ticking = true;
    }
  });
}

// ============================================
// Card Tilt Effect (3D hover)
// ============================================
const tiltCards = document.querySelectorAll('.card, .profile-card, .trading-card, .matrix-card');

tiltCards.forEach((card) => {
  card.addEventListener('mousemove', (e) => {
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateX = (y - centerY) / 20;
    const rotateY = (centerX - x) / 20;

    card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(10px)`;
  });

  card.addEventListener('mouseleave', () => {
    card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0px)';
  });
});

// ============================================
// Typing Effect for Command Pill
// ============================================
const commandPill = document.querySelector('.command-pill span');
if (commandPill) {
  const originalText = commandPill.textContent;
  commandPill.style.minWidth = `${commandPill.offsetWidth}px`;

  const typeText = () => {
    commandPill.textContent = '';
    let i = 0;
    const typeInterval = setInterval(() => {
      if (i < originalText.length) {
        commandPill.textContent += originalText.charAt(i);
        i++;
      } else {
        clearInterval(typeInterval);
      }
    }, 50);
  };

  // Type on initial view
  const commandObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        setTimeout(typeText, 300);
        commandObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  commandObserver.observe(commandPill.parentElement);
}

// ============================================
// Smooth Counter Animation for Stats
// ============================================
const animateCounter = (el) => {
  const target = el.textContent;
  const isNumber = /^\d+/.test(target);

  if (isNumber) {
    const num = parseInt(target);
    const suffix = target.replace(/^\d+/, '');
    let current = 0;
    const increment = num / 30;
    const timer = setInterval(() => {
      current += increment;
      if (current >= num) {
        el.textContent = target;
        clearInterval(timer);
      } else {
        el.textContent = Math.floor(current) + suffix;
      }
    }, 30);
  }
};

const statNums = document.querySelectorAll('.stat-num');
const statsObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      animateCounter(entry.target);
      statsObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

statNums.forEach((stat) => statsObserver.observe(stat));

// ============================================
// Button Ripple Effect
// ============================================
document.querySelectorAll('.btn').forEach((btn) => {
  btn.addEventListener('click', function(e) {
    const rect = this.getBoundingClientRect();
    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    ripple.style.left = `${e.clientX - rect.left}px`;
    ripple.style.top = `${e.clientY - rect.top}px`;
    this.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
  });
});

// ============================================
// Cursor Glow Effect (optional, subtle)
// ============================================
const glowCursor = document.createElement('div');
glowCursor.className = 'cursor-glow';
document.body.appendChild(glowCursor);

let cursorTimeout;
document.addEventListener('mousemove', (e) => {
  glowCursor.style.opacity = '1';
  glowCursor.style.left = `${e.clientX}px`;
  glowCursor.style.top = `${e.clientY}px`;

  clearTimeout(cursorTimeout);
  cursorTimeout = setTimeout(() => {
    glowCursor.style.opacity = '0';
  }, 1000);
});
