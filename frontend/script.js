const form = document.getElementById('prediction-form');
const result = document.getElementById('result');

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const payload = {
    rank: document.getElementById('rank').value,
    gujcet_score: document.getElementById('gujcet_score').value,
    percentile: document.getElementById('percentile').value,
    category: document.getElementById('category').value,
    gender: document.getElementById('gender').value,
    quota: document.getElementById('quota').value,
  };

  try {
    const response = await fetch('http://127.0.0.1:5000/predict', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    result.textContent = data.predicted_field;
  } catch (error) {
    result.textContent = 'Unable to connect to the backend.';
  }
});