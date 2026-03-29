const form = document.getElementById('prediction-form');
const result = document.getElementById('result');

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const payload = {
    rank: document.getElementById('rank').value,
    category: document.getElementById('category').value,
    quota: document.getElementById('quota').value,
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