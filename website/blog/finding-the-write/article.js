// A controlled browser model of example/. Storage here is in memory, not SQLite.
(() => {
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const lab = document.querySelector('.save-lab');
  const el = id => document.getElementById(`lab-${id}`);
  const rows = [...lab.querySelectorAll('.lab-events li')];
  const sourceButtons = [...lab.querySelectorAll('[data-source]')];
  const scenarioButtons = [...lab.querySelectorAll('[data-scenario]')];
  const storagePane = lab.querySelector('.lab-storage');
  const verdictPane = lab.querySelector('.lab-verdict');
  const timer = lab.querySelector('.lab-timer > span');
  const animations = new Set();
  const scenarios = {
    before: { guard: false, reverse: false, rule: 'Manual save first · revision check off' },
    after: { guard: true, reverse: false, rule: 'Manual save first · revision check on' },
    reverse: { guard: true, reverse: true, rule: 'Autosave first · revision check on' },
  };
  let scenario = 'before';
  let rememberedDraft = 'Finished paragraph';
  let store;
  let editorRevision;
  let pending;
  let requests;
  let conflict = false;
  let finished = false;
  let resolution = null;
  let reviewRow = null;
  let playback = null;
  let frame = 0;
  let visible = true;

  function announce(message) { el('announcement').textContent = message; }
  function animate(element) {
    if (motion.matches || !element.animate) return;
    const animation = element.animate([{ opacity: .4, transform: 'translateY(5px)' }, { opacity: 1, transform: 'translateY(0)' }], { duration: 260, easing: 'ease-out' });
    animations.add(animation);
    animation.finished.catch(() => {}).finally(() => animations.delete(animation));
  }
  function stop() {
    cancelAnimationFrame(frame);
    playback = null;
    animations.forEach(animation => animation.cancel());
    animations.clear();
    lab.dataset.paused = 'false';
  }
  function showSource(name) {
    const guarded = scenarios[scenario].guard;
    const sources = {
      editor: ['editor.py', 'snapshot()', "return {'id': self.document_id, 'body': self.body, 'revision': self.revision}", 'The document ID, text, and loaded revision travel together. A later edit changes the editor, not an existing snapshot.'],
      queue: ['save_queue.py', 'enqueue()', 'self.pending.append(dict(snapshot))', 'The queue keeps a copy. It still carries “Earlier draft” and revision 0, even after your manual save succeeds.'],
      service: ['documents.py', 'save()', "return self.repository.write(payload['id'], payload['body'], payload['revision'])", 'The API passes the payload to the service. The same three values reach the repository; the service does not pick a newer paragraph.'],
      storage: ['storage.py', 'write() · SQL', guarded ? 'UPDATE documents SET body = ?, revision = revision + 1 WHERE id = ? AND revision = ?' : 'UPDATE documents SET body = ?, revision = revision + 1 WHERE id = ?', guarded ? 'The comparison and write are one statement. A stale revision updates no row; SaveConflict becomes a 409 at the API boundary.' : 'Only the ID is checked. Every accepted request replaces the body and advances the stored revision, including an older snapshot.'],
    };
    const [file, method, code, note] = sources[name];
    sourceButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.source === name)));
    el('source-file').textContent = `${file} · ${method} ↗`;
    el('source-file').href = `../../example/${file}`;
    el('source-code').replaceChildren();
    if (name === 'storage' && guarded) {
      const [before, after] = code.split('AND revision = ?');
      const mark = document.createElement('mark'); mark.textContent = 'AND revision = ?';
      el('source-code').append(before, mark, after);
    } else el('source-code').textContent = code;
    el('source-note').textContent = note;
  }
  function renderStore(result = 'neutral') {
    const changed = el('stored-text').textContent !== store.body;
    el('stored-text').textContent = store.body;
    el('stored-revision').textContent = store.revision;
    storagePane.dataset.result = result;
    if (changed) animate(el('stored-text'));
  }
  function setVerdict(label, message, result = 'neutral') {
    el('verdict-label').textContent = label;
    el('verdict').textContent = message;
    verdictPane.dataset.result = result;
  }
  function eventRow(index, state, status) {
    const position = index === 0 ? 'first' : 'second';
    rows[index].dataset.state = state;
    el(`${position}-status`).textContent = status;
    el(`${position}-status`).classList.toggle('conflict', status.startsWith('409'));
  }
  function reset(name = scenario) {
    stop();
    scenario = name;
    store = { id: 1, body: 'Starting text', revision: 0 };
    editorRevision = 0;
    pending = { id: 1, body: 'Earlier draft', revision: 0 };
    conflict = false; finished = false;
    resolution = null;
    reviewRow?.remove(); reviewRow = null;
    lab.dataset.scenario = name; lab.dataset.phase = 'ready';
    scenarioButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.scenario === name)));
    el('rule').textContent = scenarios[name].rule;
    el('draft').value = rememberedDraft;
    el('draft').readOnly = false;
    el('editor-revision').textContent = 0;
    el('editor-note').textContent = 'Make this paragraph yours. The queued copy won’t change.';
    el('save').disabled = false; el('save').innerHTML = 'Save paragraph <span aria-hidden="true">↗</span>';
    el('reload').disabled = true;
    el('play').hidden = true;
    lab.querySelector('.lab-decision').hidden = true;
    el('queue-status').textContent = 'Waiting'; el('queue-status').classList.remove('conflict');
    el('storage-note').textContent = 'This is what a fresh read would return.';
    lab.querySelector('.lab-storage-glyph').textContent = '↙';
    el('phase').textContent = 'Ready when you are';
    timer.style.transform = 'scaleX(0)';
    const first = scenarios[name].reverse ? 'Autosave' : 'Manual save';
    el('first-title').textContent = first;
    el('second-title').textContent = scenarios[name].reverse ? 'Manual save' : 'Delayed autosave';
    el('first-body').textContent = scenarios[name].reverse ? 'Earlier draft · revision 0' : 'Your paragraph · revision 0';
    el('second-body').textContent = scenarios[name].reverse ? 'Your paragraph · revision 0' : 'Earlier draft · revision 0';
    eventRow(0, 'waiting', 'Ready'); eventRow(1, 'waiting', 'Queued');
    renderStore();
    setVerdict('Watch the other writer', 'A “Saved” message describes one write. What happens after it?');
    showSource('editor');
  }
  // Same rule as Repository.write(): compare at the write boundary, then increment.
  function write(snapshot) {
    if (scenarios[scenario].guard && snapshot.revision !== store.revision) return 409;
    store = { id: snapshot.id, body: snapshot.body, revision: store.revision + 1 };
    return 200;
  }
  function acceptRequest(index) {
    const request = requests[index];
    const status = write(request.snapshot);
    request.status = status;
    eventRow(index, 'done', status === 200 ? '200 · Saved' : '409 · Conflict');
    if (request.manual) {
      if (status === 200) {
        editorRevision = store.revision;
        el('editor-revision').textContent = editorRevision;
        el('editor-note').textContent = `Saved at revision ${editorRevision}. Your paragraph is still open.`;
      } else {
        conflict = true;
        el('editor-note').textContent = '409 · Not saved. Your draft is still here; compare it before saving again.';
      }
    } else {
      pending = null;
      el('queue-status').textContent = status === 200 ? '200 · Written' : '409 · Rejected';
      el('queue-status').classList.toggle('conflict', status === 409);
    }
    showSource('storage');
    renderStore(index === 0 ? 'neutral' : scenario === 'before' ? 'overwritten' : conflict ? 'conflict' : 'protected');
  }
  function finalResult() {
    finished = true; lab.dataset.phase = 'complete';
    el('draft').readOnly = !conflict;
    el('reload').disabled = false;
    el('play').hidden = false; el('play').textContent = '↻ Replay';
    el('play').setAttribute('aria-label', 'Replay saves with this paragraph');
    el('save').textContent = conflict ? 'Not saved' : 'Saved ✓';
    el('phase').textContent = 'Both requests finished · try Reload';
    timer.style.transform = 'scaleX(1)';
    if (scenario === 'before') {
      el('storage-note').textContent = 'The older snapshot replaced your saved paragraph.';
      lab.querySelector('.lab-storage-glyph').textContent = '↶';
      const sameText = requests.find(request => request.manual).snapshot.body === store.body;
      setVerdict(sameText ? 'Two successful writes. The same text.' : 'Two successes. One lost edit.', sameText ? 'Both requests carried the same text this time. Revision 2 still shows that the older request was accepted.' : 'Your manual save worked. The older write worked too. Reload to see what comes back.', 'overwritten');
    } else if (conflict) {
      el('storage-note').textContent = 'Autosave got here first. Your local draft is not stored.';
      lab.querySelector('.lab-storage-glyph').textContent = '!';
      setVerdict('Your draft is here. It isn’t saved.', 'The revision check rejected the manual save. Compare your draft with the stored text and make a choice.', 'conflict');
      lab.querySelector('.lab-decision').hidden = false;
    } else {
      el('editor-note').textContent = 'Saved at revision 1. The delayed autosave was rejected.';
      el('storage-note').textContent = 'The revision check kept your accepted save.';
      lab.querySelector('.lab-storage-glyph').textContent = '✓';
      setVerdict('The older write has no permission.', 'Revision 0 no longer matches revision 1. The stale autosave is rejected; your paragraph survives.', 'protected');
    }
    announce(`${el('verdict').textContent} Stored revision ${store.revision}: ${store.body}`);
  }
  function stage(index) {
    if (index === 0 || index === 2) {
      const requestIndex = index === 0 ? 0 : 1;
      const request = requests[requestIndex];
      eventRow(requestIndex, 'writing', 'Writing…');
      el('phase').textContent = request.manual ? 'Your manual save arrives' : 'The queued snapshot arrives';
      if (!request.manual) el('queue-status').textContent = 'Arriving…';
      showSource(request.manual ? 'service' : 'queue');
    } else if (index === 1) {
      acceptRequest(0);
      el('phase').textContent = 'First write accepted · stored revision 1';
      setVerdict('One write is still waiting', 'The first request succeeded. The other request still carries revision 0.');
      announce(`${requests[0].manual ? 'Manual save' : 'Autosave'} succeeded. Stored revision 1. A second request is waiting.`);
    } else if (index === 3) {
      acceptRequest(1);
      finalResult();
    }
  }
  const stageTimes = [0, 650, 1850, 2650];
  function tick(now) {
    if (!playback || playback.paused) return;
    if (playback.last !== null) playback.elapsed += Math.min(100, now - playback.last);
    playback.last = now;
    const nextStage = stageTimes.reduce((current, time, index) => playback.elapsed >= time ? index : current, -1);
    while (playback.stage < nextStage) { playback.stage++; stage(playback.stage); }
    if (finished) { stop(); return; }
    timer.style.transform = `scaleX(${Math.min(1, playback.elapsed / 2650)})`;
    frame = requestAnimationFrame(tick);
  }
  function run() {
    if (!finished) rememberedDraft = el('draft').value;
    reset();
    const manual = { manual: true, snapshot: { id: 1, body: rememberedDraft, revision: editorRevision } };
    const autosave = { manual: false, snapshot: { ...pending } };
    requests = scenarios[scenario].reverse ? [autosave, manual] : [manual, autosave];
    requests.forEach((request, index) => {
      el(`${index === 0 ? 'first' : 'second'}-body`).textContent = `${request.snapshot.body || '(empty paragraph)'} · revision ${request.snapshot.revision}`;
    });
    el('draft').readOnly = true;
    el('save').disabled = true; el('save').textContent = 'Saving…';
    el('play').hidden = motion.matches; el('play').textContent = 'Ⅱ Pause';
    el('play').setAttribute('aria-label', 'Pause save sequence');
    lab.dataset.phase = 'running';
    if (motion.matches) {
      // The same transitions, without timed motion or a forced wait.
      stageTimes.forEach((_, index) => stage(index));
    } else {
      playback = { elapsed: 0, stage: -1, last: null, paused: false, autoPaused: false };
      frame = requestAnimationFrame(tick);
    }
  }
  function pause(paused, automatic = false) {
    if (!playback) return;
    playback.paused = paused; playback.autoPaused = automatic && paused;
    lab.dataset.paused = String(paused);
    el('play').textContent = paused ? '▷ Resume' : 'Ⅱ Pause';
    el('play').setAttribute('aria-label', paused ? 'Resume save sequence' : 'Pause save sequence');
    animations.forEach(animation => paused ? animation.pause() : animation.play());
    cancelAnimationFrame(frame);
    if (!paused) { playback.last = null; frame = requestAnimationFrame(tick); }
    if (!automatic) announce(paused ? 'Sequence paused. No pending write will arrive until you resume.' : 'Sequence resumed.');
  }
  el('draft').addEventListener('input', () => { rememberedDraft = el('draft').value; });
  el('save').addEventListener('click', run);
  el('reset').addEventListener('click', () => { reset(); announce('Fresh document. Your edited paragraph is kept; the earlier snapshot is queued again.'); });
  el('play').addEventListener('click', () => { if (playback) pause(!playback.paused); else run(); });
  scenarioButtons.forEach(button => button.addEventListener('click', () => { reset(button.dataset.scenario); announce(`${scenarios[scenario].rule}. Fresh document; press Save paragraph to compare.`); }));
  sourceButtons.forEach(button => button.addEventListener('click', () => showSource(button.dataset.source)));
  el('reload').addEventListener('click', () => {
    if (!finished) return;
    if (conflict) {
      el('editor-note').textContent = `Reload read revision ${store.revision}. Your unsaved draft is kept here for comparison.`;
      setVerdict('Reload confirms the conflict', 'The stored text is “Earlier draft.” Your paragraph is still local. The revision check does not choose between them.', 'conflict');
    } else {
      el('draft').value = store.body;
      editorRevision = store.revision; el('editor-revision').textContent = editorRevision;
      el('editor-note').textContent = `Reloaded from storage at revision ${editorRevision}. Reset to try another paragraph.`;
      if (resolution === 'draft') {
        setVerdict('Your choice is stored.', `Reload returned the draft you chose at revision ${store.revision}. Your deliberate replacement was saved.`, 'protected');
      } else if (resolution === 'stored') {
        setVerdict('The stored text you chose.', `Reload returned the stored paragraph at revision ${store.revision}. Choosing it made no additional write.`);
      } else if (scenario === 'before') {
        const sameText = requests.find(request => request.manual).snapshot.body === store.body;
        setVerdict(sameText ? 'No text difference this time.' : 'There it is. The old draft.', sameText ? 'Both writes carried the same paragraph. Revision 2 confirms the second write; try different text to see the overwrite.' : 'Reload returned the older text at revision 2. “Saved” was true; it just wasn’t the last write.', 'overwritten');
      } else {
        setVerdict('Your paragraph survived.', `Reload returned your paragraph at revision ${store.revision}. The delayed stale request never changed it.`, 'protected');
      }
      animate(el('draft'));
    }
    el('storage-note').textContent = `Fresh read confirmed · revision ${store.revision}`;
    announce(`${el('verdict').textContent} Stored text: ${store.body}`);
  });
  el('keep').addEventListener('click', () => {
    if (!conflict || playback) return;
    // Explicit replacement after comparing; no automatic retry or merging.
    const reviewedRevision = store.revision;
    editorRevision = reviewedRevision;
    const status = write({ id: 1, body: el('draft').value, revision: editorRevision });
    if (status !== 200) return;
    conflict = false; resolution = 'draft'; rememberedDraft = el('draft').value;
    editorRevision = store.revision; el('editor-revision').textContent = editorRevision;
    el('draft').readOnly = true; el('save').textContent = 'Saved ✓';
    el('editor-note').textContent = `Your choice was saved at revision ${editorRevision}.`;
    lab.querySelector('.lab-decision').hidden = true;
    renderStore('protected'); showSource('storage');
    el('storage-note').textContent = 'Your draft replaced the stored text after review.';
    el('phase').textContent = `Reviewed replacement saved · revision ${store.revision}`;
    reviewRow = document.createElement('li');
    reviewRow.dataset.state = 'done';
    const number = document.createElement('span'); number.className = 'event-number'; number.textContent = '03';
    const description = document.createElement('div');
    const title = document.createElement('strong'); title.textContent = 'Save after your review';
    const body = document.createElement('span'); body.textContent = `${rememberedDraft || '(empty paragraph)'} · revision ${reviewedRevision}`;
    description.append(title, body);
    const saved = document.createElement('span'); saved.className = 'status'; saved.textContent = '200 · Saved';
    reviewRow.append(number, description, saved);
    lab.querySelector('.lab-events').append(reviewRow);
    setVerdict('You chose your draft.', 'After comparing, you saved against the current revision. This deliberate replacement succeeds; nothing was merged.', 'protected');
    announce(`Your draft was saved at revision ${store.revision}. ${store.body}`);
  });
  el('use').addEventListener('click', () => {
    if (!conflict || playback) return;
    conflict = false; resolution = 'stored';
    el('draft').value = store.body;
    editorRevision = store.revision; el('editor-revision').textContent = editorRevision;
    el('draft').readOnly = true;
    el('editor-note').textContent = `You chose the stored text at revision ${editorRevision}.`;
    el('save').textContent = 'Stored text loaded';
    el('phase').textContent = `Stored revision ${store.revision} loaded · no new write`;
    lab.querySelector('.lab-decision').hidden = true;
    setVerdict('You chose the stored text.', 'Your editor now shows the stored paragraph. No new write was made. Reset to try your draft again.');
    announce(`Stored text loaded at revision ${store.revision}. No new write was made.`);
  });
  document.querySelectorAll('[data-try-scenario]').forEach(link => link.addEventListener('click', () => {
    reset(link.dataset.tryScenario);
    el('draft').focus({ preventScroll: true });
    announce(`${scenarios[scenario].rule}. Press Save paragraph to run this scenario.`);
  }));
  if ('IntersectionObserver' in window) new IntersectionObserver(entries => {
    visible = entries[0].isIntersecting;
    if (!visible && playback && !playback.paused) pause(true, true);
    else if (visible && playback?.autoPaused && !document.hidden) pause(false);
  }).observe(lab);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden && playback && !playback.paused) pause(true, true);
    else if (!document.hidden && visible && playback?.autoPaused) pause(false);
  });
  motion.addEventListener('change', () => {
    if (motion.matches && playback) {
      const currentStage = playback.stage;
      stop();
      for (let index = currentStage + 1; index < stageTimes.length; index++) stage(index);
    }
  });
  reset();
  // The source stays available without making the mobile experiment a long form.
  if (matchMedia('(max-width: 700px)').matches) lab.querySelector('.lab-source').open = false;

  const heroScene = document.querySelector('.hero-scene');
  function playHero() {
    heroScene.classList.remove('is-playing');
    if (motion.matches) return;
    void heroScene.offsetWidth;
    heroScene.classList.add('is-playing');
  }
  document.querySelector('.hero-replay').addEventListener('click', playHero);
  playHero();
  motion.addEventListener('change', () => { if (motion.matches) heroScene.classList.remove('is-playing'); });

  const chapterNav = document.querySelector('.chapter-nav');
  const article = document.getElementById('article');
  const links = [...chapterNav.querySelectorAll('a')];
  const headings = links.map(link => document.querySelector(link.getAttribute('href')));
  let chapterFrame = 0;
  function updateChapters() {
    chapterFrame = 0;
    const rect = article.getBoundingClientRect();
    chapterNav.dataset.visible = String(rect.top < 180 && rect.bottom > innerHeight * .35);
    let current = 0;
    headings.forEach((heading, index) => { if (heading.getBoundingClientRect().top <= innerHeight * .27) current = index; });
    links.forEach((link, index) => { if (index === current) link.setAttribute('aria-current', 'location'); else link.removeAttribute('aria-current'); });
    const progress = Math.max(0, Math.min(1, (180 - rect.top) / (rect.height - innerHeight * .35)));
    chapterNav.querySelector('.chapter-progress > span').style.transform = `scaleX(${progress})`;
  }
  function requestChapterUpdate() { if (!chapterFrame) chapterFrame = requestAnimationFrame(updateChapters); }
  addEventListener('scroll', requestChapterUpdate, { passive: true });
  addEventListener('resize', requestChapterUpdate);
  updateChapters();
})();
