const copyButtons = document.querySelectorAll('[data-copy]');

copyButtons.forEach((btn) => {
  const label = btn.textContent;
  btn.addEventListener('click', async () => {
    const payload = btn.getAttribute('data-copy');
    try {
      await navigator.clipboard.writeText(payload);
      btn.textContent = 'Copied OK';
    } catch (err) {
      console.error('Copy failed', err);
      btn.textContent = 'Copy failed';
    }
    setTimeout(() => { btn.textContent = label; }, 1800);
  });
});

const smoothLinks = document.querySelectorAll('a[href^="#"]');
smoothLinks.forEach((link) => {
  link.addEventListener('click', (e) => {
    const target = document.querySelector(link.getAttribute('href'));
    if (!target) return;
    e.preventDefault();
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});

const scrollButtons = document.querySelectorAll('[data-scroll]');
scrollButtons.forEach((btn) => {
  btn.addEventListener('click', () => {
    const target = document.querySelector(btn.getAttribute('data-scroll'));
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});

const body = document.body;
const toggle = document.getElementById('theme-toggle');
const savedTheme = localStorage.getItem('affinity-theme');

function applyTheme(mode) {
  if (mode === 'light') {
    body.classList.add('theme-light');
    toggle.textContent = 'Dark';
  } else {
    body.classList.remove('theme-light');
    toggle.textContent = 'Light';
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
