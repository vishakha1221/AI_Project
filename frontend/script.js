const form = document.getElementById('prediction-form');
const result = document.getElementById('result');
const filterForm = document.getElementById('filter-form');
const citySelect = document.getElementById('filter-city');
const branchSelect = document.getElementById('filter-branch');
const instituteSelect = document.getElementById('filter-institute');
const hostelSelect = document.getElementById('filter-hostel');
const filterResults = document.getElementById('filter-results');

async function loadFilterOptions() {
  const response = await fetch('/api/options');
  const data = await response.json();

  if (Array.isArray(data.categories)) {
    const categorySelect = document.getElementById('category');
    data.categories.forEach((category) => {
      const option = document.createElement('option');
      option.value = category;
      option.textContent = category;
      categorySelect.appendChild(option);
    });
  }

  if (Array.isArray(data.quotas)) {
    const quotaSelect = document.getElementById('quota');
    data.quotas.forEach((quota) => {
      const option = document.createElement('option');
      option.value = quota;
      option.textContent = quota;
      quotaSelect.appendChild(option);
    });
  }

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

function renderResults(rows) {
  if (!rows.length) {
    filterResults.innerHTML = '<tr><td colspan="5">No matching institutes found.</td></tr>';
    return;
  }

  filterResults.innerHTML = rows
    .map((row) => `
      <tr>
        <td>${row.institute_name ?? ''}</td>
        <td>${row.course_name ?? ''}</td>
        <td>${row.city ?? ''}</td>
        <td>${row.hostel_available ?? ''}</td>
        <td>${row.official_website ? `<a href="${row.official_website}" target="_blank" rel="noreferrer">Visit</a>` : ''}</td>
      </tr>
    `)
    .join('');
}

async function searchInstitutes(event) {
  event.preventDefault();

  const branch = branchSelect.value;
  const city = citySelect.value;
  const institute = instituteSelect.value;
  const hostel = hostelSelect.value;

  const params = new URLSearchParams();
  if (city) params.set('city', city);
  if (branch) params.set('branch', branch);
  if (institute) params.set('institute_name', institute);
  if (hostel) params.set('hostel_available', hostel);

  const response = await fetch(`/api/filter?${params.toString()}`);
  const data = await response.json();
  renderResults(data.results || []);
}

loadFilterOptions().catch(() => {
  citySelect.innerHTML = '<option value="">Unable to load cities</option>';
  branchSelect.innerHTML = '<option value="">Unable to load branches</option>';
  instituteSelect.innerHTML = '<option value="">Unable to load institutes</option>';
});

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

filterForm.addEventListener('submit', searchInstitutes);