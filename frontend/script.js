const form = document.getElementById('prediction-form');
const result = document.getElementById('result');
const accuracyResult = document.getElementById('accuracy-result');
const checkAccuracyButton = document.getElementById('check-accuracy-btn');
const filterForm = document.getElementById('filter-form');
const citySelect = document.getElementById('filter-city');
const branchSelect = document.getElementById('filter-branch');
const instituteSelect = document.getElementById('filter-institute');
const boysHostelSelect = document.getElementById('filter-boys-hostel');
const girlsHostelSelect = document.getElementById('filter-girls-hostel');
const filterResults = document.getElementById('filter-results');
const prevPageButton = document.getElementById('prev-page');
const nextPageButton = document.getElementById('next-page');
const pageInfo = document.getElementById('page-info');
const pageSizeSelect = document.getElementById('page-size-select');
const predictionEmpty = document.getElementById('prediction-empty');
const resultBadge = document.getElementById('result-badge');
const accuracyProgressFill = document.getElementById('accuracy-progress-fill');
const accuracyPercentage = document.getElementById('accuracy-percentage');

const DEFAULT_PAGE_SIZE = '10';
let currentPage = 1;
let totalPages = 1;
let currentPageSize = DEFAULT_PAGE_SIZE;
let activeFilters = {};
let isFetchingPage = false;
let lastFilterKey = '';
const institutePageCache = new Map();

function setPredictionState(message, isSuccess = false) {
  result.textContent = message;
  if (predictionEmpty) {
    predictionEmpty.style.display = isSuccess ? 'none' : 'block';
  }
  if (resultBadge) {
    resultBadge.textContent = isSuccess ? 'Prediction Ready' : 'Awaiting Input';
    resultBadge.classList.toggle('success', isSuccess);
  }
}

function setAccuracyProgress(percentValue) {
  const clamped = Number.isFinite(percentValue)
    ? Math.min(Math.max(percentValue, 0), 100)
    : 0;

  if (accuracyProgressFill) {
    accuracyProgressFill.style.width = `${clamped}%`;
  }
  if (accuracyPercentage) {
    accuracyPercentage.textContent = `${clamped.toFixed(1)}%`;
  }
}

function getFilterCacheKey(filters) {
  return JSON.stringify(Object.keys(filters).sort().reduce((acc, key) => {
    acc[key] = filters[key];
    return acc;
  }, {}));
}

function setPaginationLoadingState(loading) {
  isFetchingPage = loading;
  const isAllMode = currentPageSize === 'all';
  prevPageButton.disabled = loading || isAllMode || currentPage <= 1;
  nextPageButton.disabled = loading || isAllMode || currentPage >= totalPages;
  if (loading) {
    pageInfo.textContent = isAllMode ? 'Loading all results...' : `Loading page ${currentPage}...`;
  } else {
    pageInfo.textContent = isAllMode
      ? `Showing all results (${totalPages === 1 ? 'all available rows' : 'filtered rows'})`
      : `Page ${currentPage} of ${totalPages}`;
  }
}

function updatePaginationControls() {
  const isAllMode = currentPageSize === 'all';
  prevPageButton.disabled = isFetchingPage || isAllMode || currentPage <= 1;
  nextPageButton.disabled = isFetchingPage || isAllMode || currentPage >= totalPages;
  if (!isFetchingPage) {
    pageInfo.textContent = isAllMode
      ? 'Showing all results'
      : `Page ${currentPage} of ${totalPages}`;
  }
}

async function prefetchAdjacentPages() {
  const pagesToPrefetch = [currentPage + 1, currentPage - 1].filter(
    (page) => page >= 1 && page <= totalPages
  );

  for (const page of pagesToPrefetch) {
    const cacheKey = `${lastFilterKey}|${page}`;
    if (institutePageCache.has(cacheKey)) {
      continue;
    }

    const params = new URLSearchParams();
    Object.entries(activeFilters).forEach(([key, value]) => {
      params.set(key, value);
    });
    params.set('limit', currentPageSize);
    params.set('page', String(page));

    try {
      const response = await fetch(`/api/filter?${params.toString()}`);
      if (!response.ok) {
        continue;
      }
      const data = await response.json();
      institutePageCache.set(cacheKey, data);
    } catch (error) {
      continue;
    }
  }
}

async function loadFilterOptions() {
  const response = await fetch('/api/options');
  const data = await response.json();

  if (Array.isArray(data.categories)) {
    const categorySelect = document.getElementById('category');
    categorySelect.innerHTML = '<option value="">Auto</option>';
    [...new Set(data.categories)].forEach((category) => {
      const option = document.createElement('option');
      option.value = category;
      option.textContent = category;
      categorySelect.appendChild(option);
    });
  }

  if (Array.isArray(data.quotas)) {
    const quotaSelect = document.getElementById('quota');
    quotaSelect.innerHTML = '<option value="">Auto</option>';
    [...new Set(data.quotas)].forEach((quota) => {
      const option = document.createElement('option');
      option.value = quota;
      option.textContent = quota;
      quotaSelect.appendChild(option);
    });
  }

  boysHostelSelect.innerHTML = `
    <option value="">All</option>
    <option value="Yes">Yes</option>
    <option value="No">No</option>
  `;

  girlsHostelSelect.innerHTML = `
    <option value="">All</option>
    <option value="Yes">Yes</option>
    <option value="No">No</option>
  `;

  data.cities.forEach((city) => {
    const option = document.createElement('option');
    option.value = city;
    option.textContent = city;
    citySelect.appendChild(option);
  });

  data.branches.forEach((branch) => {
    const option = document.createElement('option');
    option.value = branch;
    option.textContent = branch;
    branchSelect.appendChild(option);
  });

  data.institutes.forEach((institute) => {
    const option = document.createElement('option');
    option.value = institute;
    option.textContent = institute;
    instituteSelect.appendChild(option);
  });
}

function renderResults(rows, page = 1, pageSize = 1) {
  if (!rows.length) {
    filterResults.innerHTML = '<tr><td colspan="4">No matching institutes found.</td></tr>';
    return;
  }

  const startNo = (page - 1) * pageSize;
  filterResults.innerHTML = rows
    .map((row, index) => `
      <tr>
        <td>${startNo + index + 1}</td>
        <td>${row.institute_name ?? ''}</td>
        <td>${row.city ?? ''}</td>
        <td>${row.official_website ? `<a href="${row.official_website}" target="_blank" rel="noreferrer">Visit</a>` : ''}</td>
      </tr>
    `)
    .join('');
}

function collectFilters() {
  const branch = branchSelect.value;
  const city = citySelect.value;
  const institute = instituteSelect.value;
  const boysHostel = boysHostelSelect.value;
  const girlsHostel = girlsHostelSelect.value;

  const filters = {};
  if (city) filters.city = city;
  if (branch) filters.branch = branch;
  if (institute) filters.institute_name = institute;
  if (boysHostel) filters.boys_hostel = boysHostel;
  if (girlsHostel) filters.girls_hostel = girlsHostel;
  return filters;
}

async function fetchInstitutePage(page = 1) {
  const filterKey = getFilterCacheKey(activeFilters);
  const combinedKey = `${filterKey}|size:${currentPageSize}`;
  if (combinedKey !== lastFilterKey) {
    institutePageCache.clear();
    lastFilterKey = combinedKey;
  }

  const cacheKey = `${combinedKey}|${page}`;
  const cached = institutePageCache.get(cacheKey);
  if (cached) {
    currentPage = Number(cached.page || page);
    totalPages = Number(cached.total_pages || 1);
    currentPageSize = String(cached.show_all ? 'all' : cached.page_size || currentPageSize);
    pageSizeSelect.value = currentPageSize;
    renderResults(cached.results || [], currentPage, cached.show_all ? Math.max((cached.results || []).length, 1) : Number(cached.page_size || 10));
    updatePaginationControls();
    void prefetchAdjacentPages();
    return;
  }

  setPaginationLoadingState(true);
  const params = new URLSearchParams();
  Object.entries(activeFilters).forEach(([key, value]) => {
    params.set(key, value);
  });
  params.set('limit', currentPageSize);
  params.set('page', String(page));

  try {
    const response = await fetch(`/api/filter?${params.toString()}`);
    const data = await response.json();

    currentPage = Number(data.page || page);
    totalPages = Number(data.total_pages || 1);
    currentPageSize = String(data.show_all ? 'all' : data.page_size || currentPageSize);
    pageSizeSelect.value = currentPageSize;
    institutePageCache.set(`${combinedKey}|${currentPage}`, data);

    renderResults(data.results || [], currentPage, data.show_all ? Math.max((data.results || []).length, 1) : Number(data.page_size || 10));
    updatePaginationControls();
    void prefetchAdjacentPages();
  } catch (error) {
    filterResults.innerHTML = '<tr><td colspan="4">Unable to fetch institutes right now.</td></tr>';
    pageInfo.textContent = 'Load failed';
  } finally {
    setPaginationLoadingState(false);
    updatePaginationControls();
  }
}

async function searchInstitutes(event) {
  event.preventDefault();
  activeFilters = collectFilters();
  institutePageCache.clear();
  currentPage = 1;
  await fetchInstitutePage(currentPage);
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const payload = {
    rank: document.getElementById('rank').value,
    category: document.getElementById('category').value || null,
    quota: document.getElementById('quota').value || null,
  };

  try {
    setPredictionState('Predicting...', false);

    const response = await fetch('/predict', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      setPredictionState(data.error || 'Prediction failed.', false);
      return;
    }

    setPredictionState(data.predicted_field || 'Prediction completed.', true);
  } catch (error) {
    setPredictionState('Unable to connect to the backend.', false);
  }
});

checkAccuracyButton.addEventListener('click', async () => {
  const payload = {
    rank: document.getElementById('rank').value,
    category: document.getElementById('category').value || null,
    quota: document.getElementById('quota').value || null,
  };

  try {
    accuracyResult.textContent = 'Checking accuracy...';
    setAccuracyProgress(0);

    const response = await fetch('/predict/check', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      accuracyResult.textContent = data.error || 'Accuracy check failed.';
      setAccuracyProgress(0);
      return;
    }

    const estimatedInputAccuracy = typeof data.estimated_input_accuracy === 'number'
      ? `${(data.estimated_input_accuracy * 100).toFixed(2)}%`
      : 'N/A';
    const estimatedInputAccuracyValue = typeof data.estimated_input_accuracy === 'number'
      ? data.estimated_input_accuracy * 100
      : 0;
    const modelAccuracy = typeof data.model_training_accuracy === 'number'
      ? `${(data.model_training_accuracy * 100).toFixed(2)}%`
      : 'N/A';

    accuracyResult.textContent =
      `Predicted: ${data.predicted_field} | Estimated Input Accuracy: ${estimatedInputAccuracy} (similar rows: ${data.similar_rows_used}, rank window: +/-${data.rank_window}) | Model Accuracy: ${modelAccuracy} (${data.evaluated_samples} samples)`;
    setAccuracyProgress(estimatedInputAccuracyValue);
  } catch (error) {
    accuracyResult.textContent = 'Unable to connect to the backend.';
    setAccuracyProgress(0);
  }
});

filterForm.addEventListener('submit', searchInstitutes);

pageSizeSelect.addEventListener('change', async () => {
  currentPageSize = pageSizeSelect.value;
  institutePageCache.clear();
  currentPage = 1;
  await fetchInstitutePage(1);
});

prevPageButton.addEventListener('click', async () => {
  if (!isFetchingPage && currentPage > 1) {
    await fetchInstitutePage(currentPage - 1);
  }
});

nextPageButton.addEventListener('click', async () => {
  if (!isFetchingPage && currentPage < totalPages) {
    await fetchInstitutePage(currentPage + 1);
  }
});

loadFilterOptions()
  .then(() => {
    setPredictionState('No prediction yet.', false);
    setAccuracyProgress(0);
    activeFilters = collectFilters();
    currentPageSize = pageSizeSelect.value || DEFAULT_PAGE_SIZE;
    return fetchInstitutePage(1);
  })
  .catch(() => {
    citySelect.innerHTML = '<option value="">Unable to load cities</option>';
    branchSelect.innerHTML = '<option value="">Unable to load branches</option>';
    instituteSelect.innerHTML = '<option value="">Unable to load institutes</option>';
  });