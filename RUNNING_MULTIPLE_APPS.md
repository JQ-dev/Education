# Running Multiple Apps Simultaneously

## 🚀 Quick Start

All three SABER dashboard applications can now run **in parallel** on different ports!

### Port Assignments

| Application | Port | URL |
|------------|------|-----|
| **app.py** (Basic) | 8051 | http://127.0.0.1:8051/ |
| **app_enhanced.py** (Government) | 8052 | http://127.0.0.1:8052/ |
| **app_temporal.py** (Temporal) | 8053 | http://127.0.0.1:8053/ |

---

## Method 1: Automatic (Recommended)

### Windows
```bash
run_all_apps.bat
```

### Linux/Mac
```bash
./run_all_apps.sh
```

This will:
- ✅ Start all 3 apps simultaneously
- ✅ Open each on its own port
- ✅ Display URLs for easy access
- ✅ Allow you to stop all with Ctrl+C

---

## Method 2: Manual (Separate Terminals)

Open 3 separate terminal windows:

### Terminal 1: Basic Dashboard
```bash
python app.py
```
→ Opens on http://127.0.0.1:8051/

### Terminal 2: Government Analytics
```bash
python app_enhanced.py
```
→ Opens on http://127.0.0.1:8052/

### Terminal 3: Temporal Analysis
```bash
python app_temporal.py
```
→ Opens on http://127.0.0.1:8053/

---

## Method 3: Background Processes (Linux/Mac)

```bash
# Start all in background
python app.py &
python app_enhanced.py &
python app_temporal.py &

# View running processes
ps aux | grep app.py

# Stop all
killall python
```

---

## Method 4: Using nohup (Linux/Mac)

```bash
# Start with logs
nohup python app.py > app1.log 2>&1 &
nohup python app_enhanced.py > app2.log 2>&1 &
nohup python app_temporal.py > app3.log 2>&1 &

# Check logs
tail -f app1.log
tail -f app2.log
tail -f app3.log
```

---

## Why Run Multiple Apps?

### Use Case 1: Comparative Analysis
- **app.py (8051)**: Quick school lookup
- **app_enhanced.py (8052)**: Deep value-added analysis
- **app_temporal.py (8053)**: Year-over-year trends

→ Switch between apps without restarting!

### Use Case 2: Multi-User Access
Different team members can use different apps:
- Analyst 1: Uses basic dashboard (8051)
- Analyst 2: Uses government analytics (8052)
- Analyst 3: Uses temporal trends (8053)

### Use Case 3: Presentation Mode
Have all apps ready during a presentation:
- Show national overview in app 8052
- Show specific school trends in app 8053
- Quick lookups in app 8051

---

## Accessing the Apps

Once running, open your browser to:

### Basic Dashboard (Port 8051)
```
http://127.0.0.1:8051/
http://localhost:8051/
```
**Best for**: Quick school searches, basic comparisons

### Government Analytics (Port 8052)
```
http://127.0.0.1:8052/
http://localhost:8052/
```
**Best for**: Value-added analysis, department comparisons, socioeconomic impact

### Temporal Analysis (Port 8053)
```
http://127.0.0.1:8053/
http://localhost:8053/
```
**Best for**: Year-over-year trends, improvement analysis, projections

---

## Stopping Apps

### If using run_all_apps scripts:
- Press **Ctrl+C** in the terminal

### If running manually:
- Press **Ctrl+C** in each terminal window

### If running in background:
```bash
# Find processes
ps aux | grep "python app"

# Kill specific process
kill <PID>

# Kill all Python processes (careful!)
killall python
```

---

## Troubleshooting

### Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Windows
netstat -ano | findstr :8051
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8051 | xargs kill -9
lsof -ti:8052 | xargs kill -9
lsof -ti:8053 | xargs kill -9
```

### Can't Access from Browser

1. **Check if app is running**:
   - Look for console output
   - Check for errors in terminal

2. **Try different URL formats**:
   - `http://127.0.0.1:8051/`
   - `http://localhost:8051/`
   - `http://0.0.0.0:8051/` (Linux/Mac)

3. **Check firewall**:
   - Allow Python through firewall
   - Allow ports 8051-8053

### Performance Issues

Running all 3 apps uses more memory:
- Each app: ~200-500 MB
- Total: ~1-1.5 GB

**Recommendations**:
- Close unused browser tabs
- Run only the apps you need
- Use Parquet files for faster loading

---

## Advanced: Custom Ports

Want different ports? Edit the files:

### app.py
```python
# Line 584
app.run(debug=True, host='0.0.0.0', port=8051)  # Change 8051
```

### app_enhanced.py
```python
# Line 1260
app.run(debug=True, host='0.0.0.0', port=8052)  # Change 8052
```

### app_temporal.py
```python
# Line 955
app.run(debug=True, host='0.0.0.0', port=8053)  # Change 8053
```

---

## Network Access (Optional)

To access from other computers on your network:

1. Find your IP address:
   ```bash
   # Windows
   ipconfig

   # Linux/Mac
   ifconfig
   ```

2. Access from other computers:
   ```
   http://<YOUR_IP>:8051/
   http://<YOUR_IP>:8052/
   http://<YOUR_IP>:8053/
   ```

3. **Security Note**: Only do this on trusted networks!

---

## Production Deployment

For production use, consider:

### Option 1: Using Gunicorn (Linux/Mac)
```bash
pip install gunicorn

gunicorn app:server -b 0.0.0.0:8051 &
gunicorn app_enhanced:server -b 0.0.0.0:8052 &
gunicorn app_temporal:server -b 0.0.0.0:8053 &
```

### Option 2: Using Waitress (Windows)
```bash
pip install waitress

waitress-serve --port=8051 app:server &
waitress-serve --port=8052 app_enhanced:server &
waitress-serve --port=8053 app_temporal:server &
```

### Option 3: Docker
Create `docker-compose.yml`:
```yaml
version: '3'
services:
  app-basic:
    build: .
    command: python app.py
    ports:
      - "8051:8051"

  app-enhanced:
    build: .
    command: python app_enhanced.py
    ports:
      - "8052:8052"

  app-temporal:
    build: .
    command: python app_temporal.py
    ports:
      - "8053:8053"
```

---

## Summary

### ✅ All apps now run on separate ports:
- app.py → 8051
- app_enhanced.py → 8052
- app_temporal.py → 8053

### ✅ Easy to run all simultaneously:
- Windows: `run_all_apps.bat`
- Linux/Mac: `./run_all_apps.sh`

### ✅ Changed from `app.run_server()` to `app.run()`:
- More standard Dash syntax
- Better compatibility

### ✅ No more port conflicts!

---

**Happy analyzing! 📊🚀**
