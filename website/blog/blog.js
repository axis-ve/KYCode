// Blog page enhancements: scroll reveals, stat count-ups, the reading bar, and Fig. 1's fix picker.
// Everything here is optional; without it the page reads the same, just without motion.
const root = document.documentElement;
const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
root.classList.add('js');

function countUp(el) {
  const target = Number(el.dataset.count);
  if (still || !target) return;
  const start = performance.now();
  const tick = now => {
    const t = Math.min(1, (now - start) / 900);
    el.textContent = `${Math.round(target * (1 - (1 - t) ** 3))}%`;
    if (t < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

const revealables = document.querySelectorAll('[data-reveal]');
const show = el => {
  el.classList.add('in');
  el.querySelectorAll('[data-count]').forEach(countUp);
};
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      show(entry.target);
      observer.unobserve(entry.target);
    }
  }, { threshold: 0.2, rootMargin: '0px 0px -8% 0px' });
  revealables.forEach(el => observer.observe(el));
} else {
  revealables.forEach(show);
}

const bar = document.querySelector('.progress');
if (bar) {
  const update = () => {
    const max = root.scrollHeight - innerHeight;
    bar.style.transform = `scaleX(${max > 0 ? Math.min(1, scrollY / max) : 0})`;
  };
  addEventListener('scroll', update, { passive: true });
  addEventListener('resize', update);
  update();
}

const captions = {
  today: 'Today, Save runs the title through the helper and loses its capitals. Search and Export use the same helper.',
  helper: 'Save keeps its capitals, but a search for “plans” now finds nothing, and exported files change name.',
  scoped: 'Save keeps its capitals. Search and Export still use the helper, so they behave as before. This is the fix the reach check leads to.',
};
document.querySelectorAll('.fig.reach').forEach(fig => {
  const caption = fig.querySelector('.fig-caption');
  const buttons = fig.querySelectorAll('[data-set]');
  buttons.forEach(button => button.addEventListener('click', () => {
    fig.dataset.state = button.dataset.set;
    buttons.forEach(other => other.setAttribute('aria-pressed', String(other === button)));
    caption.textContent = captions[button.dataset.set];
    fig.classList.remove('changed');
    void fig.offsetWidth; // restart the result animation
    fig.classList.add('changed');
  }));
});
