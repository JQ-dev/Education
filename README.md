# SABER School Results Dashboard

Interactive Dash application for analyzing Colombian SABER test results across different schools and grades, with machine learning-based performance prediction.

## Features

### 📊 Data Visualization
- **Scatter Plots**: Compare Language vs Mathematics performance by grade
- **Distribution Analysis**: View score distributions for each subject
- **Grade Comparison**: Compare average performance across grades 3, 5, 9, and 11
- **School Search**: Find and analyze specific schools by name

### 🔍 Interactive Filters
- Filter by school gender (Género)
- Filter by school type (Naturaleza: Oficial/No Oficial)
- Filter by school character (Carácter: Académico/Técnico)
- Filter by location (Área: Urbano/Rural)
- Adjustable minimum sample size to ensure data quality

### 🤖 Machine Learning Predictions
- Random Forest model to estimate school performance
- Feature importance analysis showing which school characteristics most impact results
- Interactive prediction tool based on school features

## Data Sources

The app uses SABER test data including:
- **Colegios4.csv**: Standardized test scores (z-scores) for grades 3, 5, 9, and 11
- **Cole_list3.csv**: School metadata including name, type, location, etc.

Subjects covered:
- Lenguaje (Language/Reading Comprehension)
- Matemáticas (Mathematics)

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the Dash app:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://127.0.0.1:8050/
```

3. Use the filters to explore different school segments
4. Switch between tabs to view different visualizations
5. Try the ML prediction tool to estimate performance based on school features

## Dashboard Tabs

### 📈 Lenguaje vs Matemáticas
Interactive scatter plot showing the relationship between Language and Math scores. Points are sized by number of students tested.

### 📊 Distribuciones
Histograms showing the distribution of scores for both subjects in the selected grade.

### 📉 Comparación por Grado
Bar chart comparing average performance across all grade levels.

### 🤖 Predicción ML
Machine learning section with:
- Random Forest model trained on school characteristics
- Feature importance visualization
- Interactive prediction tool

### 🔍 Buscar Colegio
Search functionality to find specific schools and view their complete results.

## Technical Details

- **Framework**: Dash with Bootstrap components
- **ML Model**: Random Forest Regressor (scikit-learn)
- **Visualizations**: Plotly
- **Data Processing**: Pandas

## Performance Notes

- The app filters schools by minimum sample size to ensure statistical reliability
- Scores are standardized (z-scores) for easier comparison
- Missing data is handled automatically in visualizations

## Author

Created for analyzing Colombian SABER educational assessment data.
