# SABER Educational Results Dashboard - Government Analytics Platform

**Comprehensive educational performance analysis system designed for Colombian governmental agencies**

## Executive Summary

This enhanced Dash application provides multi-level analysis of SABER test results, enabling governmental decision-makers to:

1. **Identify performance gaps** across departments, municipalities, and schools
2. **Understand socioeconomic impacts** on educational outcomes
3. **Discover truly excellent schools** using value-added analysis that controls for demographic factors
4. **Make data-driven policy decisions** based on comprehensive educational analytics

## Key Features

### 1. 📊 National Overview Tab
**Purpose**: High-level view of national educational performance

**Features**:
- Filter by grade level (3, 5, 9, 11)
- Filter by school type (Official/Private)
- Filter by area (Urban/Rural)
- Summary statistics (total schools, students, average scores)
- Language vs Mathematics performance scatter plot
- Score distribution histograms
- Grade-level comparison charts

**Use Cases**:
- Monitor national educational trends
- Compare performance across different school types
- Identify urban-rural achievement gaps
- Track progress across grade levels

---

### 2. 🗺️ Department Analysis Tab
**Purpose**: Regional performance analysis and inter-municipality comparisons

**Features**:
- Select any of Colombia's 32 departments
- View department-level statistics
- Municipality ranking within department
- Performance visualization maps
- School type comparisons

**Key Metrics**:
- Total municipalities in department
- Total schools analyzed
- Department average scores (Language & Math)
- Top 20 performing municipalities

**Use Cases**:
- Regional education planning
- Resource allocation across municipalities
- Identify best-performing regions for benchmarking
- Department-level policy evaluation

---

### 3. 🏘️ Municipality Analysis Tab
**Purpose**: Detailed municipality-level insights and school performance

**Features**:
- Two-level selection (Department → Municipality)
- Municipality-specific statistics
- Top 15 schools ranking
- Performance distribution analysis
- School type breakdown

**Key Metrics**:
- Total schools in municipality
- Total students evaluated
- Municipality average scores
- School performance rankings

**Use Cases**:
- Municipal education planning
- Identify schools needing intervention
- Recognize top-performing schools
- Local policy development

---

### 4. 🏫 School Analysis Tab
**Purpose**: Individual school performance profiles

**Features**:
- Search schools by name (fuzzy search)
- Detailed school information
- Performance across all grades
- Comprehensive school profile

**Information Displayed**:
- School code (DANE)
- Name and location
- School characteristics (gender, type, area)
- Performance scores across grades 3, 5, 9, 11

**Use Cases**:
- School-specific analysis
- Parent/community information
- Targeted school interventions
- Success story identification

---

### 5. 💰 Socioeconomic Analysis Tab
**Purpose**: Understand how socioeconomic factors impact educational outcomes

**Analysis Types**:

#### a) Parent Education Impact
- Analyzes correlation between parental education and student scores
- Separate analysis for mother's and father's education
- Visualizes achievement gaps by education level

#### b) Socioeconomic Stratum (Estrato)
- Performance analysis across Colombia's 6 socioeconomic strata
- Average scores by stratum
- Distribution visualization
- Key indicator for policy targeting

#### c) Home Assets & Resources
- Impact of technology access (internet, computer)
- Correlation with educational outcomes
- Resource availability analysis

#### d) Family Economic Situation
- Student performance by family economic status
- Identifies economically disadvantaged groups
- Informs social support programs

#### e) Comprehensive Socioeconomic Index (INSE)
- Uses official INSE scores
- Scatter plots showing score vs socioeconomic level
- Trendline analysis
- Most comprehensive socioeconomic indicator

**Use Cases**:
- Target support programs to disadvantaged groups
- Evaluate impact of socioeconomic interventions
- Design equity-focused policies
- Resource allocation based on need

---

### 6. 🤖 Advanced Analytics Tab
**Purpose**: Value-added analysis to identify schools exceeding or underperforming expectations

This is the **most important tab for identifying truly excellent schools**.

#### What is Value-Added Analysis?

Traditional school rankings simply show which schools have the highest scores. However, high scores often reflect advantaged student populations rather than school quality.

**Value-added analysis** controls for:
- Socioeconomic status (INSE, estrato)
- Parental education
- Home resources (internet, computer, etc.)
- School location (urban/rural)
- School type and characteristics

#### How It Works

1. **Build Prediction Model**: Uses machine learning (Random Forest/Gradient Boosting) to predict expected scores based on demographic factors

2. **Calculate Residuals**: Compares actual performance to predicted performance
   - **Positive residual** = School performs BETTER than expected (high value-added)
   - **Negative residual** = School performs WORSE than expected (low value-added)

3. **Identify True Excellence**: Schools with high positive residuals are truly excellent, as they achieve results beyond what demographics would predict

#### Two Analysis Levels

**Student-Level Analysis**:
- Uses individual student data from Saber 11
- Controls for family education, estrato, assets, gender
- More granular and accurate
- Identifies schools adding maximum value to students

**School-Level Analysis**:
- Uses aggregated school data
- Controls for school characteristics
- Faster computation
- Good for high-level screening

#### Key Outputs

1. **Model Performance Metrics**:
   - R² Score: How well demographics explain performance
   - MAE (Mean Absolute Error): Average prediction error
   - RMSE: Prediction accuracy measure

2. **Feature Importance Chart**:
   - Shows which factors most impact student performance
   - Helps prioritize policy interventions

3. **Value-Added Scatter Plot**:
   - X-axis: Predicted score (based on demographics)
   - Y-axis: Actual score
   - Points above diagonal: Exceeding expectations
   - Points below diagonal: Below expectations

4. **Top Schools Table**:
   - Schools with highest positive residuals
   - **These are the truly excellent schools**
   - Should be studied for best practices

5. **Underperforming Schools Table**:
   - Schools with lowest (most negative) residuals
   - Need intervention and support
   - Priority targets for improvement programs

#### Use Cases

1. **Identify Best Practices**: Study high value-added schools to understand what makes them successful

2. **Fair School Evaluation**: Evaluate schools based on value added, not raw scores

3. **Target Interventions**: Focus support on schools underperforming given their context

4. **Policy Development**: Design programs based on what actually works (feature importance)

5. **Resource Allocation**: Reward schools that achieve excellence despite challenges

---

## Data Sources

### Primary Datasets

1. **Colegios4.csv** (16,632 schools)
   - Aggregated test scores by grade (3, 5, 9, 11)
   - Z-scores for Language and Mathematics
   - Number of students tested per grade

2. **Cole_list3.csv** (10,745 schools)
   - School metadata
   - DANE codes, names, locations
   - School characteristics (gender, type, area)

3. **Municipios3.csv** (1,112 municipalities)
   - Municipality-level aggregated scores
   - All grades and subjects

4. **Muni_list_proper2.csv**
   - Municipality names and department mapping
   - 1,015 municipalities across 32 departments

5. **Saber_11__2017-1.csv** (Student-level data)
   - Individual student records
   - 86 columns including:
     - Test scores (Math, Reading, Natural Sciences, Social Sciences, English, Global)
     - Demographics (gender, ethnicity, age)
     - Family education (mother, father)
     - Socioeconomic indicators:
       - Estrato (1-6 scale)
       - INSE (Individual Socioeconomic Index)
       - NSE (Socioeconomic Level)
     - Home assets (internet, computer, car, books, appliances)
     - Family work status
     - Economic situation
     - Student study/work hours

### Score Interpretation

- **Z-scores**: Standardized scores with mean=0, std=1
  - Positive values = above average
  - Negative values = below average
  - Typical range: -3 to +3

- **Percentiles**: 0-100 scale showing percentage of students scoring below

- **Raw scores**: Subject-specific scales (varies by subject)

---

## Installation

### Requirements
```bash
pip install -r requirements.txt
```

### Dependencies
- dash==2.14.2
- dash-bootstrap-components==1.5.0
- pandas==2.1.3
- plotly==5.18.0
- scikit-learn==1.3.2
- numpy==1.26.2

---

## Usage

### Running the Application

```bash
python app_enhanced.py
```

Then open your browser to: **http://127.0.0.1:8050/**

### Performance Considerations

- Student-level analysis uses a sample (default: 50,000 records) for performance
- Adjust `sample_size` parameter in `load_student_level_data()` if needed
- Larger samples = more accurate but slower
- Recommended minimum: 10,000 for statistical validity

---

## Interpretation Guide for Government Officials

### Understanding Z-Scores

- **Z-score = 0**: Exactly average performance
- **Z-score = +1**: One standard deviation above average (better than ~84% of schools)
- **Z-score = +2**: Two standard deviations above average (better than ~97% of schools)
- **Z-score = -1**: One standard deviation below average
- **Z-score = -2**: Two standard deviations below average

### Key Questions the Dashboard Answers

1. **Which departments are performing best/worst?**
   - Use Department Analysis tab
   - Look at department average scores

2. **Are urban schools outperforming rural schools?**
   - Use National Overview tab
   - Filter by area and compare

3. **How much does socioeconomic status affect outcomes?**
   - Use Socioeconomic Analysis tab
   - Look at Estrato or INSE analysis
   - High correlation = strong impact

4. **Which schools are truly excellent (not just serving privileged students)?**
   - **Use Advanced Analytics tab**
   - Look at schools with highest positive residuals
   - These schools add maximum value

5. **Which schools need urgent intervention?**
   - Use Advanced Analytics tab for value-added approach
   - OR Municipality Analysis for absolute performance

6. **What factors most impact student success?**
   - Use Advanced Analytics tab
   - Check Feature Importance chart
   - Top features are most impactful

### Policy Recommendations Based on Analysis

1. **High socioeconomic impact observed?**
   - Implement targeted support programs
   - Provide technology access (computers, internet)
   - Support for disadvantaged families

2. **Large urban-rural gap?**
   - Rural school investment programs
   - Teacher incentives for rural areas
   - Infrastructure improvement

3. **Identified high value-added schools?**
   - Study their practices
   - Create best practice guides
   - Teacher exchange programs
   - Replicate successful models

4. **Schools underperforming given context?**
   - Principal training programs
   - Teacher professional development
   - Infrastructure assessment
   - Management interventions

---

## Technical Architecture

### Machine Learning Models

**Gradient Boosting Regressor** (Student-level):
- Handles non-linear relationships
- Robust to outliers
- Feature importance built-in
- Parameters: 100 estimators, max_depth=5

**Random Forest Regressor** (School-level):
- Ensemble learning
- Handles categorical features well
- Robust and interpretable
- Parameters: 200 estimators, max_depth=10

### Model Validation
- 80/20 train-test split
- R² score for goodness of fit
- MAE and RMSE for error quantification
- Cross-validation available (can be added)

---

## Limitations and Caveats

1. **Data from 2017**: Results reflect that academic year only

2. **Sampling**: Student-level analysis uses sampling; results may vary slightly between runs

3. **Causation vs Correlation**: Models show associations, not necessarily causation

4. **Missing Data**: Some schools/municipalities may have incomplete data across all grades

5. **Z-scores**: Based on national distribution; interpretation may differ for specific subpopulations

6. **External Factors**: Models cannot account for all factors (e.g., natural disasters, local events, school leadership changes)

---

## Future Enhancements

### Potential Additions

1. **Temporal Analysis**: Compare performance across multiple years

2. **Geographic Visualization**: Interactive maps showing regional performance

3. **Predictive Analytics**: Forecast future performance trends

4. **Intervention Tracking**: Monitor impact of specific programs

5. **Export Functionality**: PDF reports, Excel exports

6. **User Authentication**: Role-based access for different government levels

7. **Real-time Data Integration**: Connect to live ICFES databases

8. **Advanced Filtering**: More granular filters (e.g., school size, teacher qualifications)

---

## Support and Documentation

### For Technical Issues
- Check that all CSV files are in the same directory as the app
- Ensure all dependencies are installed
- Verify Python version ≥ 3.8

### For Data Questions
- Refer to ICFES official documentation
- Column descriptions in Saber 11 technical manual
- Consult metadata files for code definitions

---

## Authors and Acknowledgments

**Data Source**: ICFES (Colombian Institute for Educational Evaluation)

**Application**: Built with Dash framework for interactive analytics

**Purpose**: Governmental decision support for educational policy

---

## License and Usage Terms

This dashboard is designed for governmental and educational research purposes. Data should be used in compliance with ICFES terms and Colombian data protection regulations.

---

## Quick Start Guide

**First Time Users (Government Officials):**

1. **Start with National Overview**
   - Get familiar with the data
   - Understand the filters
   - Observe national trends

2. **Drill Down to Your Region**
   - Go to Department Analysis
   - Select your department
   - Review municipality rankings

3. **Analyze Socioeconomic Impact**
   - Visit Socioeconomic Analysis tab
   - Try different analysis types
   - Understand local disparities

4. **Identify Best Schools**
   - **Go to Advanced Analytics tab**
   - Review value-added analysis
   - List schools with highest residuals
   - Plan site visits to study best practices

5. **Create Action Plan**
   - Identify schools needing support (negative residuals)
   - Design interventions based on feature importance
   - Allocate resources to high-impact areas

---

**For questions or support, consult your technical team or refer to ICFES documentation.**
