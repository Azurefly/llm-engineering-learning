(() => {
  const clock = document.getElementById('report-clock');
  const fullscreen = document.getElementById('fullscreen-toggle');

  function updateClock() {
    if (!clock) return;
    const now = new Date();
    clock.textContent = new Intl.DateTimeFormat(undefined, {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    }).format(now);
  }

  updateClock();
  setInterval(updateClock, 1000);

  if (fullscreen) {
    fullscreen.addEventListener('click', async () => {
      try {
        if (!document.fullscreenElement) {
          await document.documentElement.requestFullscreen();
        } else {
          await document.exitFullscreen();
        }
      } catch (_) {
        // Fullscreen is optional; the report remains usable without it.
      }
    });
  }

  setTimeout(() => window.location.reload(), 60000);
})();
