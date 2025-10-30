# Fix Apache mod_wsgi Python Version Issue

## 🚨 Problem Identified

**Your System:** Python 3.13 installed  
**Apache/mod_wsgi Using:** Python 3.8

**Error Path Shows:**
```
c:\users\jfsl1234\appdata\local\programs\python\python38\lib\site-packages\sqlalchemy\orm\__init__.py
```

This means Apache's mod_wsgi is compiled for/pointing to Python 3.8, not Python 3.13!

---

## ✅ Solution: Update mod_wsgi to Use Python 3.13

### Option 1: Reinstall mod_wsgi for Python 3.13 (Recommended)

#### Step 1: Uninstall Current mod_wsgi
```bash
pip uninstall mod-wsgi
```

#### Step 2: Install mod_wsgi with Python 3.13
```bash
# Make sure you're using Python 3.13
python --version  # Should show 3.13.x

# Install mod_wsgi
pip install mod-wsgi

# Generate Apache configuration
mod_wsgi-express module-config
```

#### Step 3: Update Apache Configuration
The `mod_wsgi-express module-config` command will output something like:
```apache
LoadFile "c:/users/jfsl1234/appdata/local/programs/python/python313/python313.dll"
LoadModule wsgi_module "c:/path/to/python313/site-packages/mod_wsgi/server/mod_wsgi.cp313-win_amd64.pyd"
WSGIPythonHome "c:/users/jfsl1234/appdata/local/programs/python/python313"
```

Add these lines to your Apache config (usually `httpd.conf` or in `conf.d/`).

---

### Option 2: Update Apache WSGI Configuration

#### Check Current Configuration

Find your Apache configuration file (typically `C:\Apache24\conf\httpd.conf`) and look for:

```apache
LoadFile "c:/users/jfsl1234/appdata/local/programs/python/python38/python38.dll"
LoadModule wsgi_module "..."
WSGIPythonHome "c:/users/jfsl1234/appdata/local/programs/python/python38"
```

#### Update to Python 3.13

Replace with:
```apache
LoadFile "c:/users/jfsl1234/appdata/local/programs/python/python313/python313.dll"
LoadModule wsgi_module "c:/users/jfsl1234/appdata/local/programs/python/python313/site-packages/mod_wsgi/server/mod_wsgi.cp313-win_amd64.pyd"
WSGIPythonHome "c:/users/jfsl1234/appdata/local/programs/python/python313"
```

**Note:** Adjust paths based on your actual Python 3.13 installation location.

---

### Option 3: Update Your wsgi.py Configuration

#### Update wsgi.py File

Edit `C:/jfsl_cloud/prod/fabric/wsgi.py`:

```python
import sys
import os

# Force Python 3.13 path (adjust to your actual path)
python313_path = r'C:\Users\jfsl1234\AppData\Local\Programs\Python\Python313'
python313_site = os.path.join(python313_path, 'Lib', 'site-packages')

# Remove old Python 3.8 paths
sys.path = [p for p in sys.path if 'python38' not in p.lower()]

# Add Python 3.13 paths at the beginning
sys.path.insert(0, python313_site)
sys.path.insert(0, python313_path)

# Add your application path
sys.path.insert(0, r'C:\jfsl_cloud\prod\fabric')

# Continue with rest of wsgi.py...
from fabric import create_app
application = create_app()
```

---

## 🔍 Diagnostic Commands

### Check Which Python Apache is Using

Create a test WSGI file (`test_python.py`):

```python
def application(environ, start_response):
    import sys
    output = f"Python Version: {sys.version}\n"
    output += f"Python Path: {sys.executable}\n"
    output += f"sys.path:\n"
    for p in sys.path:
        output += f"  {p}\n"
    
    status = '200 OK'
    headers = [('Content-type', 'text/plain')]
    start_response(status, headers)
    return [output.encode('utf-8')]
```

Access it via browser to see which Python Apache is actually using.

### Verify Python 3.13 Installation

```cmd
# Check Python 3.13 is installed
where python
python --version

# Check if Python 3.13 has required packages
py -3.13 -m pip list | findstr SQLAlchemy
py -3.13 -m pip list | findstr Flask
```

### Install Packages in Python 3.13

```cmd
# Use Python 3.13 specifically
py -3.13 -m pip install -r C:\jfsl_cloud\prod\fabric\requirements.txt

# Or if python command points to 3.13
cd C:\jfsl_cloud\prod\fabric
python -m pip install -r requirements.txt
```

---

## 📋 Step-by-Step Fix Guide

### Quick Fix (5 minutes):

1. **Stop Apache**
   ```cmd
   net stop Apache2.4
   ```

2. **Install packages in Python 3.13**
   ```cmd
   py -3.13 -m pip install -r C:\jfsl_cloud\prod\fabric\requirements.txt
   ```

3. **Update wsgi.py** (add Python 3.13 path at top)

4. **Start Apache**
   ```cmd
   net start Apache2.4
   ```

### Proper Fix (30 minutes):

1. **Reinstall mod_wsgi for Python 3.13**
   ```cmd
   py -3.13 -m pip install mod-wsgi
   py -3.13 -m mod_wsgi-express module-config
   ```

2. **Update Apache configuration** with output from above

3. **Restart Apache**

4. **Verify** via test script

---

## 🎯 Recommended Solution

Since you have Python 3.13 and want to use it:

### 1. Install Dependencies in Python 3.13

```cmd
cd C:\jfsl_cloud\prod\fabric
py -3.13 -m pip install --upgrade pip
py -3.13 -m pip install -r requirements.txt
```

### 2. Update Apache to Use Python 3.13 mod_wsgi

```cmd
# Install mod_wsgi for Python 3.13
py -3.13 -m pip install mod-wsgi

# Get Apache configuration
py -3.13 -m mod_wsgi-express module-config
```

Copy the output and update your Apache configuration files.

### 3. Update Virtual Host Configuration

In your Apache virtual host config:

```apache
<VirtualHost *:80>
    ServerName your-domain.com
    
    # Use Python 3.13
    WSGIPythonHome "C:/Users/jfsl1234/AppData/Local/Programs/Python/Python313"
    WSGIScriptAlias / "C:/jfsl_cloud/prod/fabric/wsgi.py"
    
    <Directory "C:/jfsl_cloud/prod/fabric">
        Require all granted
    </Directory>
</VirtualHost>
```

### 4. Restart Apache

```cmd
net stop Apache2.4
net start Apache2.4
```

---

## 🔧 Troubleshooting

### Still Getting Python 3.8 Error?

**Check:**
1. Which Python is in system PATH?
   ```cmd
   where python
   echo %PATH%
   ```

2. Is virtual environment activated?
   ```cmd
   # Check if venv is active
   echo %VIRTUAL_ENV%
   ```

3. Which mod_wsgi is loaded?
   ```cmd
   py -3.13 -m pip show mod-wsgi
   ```

### Apache Won't Start?

**Common Issues:**
1. **Wrong DLL path** - Verify Python 3.13 DLL location
2. **Missing mod_wsgi** - Reinstall for Python 3.13
3. **Path conflicts** - Remove Python 3.8 from PATH temporarily

---

## ✅ Verification

After fixing, verify:

```cmd
# 1. Check Apache error log (should have no Python 3.8 references)
type C:\Apache24\logs\error.log

# 2. Access your application
curl http://localhost/

# 3. Create test endpoint that shows Python version
```

Add to your Flask app:
```python
@app.route('/python-info')
def python_info():
    import sys
    return {
        'python_version': sys.version,
        'python_path': sys.executable,
        'sqlalchemy_version': sqlalchemy.__version__
    }
```

Access `/python-info` and verify it shows Python 3.13.

---

## 🎉 Expected Result

After fixing, you should see:
```
Python 3.13.x
SQLAlchemy 2.0.35
Flask 3.0.3
```

And the application will work with full SQLAlchemy 2.0 features!

---

## 📞 If Issues Persist

The backward compatible code I provided will still work, but for optimal performance with Python 3.13, you should configure Apache to use the correct Python version.

**Key Point:** The code now works with BOTH scenarios:
- ✅ Python 3.8 + SQLAlchemy 1.x (current Apache config)
- ✅ Python 3.13 + SQLAlchemy 2.0.35 (after fix)

Choose which environment you want to fix.
