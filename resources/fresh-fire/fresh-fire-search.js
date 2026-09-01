/**
 * Fresh Fire Search — client-side index and filter
 * Loads entry data from fresh-fire-data.json and provides live search.
 */
(function() {
  const searchInput = document.getElementById('ff-search-input');
  const resultsContainer = document.getElementById('ff-results');
  const resultsCount = document.getElementById('ff-count');
  const emptyState = document.getElementById('ff-empty');

  if (!searchInput) return;

  // Load entry data
  let FRESH_FIRE_ENTRIES = [];
  fetch('/resources/fresh-fire/fresh-fire-data.json')
    .then(r => r.json())
    .then(data => {
      FRESH_FIRE_ENTRIES = data;
      renderResults('');
    })
    .catch(() => {
      // data unavailable — search stays empty
    });

  function renderResults(query) {
    const q = query.toLowerCase().trim();

    let filtered;
    if (!q) {
      filtered = FRESH_FIRE_ENTRIES.slice();
    } else {
      filtered = FRESH_FIRE_ENTRIES.filter(e =>
        e.title.toLowerCase().includes(q) ||
        e.excerpt.toLowerCase().includes(q) ||
        (e.tags && e.tags.some(t => t.toLowerCase().includes(q)))
      );
    }

    if (resultsCount) {
      resultsCount.textContent = `${filtered.length} entr${filtered.length === 1 ? 'y' : 'ies'}`;
    }

    if (filtered.length === 0) {
      resultsContainer.innerHTML = '';
      if (emptyState) emptyState.style.display = 'block';
      return;
    }
    if (emptyState) emptyState.style.display = 'none';

    let html = '';
    filtered.forEach(e => {
      html += `
        <a href="/resources/fresh-fire/${e.slug}" class="ff-result-card">
          <div class="ff-result-body">
            <h4 class="ff-result-title">${e.title}</h4>
            <p class="ff-result-excerpt">${e.excerpt}</p>
            ${e.tags && e.tags.length ? `<div class="ff-tags">${e.tags.map(t => `<span class="ff-tag">${t}</span>`).join('')}</div>` : ''}
          </div>
        </a>
      `;
    });
    resultsContainer.innerHTML = html;
  }

  searchInput.addEventListener('input', () => renderResults(searchInput.value));

  // initial render — data may not be loaded yet
  renderResults('');
})();