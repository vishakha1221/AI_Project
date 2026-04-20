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

const PAGE_SIZE = 10;
let currentPage = 1;
let totalPages = 1;
let activeFilters = {};

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

function renderResults(rows, page = 1, pageSize = PAGE_SIZE) {
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
  const params = new URLSearchParams();
  Object.entries(activeFilters).forEach(([key, value]) => {
    params.set(key, value);
  });
  params.set('limit', String(PAGE_SIZE));
  params.set('page', String(page));

  const response = await fetch(`/api/filter?${params.toString()}`);
  const data = await response.json();

  currentPage = Number(data.page || page);
  totalPages = Number(data.total_pages || 1);

  renderResults(data.results || [], currentPage, PAGE_SIZE);
  pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
  prevPageButton.disabled = currentPage <= 1;
  nextPageButton.disabled = currentPage >= totalPages;
}

async function searchInstitutes(event) {
  event.preventDefault();
  activeFilters = collectFilters();
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
    result.textContent = 'Predicting...';

    const response = await fetch('/predict', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      result.textContent = data.error || 'Prediction failed.';
      return;
    }

    result.textContent = data.predicted_field;
  } catch (error) {
    result.textContent = 'Unable to connect to the backend.';
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
      return;
    }

    const estimatedInputAccuracy = typeof data.estimated_input_accuracy === 'number'
      ? `${(data.estimated_input_accuracy * 100).toFixed(2)}%`
      : 'N/A';
    const modelAccuracy = typeof data.model_training_accuracy === 'number'
      ? `${(data.model_training_accuracy * 100).toFixed(2)}%`
      : 'N/A';

    accuracyResult.textContent =
      `Predicted: ${data.predicted_field} | Estimated Input Accuracy: ${estimatedInputAccuracy} (similar rows: ${data.similar_rows_used}, rank window: +/-${data.rank_window}) | Model Accuracy: ${modelAccuracy} (${data.evaluated_samples} samples)`;
  } catch (error) {
    accuracyResult.textContent = 'Unable to connect to the backend.';
  }
});

filterForm.addEventListener('submit', searchInstitutes);

prevPageButton.addEventListener('click', async () => {
  if (currentPage > 1) {
    await fetchInstitutePage(currentPage - 1);
  }
});

nextPageButton.addEventListener('click', async () => {
  if (currentPage < totalPages) {
    await fetchInstitutePage(currentPage + 1);
  }
});

loadFilterOptions()
  .then(() => {
    activeFilters = collectFilters();
    return fetchInstitutePage(1);
  })
  .catch(() => {
    citySelect.innerHTML = '<option value="">Unable to load cities</option>';
    branchSelect.innerHTML = '<option value="">Unable to load branches</option>';
    instituteSelect.innerHTML = '<option value="">Unable to load institutes</option>';
  });