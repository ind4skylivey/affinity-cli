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
