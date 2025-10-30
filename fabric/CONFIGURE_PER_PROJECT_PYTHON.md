# Configure Python 3.13 for One Project Only

## 🎯 Problem: Multiple Projects on Same Server

You have:
- **This project** (Fabric) - Needs Python 3.13 + SQLAlchemy 2.0
- **Other projects** - Currently using Python 3.8 (don't want to break them!)

**Solution:** Use `WSGIDaemonProcess` to run this project in its own Python environment!

---

## ✅ SOLUTION: Per-Project Python Configuration

### Step 1: Install Packages in Python 3.13 (ONLY for this project)

```cmd
cd C:\jfsl_cloud\prod\fabric

REM Install in Python 3.13
C:\Users\JFSL1234\AppData\Local\Programs\Python\Python313\python.exe -m pip install -r requirements.txt

REM Verify
C:\Users\JFSL1234\AppData\Local\Programs\Python\Python313\python.exe -m pip show sqlalchemy
```

### Step 2: Pull Latest Code

```cmd
cd C:\jfsl_cloud\prod\fabric
git pull origin cursor/upgrade-python-and-sqlalchemy-to-latest-6306
```

### Step 3: Configure Apache VirtualHost for THIS Project ONLY

#### Option A: Separate VirtualHost File (Recommended)

Create/Edit: `C:\Apache24\conf\extra\fabric-vhost.conf`

```apache
<VirtualHost *:80>
    ServerName your-fabric-domain.com
    ServerAlias www.your-fabric-domain.com
    
    # Project-specific Python 3.13 Daemon Process
    WSGIDaemonProcess fabric \
        python-home=C:/Users/JFSL1234/AppData/Local/Programs/Python/Python313 \
        python-path=C:/jfsl_cloud/prod/fabric \
        processes=2 \
        threads=15 \
        display-name=%{GROUP}
    
    # Use this daemon process for this project ONLY
    WSGIProcessGroup fabric
    
    # Application entry point
    WSGIScriptAlias / C:/jfsl_cloud/prod/fabric/wsgi.py
    
    # Directory permissions
    <Directory C:/jfsl_cloud/prod/fabric>
        WSGIProcessGroup fabric
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>
    
    # Logs
    ErrorLog "logs/fabric-error.log"
    CustomLog "logs/fabric-access.log" combined
</VirtualHost>
```

**Include this file in main httpd.conf:**
```apache
# At the end of httpd.conf
Include conf/extra/fabric-vhost.conf
```

#### Option B: Add to Existing VirtualHost

If you already have a VirtualHost for this project, **just add** these lines:

```apache
<VirtualHost *:80>
    ServerName your-fabric-domain.com
    
    # ADD THESE LINES for Python 3.13
    WSGIDaemonProcess fabric \
        python-home=C:/Users/JFSL1234/AppData/Local/Programs/Python/Python313 \
        python-path=C:/jfsl_cloud/prod/fabric \
        processes=2 \
        threads=15
    
    WSGIProcessGroup fabric
    
    # Your existing WSGIScriptAlias
    WSGIScriptAlias / C:/jfsl_cloud/prod/fabric/wsgi.py
    
    <Directory C:/jfsl_cloud/prod/fabric>
        WSGIProcessGroup fabric
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>
    
    # ... rest of your existing config ...
</VirtualHost>
```

### Step 4: Keep Other Projects Unchanged

**Other projects remain EXACTLY as they are:**

```apache
# Other project 1 - Still uses Python 3.8
<VirtualHost *:80>
    ServerName other-project1.com
    WSGIDaemonProcess project1 python-home=C:/Users/JFSL1234/AppData/Local/Programs/Python/Python38
    WSGIProcessGroup project1
    WSGIScriptAlias / C:/path/to/project1/wsgi.py
    # ... etc ...
</VirtualHost>

# Other project 2 - Still uses Python 3.8
<VirtualHost *:80>
    ServerName other-project2.com
    WSGIDaemonProcess project2 python-home=C:/Users/JFSL1234/AppData/Local/Programs/Python/Python38
    WSGIProcessGroup project2
    WSGIScriptAlias / C:/path/to/project2/wsgi.py
    # ... etc ...
</VirtualHost>
```

### Step 5: Restart Apache

```cmd
REM Test configuration first
C:\Apache24\bin\httpd.exe -t

REM If OK, restart
net stop Apache2.4
net start Apache2.4
```

---

## 🎯 How It Works

### WSGIDaemonProcess Explanation

```apache
WSGIDaemonProcess fabric \              # Unique name for this project
    python-home=C:/.../Python313 \      # Python 3.13 for THIS project only
    python-path=C:/jfsl_cloud/prod/fabric \  # Project path
    processes=2 \                        # Number of processes
    threads=15                           # Threads per process
```

**Key Points:**
- ✅ Each `WSGIDaemonProcess` is **isolated**
- ✅ Different projects can use **different Python versions**
- ✅ Projects **don't interfere** with each other
- ✅ No global Apache changes needed

---

## 📋 Complete Example Configuration

### Main httpd.conf (NO CHANGES to global settings!)

```apache
# httpd.conf - Keep existing global mod_wsgi settings
LoadFile "c:/users/jfsl1234/appdata/local/programs/python/python38/python38.dll"
LoadModule wsgi_module "c:/users/jfsl1234/.../python38/.../mod_wsgi.pyd"

# Include project-specific configs
Include conf/extra/fabric-vhost.conf
Include conf/extra/other-projects.conf
```

### fabric-vhost.conf (THIS PROJECT - Python 3.13)

```apache
<VirtualHost *:80>
    ServerName fabric.yourdomain.com
    
    # Python 3.13 for Fabric project ONLY
    WSGIDaemonProcess fabric \
        python-home=C:/Users/JFSL1234/AppData/Local/Programs/Python/Python313 \
        python-path=C:/jfsl_cloud/prod/fabric \
        processes=2 \
        threads=15 \
        display-name=fabric-wsgi
    
    WSGIProcessGroup fabric
    WSGIScriptAlias / C:/jfsl_cloud/prod/fabric/wsgi.py
    
    <Directory C:/jfsl_cloud/prod/fabric>
        WSGIProcessGroup fabric
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>
    
    ErrorLog "logs/fabric-error.log"
    CustomLog "logs/fabric-access.log" combined
</VirtualHost>
```

### other-projects.conf (OTHER PROJECTS - Python 3.8)

```apache
# Project 1 - Python 3.8
<VirtualHost *:80>
    ServerName project1.yourdomain.com
    
    WSGIDaemonProcess project1 \
        python-home=C:/Users/JFSL1234/AppData/Local/Programs/Python/Python38 \
        python-path=C:/path/to/project1
    
    WSGIProcessGroup project1
    WSGIScriptAlias / C:/path/to/project1/wsgi.py
    
    <Directory C:/path/to/project1>
        WSGIProcessGroup project1
        Require all granted
    </Directory>
</VirtualHost>

# Project 2 - Python 3.8
<VirtualHost *:80>
    ServerName project2.yourdomain.com
    
    WSGIDaemonProcess project2 \
        python-home=C:/Users/JFSL1234/AppData/Local/Programs/Python/Python38 \
        python-path=C:/path/to/project2
    
    WSGIProcessGroup project2
    WSGIScriptAlias / C:/path/to/project2/wsgi.py
    
    <Directory C:/path/to/project2>
        WSGIProcessGroup project2
        Require all granted
    </Directory>
</VirtualHost>
```

---

## ✅ Benefits of This Approach

| Benefit | Description |
|---------|-------------|
| **Isolated** | Each project has its own Python environment |
| **Safe** | Other projects continue working unchanged |
| **Flexible** | Different Python versions per project |
| **No Downtime** | Other projects keep running during changes |
| **Easy Rollback** | Just remove/change one VirtualHost |
| **Performance** | Each project optimized independently |

---

## 🔍 Verify Configuration

### Check Configuration Syntax

```cmd
C:\Apache24\bin\httpd.exe -t
```

Should show: `Syntax OK`

### Check Which Python Each Project Uses

Add to each project's wsgi.py (temporarily):

```python
import sys
import logging

logging.basicConfig(filename='C:/temp/python-check.log', level=logging.INFO)
logging.info(f'Project using Python: {sys.version}')
logging.info(f'Python path: {sys.executable}')

# ... rest of wsgi.py ...
```

### Test Each Project Separately

```cmd
REM Test Fabric project (should use Python 3.13)
curl http://fabric.yourdomain.com/test-endpoint

REM Test other projects (should still work with Python 3.8)
curl http://project1.yourdomain.com/
curl http://project2.yourdomain.com/
```

---

## 🚨 Common Issues & Solutions

### Issue 1: "WSGIDaemonProcess not allowed here"

**Cause:** WSGIDaemonProcess must be in VirtualHost or server config, not in Directory

**Fix:** Move it outside `<Directory>` block

### Issue 2: "No module named 'fabric'"

**Cause:** `python-path` not set correctly

**Fix:**
```apache
WSGIDaemonProcess fabric \
    python-home=C:/Users/JFSL1234/AppData/Local/Programs/Python/Python313 \
    python-path=C:/jfsl_cloud/prod/fabric  # <-- Add this parent directory
```

### Issue 3: "Cannot find Python313.dll"

**Cause:** `python-home` path incorrect

**Fix:** Verify path:
```cmd
dir C:\Users\JFSL1234\AppData\Local\Programs\Python\Python313\python313.dll
```

Use exact path in config.

### Issue 4: Other projects stopped working

**Cause:** You changed global LoadModule instead of using daemon process

**Fix:** Keep global LoadModule as Python 3.8, use WSGIDaemonProcess for per-project Python

---

## 📊 Configuration Comparison

### ❌ Bad Approach (Affects All Projects)
```apache
# DON'T DO THIS - Changes for ALL projects!
LoadFile "c:/.../python313/python313.dll"
LoadModule wsgi_module "c:/.../python313/.../mod_wsgi.pyd"
WSGIPythonHome "c:/.../python313"
```

### ✅ Good Approach (Per-Project)
```apache
# Global (for older projects)
LoadFile "c:/.../python38/python38.dll"
LoadModule wsgi_module "c:/.../python38/.../mod_wsgi.pyd"

# Per-project configuration
<VirtualHost *:80>
    WSGIDaemonProcess fabric python-home=C:/.../Python313  # Only this project!
    WSGIProcessGroup fabric
    # ...
</VirtualHost>
```

---

## 🎯 Quick Setup Checklist

- [ ] Install packages in Python 3.13 for this project
- [ ] Pull latest code from git
- [ ] Create/update VirtualHost config with WSGIDaemonProcess
- [ ] Set `python-home` to Python 3.13 path
- [ ] Set `python-path` to project directory
- [ ] Keep other projects' configs unchanged
- [ ] Test configuration: `httpd -t`
- [ ] Restart Apache
- [ ] Test this project (Python 3.13)
- [ ] Test other projects (Python 3.8)
- [ ] Monitor logs for both

---

## 🎉 Result

After configuration:

```
Fabric Project:    Python 3.13 + SQLAlchemy 2.0.35 ✅
Other Project 1:   Python 3.8  + Old packages       ✅
Other Project 2:   Python 3.8  + Old packages       ✅
Other Project N:   Python 3.8  + Old packages       ✅
```

**All projects run independently with their own Python versions!**

---

## 📞 Need Help?

If you run into issues:

1. Check Apache error log: `C:\Apache24\logs\error.log`
2. Check project-specific log: `C:\Apache24\logs\fabric-error.log`
3. Verify Python path: `where python`
4. Test configuration: `httpd -t`
5. Check process is running: `netstat -ano | findstr :80`

---

## 💡 Pro Tips

1. **Use unique names** for each WSGIDaemonProcess (fabric, project1, project2, etc.)
2. **Separate log files** per project for easier debugging
3. **Test one project at a time** when making changes
4. **Keep backups** of working configs before changes
5. **Document** which Python version each project uses

---

## ✅ Summary

**Question:** Can I configure mod_wsgi for one project only?  
**Answer:** YES! Use `WSGIDaemonProcess` with project-specific `python-home`

**This project:** Python 3.13 ✅  
**Other projects:** Python 3.8 ✅  
**No conflicts:** Each project isolated ✅

Perfect solution for your multi-project server!
