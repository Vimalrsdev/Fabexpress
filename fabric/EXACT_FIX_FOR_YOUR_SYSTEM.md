# EXACT FIX FOR YOUR SYSTEM

## Your System Configuration

```
Python 3.13: C:\Users\JFSL1234\AppData\Local\Programs\Python\Python313\python.exe ✅ (FIRST in PATH)
Python 3.8:  C:\Users\JFSL1234\AppData\Local\Programs\Python\Python38\python.exe  ❌ (Apache using this)
```

**Problem:** Apache is using Python 3.8, but you want Python 3.13

---

## 🚀 SOLUTION: Copy-Paste These Commands

### Step 1: Install Dependencies in Python 3.13 (2 minutes)

```cmd
REM Go to your project directory
cd C:\jfsl_cloud\prod\fabric

REM Install packages using Python 3.13 specifically
C:\Users\JFSL1234\AppData\Local\Programs\Python\Python313\python.exe -m pip install --upgrade pip
C:\Users\JFSL1234\AppData\Local\Programs\Python\Python313\python.exe -m pip install -r requirements.txt

REM Verify installation
C:\Users\JFSL1234\AppData\Local\Programs\Python\Python313\python.exe -m pip show sqlalchemy
```

### Step 2: Reinstall mod_wsgi for Python 3.13 (3 minutes)

```cmd
REM Uninstall old mod_wsgi (if exists)
C:\Users\JFSL1234\AppData\Local\Programs\Python\Python313\python.exe -m pip uninstall mod-wsgi -y

REM Install mod_wsgi for Python 3.13
C:\Users\JFSL1234\AppData\Local\Programs\Python\Python313\python.exe -m pip install mod-wsgi

REM Get Apache configuration for Python 3.13
C:\Users\JFSL1234\AppData\Local\Programs\Python\Python313\python.exe -m mod_wsgi-express module-config
```

**COPY THE OUTPUT** - You'll need it for Step 3!

### Step 3: Update Apache Configuration (5 minutes)

The command above will show something like:

```apache
LoadFile "c:/users/jfsl1234/appdata/local/programs/python/python313/python313.dll"
LoadModule wsgi_module "c:/users/jfsl1234/appdata/local/programs/python/python313/lib/site-packages/mod_wsgi/server/mod_wsgi.cp313-win_amd64.pyd"
WSGIPythonHome "c:/users/jfsl1234/appdata/local/programs/python/python313"
```

#### Find your Apache config file:
- Usually: `C:\Apache24\conf\httpd.conf`
- Or: `C:\Apache24\conf\extra\httpd-vhosts.conf`

#### Replace OLD lines (Python 3.8):
```apache
LoadFile "c:/users/jfsl1234/appdata/local/programs/python/python38/python38.dll"
LoadModule wsgi_module "...python38...mod_wsgi..."
WSGIPythonHome "c:/users/jfsl1234/appdata/local/programs/python/python38"
```

#### With NEW lines (Python 3.13):
Use the output from Step 2!

### Step 4: Pull Latest Code (1 minute)

```cmd
cd C:\jfsl_cloud\prod\fabric
git pull origin cursor/upgrade-python-and-sqlalchemy-to-latest-6306
```

### Step 5: Restart Apache (1 minute)

```cmd
net stop Apache2.4
net start Apache2.4
```

### Step 6: Verify (1 minute)

```cmd
REM Check Apache error log - should have NO errors
type C:\Apache24\logs\error.log

REM Test your application
curl http://localhost
```

---

## ⚡ ALTERNATIVE: Quick Workaround (If you can't change Apache config)

If you **cannot modify Apache config right now**, add this to the TOP of `C:\jfsl_cloud\prod\fabric\wsgi.py`:

```python
import sys
import os

# Force Python 3.13 paths
python313_path = r'C:\Users\JFSL1234\AppData\Local\Programs\Python\Python313'
python313_lib = os.path.join(python313_path, 'Lib')
python313_site = os.path.join(python313_lib, 'site-packages')

# Remove ALL Python 3.8 references
sys.path = [p for p in sys.path if 'python38' not in p.lower() and 'python3.8' not in p.lower()]

# Add Python 3.13 at the START
sys.path.insert(0, python313_site)
sys.path.insert(0, python313_lib)
sys.path.insert(0, python313_path)

# Application path
sys.path.insert(0, r'C:\jfsl_cloud\prod\fabric')

# NOW import (after path is fixed)
from fabric import create_app
application = create_app()
```

Then:
```cmd
REM Install packages in Python 3.13
C:\Users\JFSL1234\AppData\Local\Programs\Python\Python313\python.exe -m pip install -r C:\jfsl_cloud\prod\fabric\requirements.txt

REM Pull latest code
cd C:\jfsl_cloud\prod\fabric
git pull origin cursor/upgrade-python-and-sqlalchemy-to-latest-6306

REM Restart Apache
net stop Apache2.4
net start Apache2.4
```

---

## ✅ After Fix - Verify Python Version

Add this temporary route to test (in `fabric/__init__.py`):

```python
@app.route('/test-python')
def test_python():
    import sys
    import sqlalchemy
    import flask
    return {
        'python_version': sys.version,
        'python_path': sys.executable,
        'sqlalchemy_version': sqlalchemy.__version__,
        'flask_version': flask.__version__,
        'sys_path': sys.path[:5]
    }
```

Access: `http://your-domain/test-python`

**Should show:**
```json
{
  "python_version": "3.13.x ...",
  "sqlalchemy_version": "2.0.35",
  "flask_version": "3.0.3"
}
```

---

## 🎯 Recommended: Do Step 1, 2, 3, 4, 5

This properly fixes Apache to use Python 3.13. Takes about 10-15 minutes total.

**Benefits:**
- ✅ Correct Python version
- ✅ Better performance  
- ✅ No workarounds needed
- ✅ Clean setup

---

## 📞 If You Get Stuck

**Common Issue:** "Cannot find httpd.conf"

**Solution:** Check these locations:
```cmd
dir C:\Apache24\conf\httpd.conf
dir C:\Apache\conf\httpd.conf
dir C:\xampp\apache\conf\httpd.conf
dir "C:\Program Files\Apache Software Foundation\Apache2.4\conf\httpd.conf"
```

**Common Issue:** "Apache won't start after config change"

**Solution:** Check syntax
```cmd
C:\Apache24\bin\httpd.exe -t
```

If errors, revert the config and try again.

---

## 🎉 Summary

**What to do:**
1. Install packages in Python 3.13 ✅
2. Reinstall mod_wsgi for Python 3.13 ✅
3. Update Apache config ✅
4. Pull latest code ✅
5. Restart Apache ✅

**Time needed:** 10-15 minutes

**Result:** Apache uses Python 3.13 with SQLAlchemy 2.0.35 ✅

Your application will work perfectly!
