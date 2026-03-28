# Admission Field Prediction System

This project is a simple Flask + frontend starter for an AI-based Admission Field Prediction System.

ML logic is not included yet. The current version only provides a working frontend-backend demo flow that returns a dummy prediction.

## Project Structure

- `data/` - placeholder for datasets
- `model/` - placeholder for saved model files
- `backend/` - Flask backend code
- `frontend/` - simple HTML, CSS, and JavaScript user interface
- `notebook/` - placeholder for future model training code
- `requirements.txt` - Python dependencies

## How To Run

1. Install Python dependencies:

	```bash
	pip install -r requirements.txt
	```

2. Start the Flask server:

	```bash
	python backend/app.py
	```

3. Open your browser and visit:

	```
	http://127.0.0.1:5000/
	```

4. Fill in the form and click Predict.

The app will send the form data to `POST /predict` and display the demo response:

```json
{
  "predicted_field": "Demo Result"
}
```

## Future Work

The machine learning model, preprocessing, and dataset handling will be added later.
# AI_Project
AI Project 
