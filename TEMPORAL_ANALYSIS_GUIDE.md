# SABER Temporal Analysis Dashboard - User Guide

## 🎯 Overview

The **Temporal Analysis Dashboard** (`app_temporal.py`) extends the SABER analytics platform with comprehensive **year-over-year trend analysis** capabilities. This enables governmental agencies to:

- Track educational performance trends over multiple years
- Identify improving or declining schools/regions
- Make data-driven projections for future planning
- Understand the impact of policy changes over time

---

## 📦 Data Requirements

### Supported File Formats

#### 1. **Parquet Files** (Recommended - Fastest)
```
Examen_Saber_11_SS_20221.parquet
Examen_Saber_11_SS_20222.parquet
Examen_Saber_11_SS_20231.parquet
Examen_Saber_11_SS_20232.parquet
Examen_Saber_11_SS_20241.parquet
Examen_Saber_11_SS_20242.parquet
```

**Why Parquet?**
- 5-10x faster to load than CSV
- Smaller file size (compressed)
- Preserves data types
- Industry standard for big data

#### 2. **CSV Files** (Supported)
```
Saber_11__2017-1.csv
ICFES_2019.csv
Saber_11__2022-1.csv
```

#### 3. **ZIP Files** (Supported)
```
Saber_11__2017-2.zip
ICFES_2019.zip
```

---

## 🔧 Period Parsing

### How Periods Work

The app **automatically combines multiple periods within the same year**:

**Example:**
- File: `Examen_Saber_11_SS_20221.parquet`
  - PERIODO column: `20221` → Parsed as **Year 2022, Period 1**

- File: `Examen_Saber_11_SS_20222.parquet`
  - PERIODO column: `20222` → Parsed as **Year 2022, Period 2**

**Result:** Both periods are combined and analyzed as **Year 2022**

### Parsing Logic

```python
def parse_period_to_year(periodo):
    """
    20221 → 2022
    20222 → 2022
    20231 → 2023
    20232 → 2023
    """
    periodo_str = str(int(periodo))
    return int(periodo_str[:4])  # First 4 digits = year
```

---

## 📊 Dashboard Tabs

### TAB 1: 📈 Year-over-Year Trends

**Purpose:** High-level national performance trends

**Features:**
- **Year Range Slider:** Select specific years to analyze
- **Score Type Selector:** Mathematics, Reading, or Global scores
- **3 Visualizations:**
  1. **National Trend Line:** Overall Colombian performance over time
  2. **Top 5 Department Trends:** Best-performing regions
  3. **School Type Comparison:** Official vs Non-Official trends

**Key Questions Answered:**
- Is national performance improving or declining?
- Which departments are leading in improvement?
- Is the gap between public and private schools widening?

**Use Case:**
> "As Minister of Education, I need to see if our 2020 policy reforms led to measurable improvements in 2021-2023."

---

### TAB 2: 🗺️ Department Trends

**Purpose:** Multi-department comparative analysis

**Features:**
- **Multi-Select Dropdown:** Compare up to 5 departments simultaneously
- **Score Type Filter:** Choose subject area
- **3 Visualizations:**
  1. **Comparison Trend:** Line chart showing all selected departments
  2. **Growth Rate Bar Chart:** Overall % change from first to last year
  3. **Variance Trend:** Consistency of scores (lower = more stable)

**Key Metrics:**
- **Growth Rate:** Percentage improvement/decline
- **Variance:** Score consistency (high variance = inequality within department)
- **Relative Performance:** How departments compare to each other

**Use Case:**
> "Compare Antioquia, Cundinamarca, and Valle to see which has the most consistent improvement trajectory."

---

### TAB 3: 🏫 School Evolution

**Purpose:** Track individual school performance over time

**Features:**
- **School Search:** Find schools by name (fuzzy matching)
- **Multi-Year Filter:** Only shows schools with data in 2+ years
- **Individual School Timelines:** See exact performance trajectory

**What You Can Track:**
- Did a school improve after a new principal?
- Impact of infrastructure investments
- Schools maintaining excellence over time
- Schools showing concerning decline

**Use Case:**
> "Search for 'Colegio San Francisco' to see if their scores improved after we invested in technology in 2021."

---

### TAB 4: 📊 Improvement Analysis

**Purpose:** Identify biggest winners and losers

**Features:**
- **Analysis Level:** Choose Schools, Municipalities, or Departments
- **Year Comparison:** Select which years to compare
- **3 Outputs:**
  1. **Most Improved Table (Top 20):** Biggest positive changes
  2. **Most Declined Table (Bottom 20):** Biggest negative changes
  3. **Distribution Chart:** Overall pattern of changes

**Color Coding:**
- 🟢 **Green:** Improved entities
- 🔴 **Red:** Declined entities

**Key Applications:**
1. **Recognition:** Reward most-improved schools/regions
2. **Intervention:** Target resources to declining entities
3. **Best Practices:** Study what improved schools did right
4. **Early Warning:** Catch decline early

**Use Case:**
> "Generate the list of Top 20 most-improved schools from 2019 to 2023 for the Excellence Awards ceremony."

---

### TAB 5: 🔮 Future Projections

**Purpose:** Statistical forecasting for planning

**Features:**
- **Linear Regression Projections:** 3-year forward projections
- **Historical vs Projected Visualization:** Clear distinction
- **Confidence Context:** Based on historical trends

**Requirements:**
- Minimum 3 years of data for reliable projections
- More years = more accurate projections

**What It Shows:**
- If current trends continue, where will scores be in 3 years?
- Are we on track to meet 2025/2030 goals?
- Where to adjust policy if trajectory is concerning

**Use Case:**
> "Project where national mathematics scores will be in 2027 if current trends continue. Are we on track for our policy goals?"

**⚠️ Important:** These are statistical projections, not guarantees. Real-world events (pandemics, policy changes, economic shifts) can alter trajectories.

---

## 🚀 Getting Started

### Step 1: Add Your Data Files

Place Parquet or CSV files in the same directory as `app_temporal.py`:

```bash
Education/
├── app_temporal.py
├── Examen_Saber_11_SS_20221.parquet  ✅ New files
├── Examen_Saber_11_SS_20222.parquet  ✅
├── Examen_Saber_11_SS_20231.parquet  ✅
├── Examen_Saber_11_SS_20232.parquet  ✅
├── Saber_11__2017-1.csv               (existing)
└── ICFES_2019.csv                     (existing)
```

### Step 2: Install Requirements

```bash
pip install pandas plotly dash dash-bootstrap-components scikit-learn pyarrow
```

**Note:** `pyarrow` is required for reading Parquet files.

### Step 3: Run the App

```bash
python app_temporal.py
```

### Step 4: Open Browser

Navigate to: **http://127.0.0.1:8050/**

---

## 📈 Data Loading Process

When you start the app, it will:

```
======================================================================
SABER TEMPORAL ANALYSIS - Loading Multi-Year Data
======================================================================

Loading Examen_Saber_11_SS_20221.parquet...
  ✓ Loaded 500,234 records

Loading Examen_Saber_11_SS_20222.parquet...
  ✓ Loaded 487,123 records

Loading Saber_11__2017-1.csv...
  ✓ Loaded 300,156 records

Loading ICFES_2019.csv...
  ✓ Loaded 450,789 records

✅ Total loaded: 1,738,302 student records
📅 Years available: [2017, 2019, 2022]

✅ Aggregated data ready:
   Schools by year: 52,341 records
   Municipalities by year: 3,215 records
   Departments by year: 96 records
======================================================================
```

---

## 🎯 Key Use Cases by Role

### 1. **National Minister of Education**

**Question:** "Is our national performance improving?"

**Steps:**
1. Go to **📈 Year-over-Year Trends** tab
2. Set year range to all available years
3. Select "Mathematics"
4. Review national trend line
5. Check if line is going up (improvement) or down (decline)

**Follow-up:**
- Check **Department Trends** to see which regions drive the trend
- Use **Future Projections** to see if on track for goals

---

### 2. **Department Education Secretary**

**Question:** "How does my department compare to neighbors?"

**Steps:**
1. Go to **🗺️ Department Trends** tab
2. Select your department + 2-3 neighboring departments
3. View comparison trend
4. Check growth rate chart

**Actions:**
- If lagging: Study what leading departments are doing
- If leading: Document best practices for replication
- If declining: Immediate investigation needed

---

### 3. **Municipality Education Officer**

**Question:** "Which of my schools improved the most?"

**Steps:**
1. Go to **📊 Improvement Analysis** tab
2. Select "Schools" level
3. Choose year comparison (e.g., 2019 vs 2023)
4. Filter results by your municipality (use search in table)

**Actions:**
- Visit most-improved schools to understand what they did
- Provide additional support to declining schools
- Share best practices across municipality

---

### 4. **Policy Researcher**

**Question:** "Did the 2020 technology program improve outcomes?"

**Steps:**
1. Identify regions that received the program
2. Go to **🗺️ Department Trends**
3. Compare program regions vs control regions
4. Check if program regions show steeper improvement after 2020

**Analysis:**
- Look for divergence in trend lines after 2020
- Check growth rates for statistical significance
- Use **Improvement Analysis** for effect size

---

### 5. **School Principal**

**Question:** "Is my school improving over time?"

**Steps:**
1. Go to **🏫 School Evolution** tab
2. Search for your school by name
3. View your school's trajectory
4. Compare to municipality/department averages

**Insights:**
- Identify years with significant changes (positive or negative)
- Correlate with school events (new programs, staff changes, etc.)
- Set improvement targets based on trends

---

## 💡 Advanced Analysis Tips

### Tip 1: Identify Policy Impact

**Scenario:** You implemented a new program in 2021. Did it work?

**Method:**
1. Look at trends BEFORE 2021 (baseline trajectory)
2. Look at trends AFTER 2021
3. Check if slope increased (acceleration of improvement)

**What to Look For:**
- **Program worked:** Steeper positive slope after 2021
- **No effect:** Slope unchanged
- **Negative effect:** Slope decreased or reversed

---

### Tip 2: Spot Regional Patterns

**Scenario:** Some departments consistently outperform others

**Method:**
1. Use **Department Trends** tab
2. Select top 5 and bottom 5 departments
3. Look for patterns:
   - Are top departments all urban/wealthy?
   - Are bottom departments all rural/poor?
   - This reveals systemic equity issues

**Policy Response:**
- Targeted interventions for struggling regions
- Resource redistribution for equity
- Study what top departments do differently

---

### Tip 3: Early Warning System

**Scenario:** Catch declining schools before crisis

**Method:**
1. Run **Improvement Analysis** annually
2. Filter for schools showing 2+ consecutive years of decline
3. Create priority intervention list

**Prevention is Key:**
- Early intervention is cheaper than crisis response
- Small declines are easier to reverse
- Proactive support prevents school failure

---

### Tip 4: Validate Improvement Claims

**Scenario:** A school claims "dramatic improvement"

**Method:**
1. Search school in **School Evolution**
2. Look at multi-year trend, not just one year
3. Check if improvement is sustained or one-time spike

**Beware:**
- Single-year spikes may be measurement error
- True improvement shows sustained trend
- Compare to similar schools for context

---

## 🔍 Data Quality Considerations

### What If I See Strange Results?

#### 1. **Missing Years**
- **Symptom:** Gaps in trend lines
- **Cause:** School didn't participate that year OR data not loaded
- **Solution:** Check if data files for those years exist

#### 2. **Dramatic Spikes**
- **Symptom:** Huge jump in one year, then drop
- **Cause:** Could be legitimate OR data error/anomaly
- **Solution:** Cross-reference with other sources, investigate school

#### 3. **All Trends Flat**
- **Symptom:** No visible changes over years
- **Cause:** Scores may be standardized within each year
- **Solution:** Look at raw scores, not z-scores

#### 4. **Only Two Years Available**
- **Symptom:** Projections disabled
- **Cause:** Need minimum 3 years for statistical validity
- **Solution:** Add more years of data

---

## 📚 Technical Details

### Column Requirements

For temporal analysis to work, files must have:

**Required Columns:**
- `PERIODO` or `YEAR`: To identify time periods
- `PUNT_MATEMATICAS`: Math scores
- `PUNT_LECTURA_CRITICA`: Reading scores
- `COLE_COD_DANE_ESTABLECIMIENTO`: School ID
- `COLE_DEPTO_UBICACION`: Department
- `COLE_MCPIO_UBICACION`: Municipality

**Optional (for enhanced analysis):**
- `COLE_NATURALEZA`: School type (Official/Private)
- `COLE_AREA_UBICACION`: Urban/Rural
- `FAMI_ESTRATOVIVIENDA`: Socioeconomic stratum
- `PUNT_GLOBAL`: Global score

### Aggregation Logic

**Student → School:**
- Mean of all student scores in that school-year
- Count of students tested

**Student → Municipality:**
- Mean of all student scores in that municipality-year
- Count of students tested

**Student → Department:**
- Mean of all student scores in that department-year
- Count of students tested

---

## 🎓 Interpreting Results

### Growth Rate

**Formula:** `((Score_End - Score_Start) / Score_Start) * 100`

**Example:**
- 2019 Score: 50
- 2023 Score: 55
- Growth: ((55 - 50) / 50) * 100 = **10%**

**Interpretation:**
- **Positive %:** Improvement
- **Negative %:** Decline
- **> 5%:** Significant change
- **< 2%:** Minimal change (might be noise)

### Variance

**What it measures:** Consistency of scores within a region/school

**High Variance:**
- Some schools/students very high, others very low
- Indicates inequality
- Priority for equity interventions

**Low Variance:**
- Most schools/students cluster around mean
- More equitable outcomes
- Consistent quality

---

## 🚨 Common Mistakes to Avoid

### ❌ Mistake 1: Comparing Non-Comparable Years
**Problem:** Comparing 2017 (old test format) with 2023 (new format)
**Solution:** Check if test methodology changed between years

### ❌ Mistake 2: Ignoring Sample Size
**Problem:** Celebrating improvement in school with only 10 students
**Solution:** Filter for minimum sample size (e.g., N > 30)

### ❌ Mistake 3: Single-Year Conclusions
**Problem:** Judging a school based on one bad year
**Solution:** Look at 3+ year trends before making decisions

### ❌ Mistake 4: Ignoring Context
**Problem:** Comparing COVID year (2020) to normal years
**Solution:** Account for external factors in interpretation

### ❌ Mistake 5: Over-Trusting Projections
**Problem:** Assuming projections are guaranteed
**Solution:** Use projections as guides, not certainties. Monitor and adjust.

---

## 📞 Support

**For questions about:**
- **Data loading:** Ensure file naming matches patterns
- **Missing visualizations:** Check that required columns exist
- **Performance issues:** Consider using Parquet instead of CSV
- **Interpretation:** Refer to this guide or consult with data analysts

---

## 🎯 Summary

The Temporal Analysis Dashboard enables:

✅ **Trend Identification:** Spot improvement/decline patterns
✅ **Comparative Analysis:** Benchmark regions against each other
✅ **Early Warning:** Catch problems before they escalate
✅ **Impact Assessment:** Evaluate policy effectiveness
✅ **Strategic Planning:** Make data-driven 3-5 year plans
✅ **Accountability:** Track if interventions work over time

**This transforms one-time snapshots into continuous improvement monitoring.**

---

## 🔗 Related Documentation

- **QUICKSTART.md:** Basic app usage
- **README_ENHANCED.md:** Full feature documentation
- **COMPARISON.md:** Differences between app versions

---

*Last Updated: 2025*

**Ready to unlock insights from multi-year educational data!** 🚀
