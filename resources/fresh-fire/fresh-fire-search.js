/**
 * Fresh Fire Search — client-side index and filter
 * Add entries to FRESH_FIRE_ENTRIES as content is supplied.
 * Each entry: { slug, title, date, excerpt, tags[], month, year }
 */
const FRESH_FIRE_ENTRIES = [];

(function() {
  const searchInput = document.getElementById('ff-search-input');
  const resultsContainer = document.getElementById('ff-results');
  const resultsCount = document.getElementById('ff-count');
  const emptyState = document.getElementById('ff-empty');

  if (!searchInput) return;

  function renderResults(query) {
    const q = query.toLowerCase().trim();

    let filtered;
    if (!q) {
      // show all, grouped by month
      filtered = FRESH_FIRE_ENTRIES.slice();
    } else {
      filtered = FRESH_FIRE_ENTRIES.filter(e =>
        e.title.toLowerCase().includes(q) ||
        e.excerpt.toLowerCase().includes(q) ||
        (e.tags && e.tags.some(t => t.toLowerCase().includes(q))) ||
        (e.month && e.month.toLowerCase().includes(q))
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

    // Group by month/year
    const groups = {};
    filtered.forEach(e => {
      const key = e.month ? `${e.month} ${e.year || ''}` : 'Other';
      if (!groups[key]) groups[key] = [];
      groups[key].push(e);
    });

    let html = '';
    for (const [group, entries] of Object.entries(groups)) {
      if (group !== 'Other') {
        html += `<div class="ff-group-label">${group}</div>`;
      }
      entries.forEach(e => {
        const dateStr = e.date ? `<span class="ff-date">${e.date}</span>` : '';
        html += `
          <a href="/resources/fresh-fire/${e.slug}" class="ff-result-card">
            <div class="ff-result-body">
              <h4 class="ff-result-title">${e.title}</h4>
              ${dateStr}
              <p class="ff-result-excerpt">${e.excerpt}</p>
              ${e.tags && e.tags.length ? `<div class="ff-tags">${e.tags.map(t => `<span class="ff-tag">${t}</span>`).join('')}</div>` : ''}
            </div>
          </a>
        `;
      });
    }
    resultsContainer.innerHTML = html;
  }

  searchInput.addEventListener('input', () => renderResults(searchInput.value));

  // initial render
  renderResults('');
})();