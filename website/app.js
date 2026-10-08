const installDialog = document.querySelector('#install-dialog');
const aboutDialog = document.querySelector('#about-dialog');
document.querySelector('#install-open').addEventListener('click', event => { event.preventDefault(); selectHost(providerNames[providerIndex]); installDialog.showModal(); });
document.querySelector('#about-open').addEventListener('click', () => aboutDialog.showModal());
document.querySelector('#about-install').addEventListener('click', () => { aboutDialog.close(); selectHost(providerNames[providerIndex]); installDialog.showModal(); });
document.querySelectorAll('dialog').forEach(dialog => {
  dialog.querySelector('.close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) { const r = dialog.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close(); } });
});
const examples = [
  ['whatIsGoingOn', "That function you've been<br>avoiding? Let's open it."],
  ['whyIsThisBroken', "Follow the bug.<br>Find the actual reason."],
  ['canWeChangeThis', "Make the change.<br>Understand what moved."]
];
let example = 0;
document.querySelector('#cycle').addEventListener('click', () => {
  example = (example + 1) % examples.length;
  document.querySelector('#code').innerHTML = examples[example][0] + '<span>()</span>';
  document.querySelector('#explanation').innerHTML = examples[example][1];
  document.querySelector('#counter').textContent = `0${example + 1} / 03`;
});
// Each host keeps skills in its own folder and invokes them with its own prefix.
const hosts = {
  codex: { name: 'Codex', agent: 'codex', dir: '.agents/skills/', anchor: 'codex', prompt: '$know-your-code Help me understand this project.' },
  cursor: { name: 'Cursor', agent: 'cursor', dir: '.cursor/skills/', anchor: 'cursor', prompt: '/know-your-code Help me understand this project.' },
  claude: { name: 'Claude Code', agent: 'claude-code', dir: '.claude/skills/', anchor: 'claude-code', prompt: '/know-your-code Help me understand this project.' },
};
let host = hosts.codex;
let installView = 0;
const hostButtons = document.querySelectorAll('[data-host]');
function renderInstallCommand() {
  const parts = ['npx skills add', 'axis-ve/KYCode', `--agent ${host.agent}`, '--skill "*"'];
  const nodes = [];
  parts.forEach((part, index) => {
    if (index) nodes.push(document.createTextNode(' '));
    const token = document.createElement('span');
    token.textContent = part;
    if (index === 2) token.className = 'command-agent';
    nodes.push(token);
  });
  document.querySelector('#install-command').replaceChildren(...nodes);
}
function selectHost(name) {
  host = hosts[name];
  installView++;
  hostButtons.forEach(other => other.setAttribute('aria-pressed', String(other.dataset.host === name)));
  document.querySelector('#host-dir').textContent = host.dir;
  document.querySelector('#host-name').textContent = host.name;
  document.querySelector('#install-host').textContent = host.name;
  renderInstallCommand();
  document.querySelector('#native-install-link').href = `https://github.com/axis-ve/KYCode#${host.anchor}`;
  document.querySelector('#host-prompt').textContent = host.prompt;
  document.querySelector('#copy-label').textContent = 'COPY';
  document.querySelector('#install-copy-label').textContent = 'Copy';
  document.querySelector('#copy-status').textContent = '';
  document.querySelector('#install-copy-status').textContent = '';
}
// Picking an app is a decision: show its colours and stop rotating away from it.
hostButtons.forEach(button => button.addEventListener('click', () => {
  selectHost(button.dataset.host);
  providerPinned = true;
  showProvider(providerNames.indexOf(button.dataset.host));
}));
renderInstallCommand();
document.querySelectorAll('[data-copy-target]').forEach(button => button.addEventListener('click', async () => {
  const copiedHost = host;
  const copiedView = installView;
  const target = document.getElementById(button.dataset.copyTarget);
  const isCommand = target.id === 'install-command';
  const label = document.querySelector(isCommand ? '#install-copy-label' : '#copy-label');
  const status = document.querySelector(isCommand ? '#install-copy-status' : '#copy-status');
  try {
    await navigator.clipboard.writeText(target.textContent);
    if (installView !== copiedView) return;
    label.textContent = isCommand ? 'Copied ✓' : 'COPIED ✓';
    status.textContent = isCommand ? 'Copied. Run it in your project’s terminal.' : `Copied. Paste it into ${copiedHost.name} in your project.`;
  } catch {
    if (installView !== copiedView) return;
    label.textContent = isCommand ? 'Copy' : 'COPY';
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(target);
    selection.removeAllRanges();
    selection.addRange(range);
    status.textContent = isCommand ? 'Command selected. Copy it, then run it in your project’s terminal.' : `Prompt selected. Copy it, then paste it into ${copiedHost.name}.`;
  }
}));

// Keep each explanation close to the control that opened it.
const popovers = [...document.querySelectorAll('.micro-pop')];
const popoverTriggers = new Map();
function positionPopover(popover) {
  const trigger = popoverTriggers.get(popover.id);
  if (!trigger) return;
  const anchor = trigger.getBoundingClientRect();
  const box = popover.getBoundingClientRect();
  const margin = 16;
  const left = Math.max(margin, Math.min(anchor.right - box.width, innerWidth - box.width - margin));
  const below = anchor.bottom + 12;
  const top = below + box.height <= innerHeight - margin ? below : Math.max(margin, anchor.top - box.height - 12);
  Object.assign(popover.style, { left: `${left}px`, top: `${top}px`, right: 'auto', bottom: 'auto' });
}
for (const trigger of document.querySelectorAll('[popovertarget]:not([popovertargetaction])')) {
  trigger.addEventListener('click', () => {
    const id = trigger.getAttribute('popovertarget');
    popoverTriggers.set(id, trigger);
    requestAnimationFrame(() => {
      const popover = document.getElementById(id);
      if (popover?.matches(':popover-open')) positionPopover(popover);
    });
  });
}
addEventListener('resize', () => {
  for (const popover of popovers) if (popover.matches(':popover-open')) positionPopover(popover);
});
addEventListener('scroll', () => {
  for (const popover of popovers) if (popover.matches(':popover-open')) positionPopover(popover);
}, { passive: true });

// Native popovers keep their keyboard behavior; move initial focus to the close
// control so the explanation can be dismissed or read without hunting for it.
popovers.forEach(popover => popover.addEventListener('toggle', event => {
  const trigger = popoverTriggers.get(popover.id);
  if (event.newState === 'open') {
    positionPopover(popover);
    popover.querySelector('.pop-close').focus({ preventScroll: true });
  } else if (popover.contains(document.activeElement)) {
    trigger?.focus({ preventScroll: true });
  }
}));

// Measure the visible provider, rather than reserving space for the longest name.
// Rotation pauses while the reader interacts with the badge or its explanation.
const providerBadge = document.querySelector('.host-badge');
const providerCarousel = providerBadge.querySelector('.host-rotator');
const providers = [...providerCarousel.querySelectorAll('.host')];
const providerMotion = matchMedia('(prefers-reduced-motion: reduce)');
const providerNames = ['codex', 'cursor', 'claude'];
let providerIndex = 0;
let providerTimer;
let providerHovered = false;
let providerPinned = false;
const themeColor = document.querySelector('meta[name=theme-color]');
const themeColors = { codex: '#244bff', cursor: '#1f2023', claude: '#b4532f' };

function fitProvider() {
  const width = `${Math.ceil(providers[providerIndex].getBoundingClientRect().width)}px`;
  if (providerCarousel.style.width !== width) providerCarousel.style.width = width;
}

function showProvider(index) {
  providers.forEach((provider, i) => {
    provider.classList.toggle('is-outgoing', provider.classList.contains('is-current') && i !== index);
    provider.classList.toggle('is-current', i === index);
  });
  providerIndex = index;
  providerBadge.dataset.provider = providerNames[index];
  document.documentElement.dataset.theme = providerNames[index];
  themeColor.content = themeColors[providerNames[index]];
  fitProvider();
}

function scheduleProvider() {
  clearTimeout(providerTimer);
  if (providerPinned || providerMotion.matches || document.hidden || providerHovered || providerBadge.matches(':focus-within') || document.querySelector('#how-pop').matches(':popover-open') || document.querySelector('dialog[open]')) return;
  providerTimer = setTimeout(() => {
    showProvider((providerIndex + 1) % providers.length);
    scheduleProvider();
  }, 3800);
}

fitProvider();
providerCarousel.classList.add('is-enhanced');
showProvider(0);
scheduleProvider();
document.fonts.ready.then(fitProvider);
const providerSizes = new ResizeObserver(fitProvider);
providers.forEach(provider => providerSizes.observe(provider));
providerBadge.addEventListener('pointerenter', event => { if (event.pointerType === 'mouse') { providerHovered = true; scheduleProvider(); } });
providerBadge.addEventListener('pointerleave', () => { providerHovered = false; scheduleProvider(); });
providerBadge.addEventListener('focusin', scheduleProvider);
providerBadge.addEventListener('focusout', () => queueMicrotask(scheduleProvider));
document.querySelector('#how-pop').addEventListener('toggle', scheduleProvider);
document.querySelectorAll('dialog').forEach(dialog => {
  dialog.addEventListener('toggle', scheduleProvider);
  dialog.addEventListener('close', scheduleProvider);
});
document.addEventListener('visibilitychange', scheduleProvider);
providerMotion.addEventListener('change', () => { if (!providerMotion.matches) fitProvider(); scheduleProvider(); });
