# 🚀 Quick Setup Guide

## Step 1: Install MySQL

### macOS:
```bash
brew install mysql
brew services start mysql
```

### Linux:
```bash
sudo apt-get install mysql-server
sudo systemctl start mysql
```

## Step 2: Configure MySQL Password

Open MySQL:
```bash
mysql -u root -p
```

Set password (if needed):
```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'your_password';
EXIT;
```

**Important**: Update the password in `server/app.py` line 16:
```python
'password': 'your_password',  # Change this
```

## Step 3: Setup Python Environment

```bash
cd server
chmod +x setup.sh
./setup.sh
```

This will create a virtual environment and install all dependencies.

## Step 4: Start Backend Server

```bash
cd server
source venv/bin/activate
python app.py
```

You should see:
```
Database initialized successfully!
* Running on http://127.0.0.1:5000
```

## Step 5: Start Frontend Server

Open a NEW terminal window:

```bash
cd public
python3 -m http.server 8000
```

## Step 6: Open Application

Open your browser and go to:
```
http://localhost:8000/login.html
```

## 🎉 You're Ready!

1. Register a new account
2. Login with your credentials
3. Start learning!

## ⚠️ Troubleshooting

### MySQL Connection Error
- Make sure MySQL is running: `brew services list` (macOS)
- Check password in `server/app.py`
- Verify MySQL is on port 3306

### Port Already in Use
- Frontend: Change port `python3 -m http.server 8001`
- Backend: Change port in `server/app.py` line 358

### Module Not Found
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt` again

## 📱 Access from Phone/Other Devices

Find your local IP:
```bash
ifconfig | grep "inet "
```

Then access from other devices:
```
http://YOUR_IP:8000/login.html
```

## 🔥 Quick Commands

**Start everything:**
```bash
# Terminal 1 - Backend
cd server && source venv/bin/activate && python app.py

# Terminal 2 - Frontend  
cd public && python3 -m http.server 8000
```

**Stop everything:**
- Press `Ctrl+C` in both terminals
