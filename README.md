# Admission Field Prediction System

This project is a simple Flask + frontend starter for an AI-based Admission Field Prediction System.

The current version includes a trained machine learning model for admission field prediction, an institute master extracted from the PDF, and a frontend that can search institutes by branch and hostel availability.

## Project Structure

- `data/` - placeholder for datasets
- `data/institute_master.csv` - institute list extracted from the PDF with hostel and website fields
- `data/acpc_admission_enriched.csv` - admissions data merged with institute details
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

The app will send the form data to `POST /predict` and display the predicted admission field:

The backend expects:

- `rank`
- `category`
- `quota`

The page also includes an institute search panel where you can filter by branch, institute name, and hostel availability.

## Future Work

The model can be improved later with more features, hyperparameter tuning, and better preprocessing.
# AI_Project
AI Project 
