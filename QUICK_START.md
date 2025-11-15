# Quick Start Guide - SABER Education Dashboard

## 🚀 Get Running in 3 Minutes!

### Prerequisites

- Python 3.8 or higher
- pip package manager
- SABER data files (Parquet format)

---

## Step 1: Install Dependencies (1 minute)

```bash
pip install dash dash-bootstrap-components pandas plotly numpy scikit-learn
```

**Optional** (for authentication):
```bash
pip install -r requirements_auth.txt
```

---

## Step 2: Launch the Demo (30 seconds)

### Option A: Using Demo Launcher
```bash
python demo.py
```

### Option B: Direct Launch
```bash
python app_enhanced.py
```

### Option C: Simple Dashboard (No landing page)
```bash
python app.py
```

---

## Step 3: Open Your Browser (30 seconds)

The demo launcher will automatically open your browser to:
```
http://localhost:8052/
```

Or manually navigate to that URL.

---

## What You'll See

### Landing Page (Home)
- Professional hero section
- Platform statistics
- Feature showcase
- "Explore Dashboard" button

### Dashboard
Click "Explore Dashboard" to access 7 analytical tabs:
1. 📊 **National Overview** - Colombia-wide statistics
2. 🗺️ **Department Analysis** - Regional breakdown
3. 🏘️ **Municipality Analysis** - Municipal deep-dive
4. 🏫 **School Analysis** - Individual school search
5. 💰 **Socioeconomic Analysis** - SES impact
6. 🤖 **Advanced Analytics** - ML predictions
7. 📊 **KPIs** - Equity & efficiency metrics

---

## Quick Tips

### Navigation
- Click tabs to switch between analyses
- Use filters to focus your view
- Hover over charts for details

### Filters
- All filters update in real-time
- Multi-select available for departments/municipalities
- Filters are independent per tab

### Charts
- Hover for tooltips
- Zoom: Click and drag
- Pan: Drag while zoomed
- Reset: Double-click
- Download: Camera icon

---

## Common First Actions

### For Education Officials:
1. Start at National Overview
2. Check your department in Department Analysis
3. Review KPIs for equity metrics

### For Researchers:
1. Check Socioeconomic Analysis
2. Explore Advanced Analytics for ML insights
3. Use School Analysis to find specific institutions

### For School Administrators:
1. Go to School Analysis
2. Search for your school
3. Compare with Municipality Analysis

---

## Data Files

### Required Files:
Place in the project directory:
- `Examen_Saber_11_SS_20241.parquet`
- `Examen_Saber_11_SS_20242.parquet`

### Alternative Files (legacy):
- CSV files from ICFES
- ZIP compressed files

The app will automatically detect and load available data.

---

## Stopping the Application

Press **Ctrl+C** in the terminal to stop the server.

---

## Next Steps

Once you're comfortable with the basics:

1. **Read the Demo Guide**: `DEMO_GUIDE.md` for detailed walkthrough
2. **Setup Authentication**: `AUTH_README.md` for user login
3. **Deploy to Cloud**: Check cloud deployment guides
4. **Customize**: Modify colors, add your logo

---

## Troubleshooting

### Port Already in Use?
```bash
# Use a different port
python app_enhanced.py
# Then edit the port in the script (default: 8052)
```

### Missing Data?
- App will still run with sample/limited data
- Some visualizations may show fewer results
- Place Parquet files in root directory

### Dependencies Error?
```bash
pip install --upgrade pip
pip install -r requirements_auth.txt
```

### Browser Doesn't Open?
- Manually navigate to http://localhost:8052/
- Try different browser (Chrome/Firefox recommended)

---

## Key Features at a Glance

✅ **Professional Landing Page** - Institutional-grade design
✅ **7 Analytical Tabs** - Comprehensive coverage
✅ **Interactive Charts** - Zoom, pan, download
✅ **Real-time Filters** - Dynamic data updates
✅ **Multi-level Analysis** - National → Department → Municipality → School
✅ **ML Predictions** - Value-added analysis
✅ **Equity KPIs** - 6 independent metrics
✅ **Responsive Design** - Works on all devices
✅ **Cloud-Ready** - Deploy anywhere

---

## Support

- **Demo Guide**: Detailed feature walkthrough
- **Integration Guide**: Technical integration
- **Auth README**: User authentication setup
- **GitHub Issues**: Report bugs or request features

---

**You're ready to go! 🎉**

Run `python demo.py` and start exploring Colombian educational data!

---

## One-Line Quick Start

```bash
pip install dash dash-bootstrap-components pandas plotly numpy scikit-learn && python demo.py
```

That's it! Your browser will open automatically. Enjoy! 🚀
