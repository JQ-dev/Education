# Quick Start Guide

## Which App Should I Run?

You now have **TWO** Dash applications:

### 1. `app.py` - Basic Version
Simple, fast dashboard for quick exploration

**Run with:**
```bash
python app.py
```

**Best for:**
- Quick school lookup
- Basic exploration
- Learning the data
- Simple presentations

---

### 2. `app_enhanced.py` - Government Analytics Platform ⭐
Comprehensive analytics for governmental decision-making

**Run with:**
```bash
python app_enhanced.py
```

**Best for:**
- Government policy making
- Resource allocation decisions
- Department/municipality analysis
- Identifying truly excellent schools (value-added)
- Socioeconomic impact analysis
- Fair school evaluation

---

## Installation

First time setup:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the enhanced app (recommended)
python app_enhanced.py

# Open browser
# Navigate to: http://127.0.0.1:8050/
```

---

## First Steps (Government Users)

### Step 1: National Overview
1. Open the app
2. You'll land on "National Overview" tab
3. Try the filters:
   - Select different grades (3, 5, 9, 11)
   - Filter by school type (Official vs Private)
   - Filter by area (Urban vs Rural)
4. Observe the summary cards and charts

### Step 2: Your Department
1. Click **"Department Analysis"** tab
2. Select your department from dropdown
3. Review:
   - Total municipalities and schools
   - Department averages
   - Municipality rankings
4. Identify top and bottom municipalities

### Step 3: Drill Down to Municipality
1. Click **"Municipality Analysis"** tab
2. Select department, then municipality
3. View:
   - Top 15 schools
   - Performance distribution
   - School type comparison

### Step 4: Socioeconomic Impact ⭐
1. Click **"Socioeconomic Analysis"** tab
2. Try different analysis types:
   - **Estrato** (most important)
   - Parent Education
   - Home Assets
   - Socioeconomic Index
3. Understand achievement gaps

### Step 5: Find Best Schools ⭐⭐⭐
**This is the most powerful feature!**

1. Click **"Advanced Analytics"** tab
2. Select "School-Level Prediction" (faster) or "Student-Level" (more accurate)
3. Choose target score (Mathematics recommended)
4. Review:
   - Model performance (R² score)
   - Feature importance chart
   - Value-added scatter plot
   - **Top Schools table** - These are TRULY excellent schools
   - Bottom Schools table - These need intervention

**Why this matters:**
- Traditional rankings show schools with high scores (often serving privileged students)
- **Value-added analysis** shows schools performing ABOVE expectations
- These schools achieve excellence DESPITE challenges
- Study these schools to learn best practices!

---

## Key Insights to Extract

### For National Policy Makers
1. **Urban-Rural Gap**: Filter by area in National Overview
2. **Public-Private Gap**: Filter by school type
3. **Socioeconomic Impact**: Check Socioeconomic Analysis tab
4. **Best Practices**: Identify high value-added schools in Advanced Analytics

### For Department Secretaries
1. Go to Department Analysis
2. Compare your department to national average
3. Identify struggling municipalities
4. Find high-performing municipalities to benchmark

### For Municipality Officers
1. Go to Municipality Analysis
2. Review all schools in your municipality
3. Identify schools needing support
4. Find local success stories
5. Use Advanced Analytics to see which schools add most value

### For Researchers
1. Use Socioeconomic Analysis for equity studies
2. Export data tables (click on tables to select/copy)
3. Use Advanced Analytics for value-added research
4. Check feature importance to identify intervention targets

---

## Understanding the Value-Added Analysis

### What is it?
A statistical method that controls for student demographics to identify schools that truly excel.

### How to read it?

**Positive Residual (Green highlight)**:
- School performs BETTER than expected
- Adding value beyond demographics
- ⭐ These are your truly excellent schools
- Study them for best practices

**Negative Residual (Red highlight)**:
- School performs WORSE than expected
- Not adding expected value
- Need intervention and support
- Priority for improvement programs

**Near Zero Residual**:
- School performing as expected given demographics
- Typical/average value-added

### Example Interpretation

If a school has:
- **Expected score**: 45 (based on student demographics)
- **Actual score**: 52
- **Residual**: +7

This school is adding significant value! Students gain 7 points more than expected.

---

## Common Questions

**Q: Why are scores negative?**
A: These are z-scores (standardized). Zero = average. Negative = below average. Positive = above average.

**Q: What's a good z-score?**
A:
- Z-score > 0: Above average
- Z-score > 1: Top 16%
- Z-score > 2: Top 2%

**Q: Which tab is most important for government?**
A: **Advanced Analytics** - Shows which schools truly add value, not just which serve privileged students.

**Q: How do I find schools in my area?**
A: Use Department → Municipality → School tabs to drill down. Or use School Analysis tab to search by name.

**Q: What is INSE?**
A: Individual Socioeconomic Index - official Colombian measure combining multiple socioeconomic factors.

**Q: What is Estrato?**
A: Socioeconomic stratum (1-6 scale) based on housing/neighborhood characteristics. 1 = lowest, 6 = highest.

---

## Exporting Data

To export any table:
1. Click on the table
2. Select rows (or Ctrl+A for all)
3. Ctrl+C to copy
4. Paste into Excel or other tool

For advanced exports, contact technical support to add CSV export buttons.

---

## Performance Tips

- First load may take 5-10 seconds (loading data)
- Student-level analysis uses 50,000 sample for speed
- For faster performance, use School-Level prediction instead of Student-Level
- Close other browser tabs if app feels slow

---

## Troubleshooting

**App won't start:**
```bash
# Check if dependencies installed
pip install -r requirements.txt

# Check Python version (needs 3.8+)
python --version
```

**Charts not showing:**
- Refresh browser (F5)
- Clear browser cache
- Try different browser (Chrome recommended)

**"No data available":**
- Ensure all CSV files are in same folder as app
- Check file names match exactly

**App is slow:**
- Close other applications
- Use School-Level instead of Student-Level in Advanced Analytics
- Filter data to reduce computation

---

## Next Steps

After exploring the dashboard:

1. **Identify priorities** based on data
2. **Create action plans** for intervention schools
3. **Study best practices** from high value-added schools
4. **Design targeted programs** based on socioeconomic gaps
5. **Allocate resources** to high-impact areas
6. **Monitor progress** over time (with multi-year data)

---

## Support

For technical issues:
- Check that all data files are present
- Review README_ENHANCED.md for detailed documentation
- Consult COMPARISON.md to understand differences between apps

For data interpretation:
- Refer to ICFES documentation
- Consult with educational researchers
- Review README_ENHANCED.md "Interpretation Guide" section

---

**Remember**: The goal is not just to rank schools, but to identify what works and replicate success while supporting struggling schools!
