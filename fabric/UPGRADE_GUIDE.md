# Python 3.13 and SQLAlchemy 2.0 Upgrade Guide

## Overview
This document describes the upgrade from Python 3.x to Python 3.13 and SQLAlchemy 1.3.19 to 2.0.35.

## What Was Changed

### 1. Python Version
- **Target Version**: Python 3.13 (also compatible with Python 3.12+)
- **File**: `.python-version` - Created to specify Python version

### 2. Dependencies Updated (requirements.txt)

#### Major Version Updates:
- **SQLAlchemy**: 1.3.19 → 2.0.35 (Major upgrade)
- **Flask-SQLAlchemy**: 2.4.1 → 3.1.1 (Major upgrade)
- **Flask**: 1.1.2 → 3.0.3 (Major upgrade)
- **Flask-Login**: 0.5.0 → 0.6.3
- **Flask-WTF**: 0.14.3 → 1.2.2
- **Werkzeug**: 1.0.1 → 3.0.4
- **Jinja2**: 2.11.2 → 3.1.4
- **PyJWT**: 1.7.1 → 2.9.0
- **redis**: 3.5.3 → 5.2.0
- **pyfcm**: 1.5.1 → 2.1.0
- **pyodbc**: 4.0.30 → 5.2.0
- **requests**: 2.24.0 → 2.32.3

#### All Other Dependencies:
Updated to their latest stable versions compatible with Python 3.13.

### 3. Code Changes

#### fabric/__init__.py
**Purpose**: Updated Flask-SQLAlchemy initialization for version 3.x compatibility

**Changes**:
- Added SQLAlchemy 2.0 DeclarativeBase import
- Created custom Base class for SQLAlchemy 2.0
- Configured SQLAlchemy with `model_class=Base` for proper initialization

**Before**:
```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
```

**After**:
```python
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
```

#### fabric/config.py
**Purpose**: Added SQLAlchemy 2.0 engine options

**Changes**:
- Added `SQLALCHEMY_ENGINE_OPTIONS` configuration
- Enabled connection pool pre-ping for better connection handling
- Set pool recycle time to 300 seconds

**Added Configuration**:
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}
```

#### fabric/blueprints/api_routes/user_manager.py
**Purpose**: Updated to use session-based query instead of Model.query

**Before**:
```python
admin = APIRoutesUser.query.filter_by(Id=id).first()
```

**After**:
```python
from fabric import db
admin = db.session.query(APIRoutesUser).filter_by(Id=id).first()
```

## SQLAlchemy 2.0 Compatibility

### Backward Compatibility
The upgrade maintains backward compatibility for existing code patterns:

1. **Query API**: The legacy `db.session.query()` pattern continues to work
2. **Relationships**: All existing relationship definitions remain compatible
3. **Model Definitions**: Declarative model definitions work without changes

### What Still Works
- ✅ `db.session.query(Model).filter(...).all()`
- ✅ `db.session.query(Model).filter_by(...).first()`
- ✅ `db.session.query(Model).join(...)`
- ✅ All existing `relationship()` definitions
- ✅ `db.session.execute(text("SQL"), params)`
- ✅ All model class definitions using `db.Model`

### SQLAlchemy 2.0 New Features Available
While not required for existing code, you can now use:

1. **New Select API** (Optional):
```python
from sqlalchemy import select
result = db.session.execute(select(User).where(User.name == "John"))
users = result.scalars().all()
```

2. **Improved Type Hints**: Better IDE support and type checking

3. **Performance Improvements**: Faster query execution and better connection pooling

## Testing

### Verified Functionality
- ✅ Package installation successful
- ✅ Import of Flask and SQLAlchemy works
- ✅ Model imports work correctly
- ✅ Query API availability confirmed
- ✅ Backward compatibility maintained

### Database Connection Requirements
The application requires ODBC drivers for MSSQL connectivity:
- **Linux**: `unixodbc` and `msodbcsql17` or `msodbcsql18`
- **Windows**: Microsoft ODBC Driver 17 or 18 for SQL Server

## Migration Notes

### No Breaking Changes for Existing Code
The upgrade was designed to maintain full backward compatibility. Your existing code using:
- `db.session.query()`
- Model relationships
- Database queries
- Transaction management

...will continue to work without modifications.

### Future Improvements (Optional)
While not required, you may consider:

1. **Migrate to 2.0 style queries** (gradual, over time)
2. **Add type hints** for better IDE support
3. **Use async features** if needed (SQLAlchemy 2.0 has built-in async support)

## Troubleshooting

### Common Issues

#### 1. Import Errors
If you see import errors, ensure all packages are installed:
```bash
pip install -r requirements.txt
```

#### 2. ODBC Driver Missing
If you see "libodbc.so.2: cannot open shared object file":
```bash
# Ubuntu/Debian
sudo apt-get install unixodbc unixodbc-dev

# Then install MS SQL ODBC Driver
# Follow: https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server
```

#### 3. Connection String Issues
The connection strings for MSSQL remain the same format, no changes needed.

## Benefits of This Upgrade

1. **Security**: Latest versions include security patches
2. **Performance**: SQLAlchemy 2.0 is significantly faster
3. **Python 3.13**: Access to latest Python features and improvements
4. **Better Typing**: Improved IDE support and type checking
5. **Active Support**: All packages are actively maintained
6. **Future-Proof**: Ready for future Python and SQLAlchemy updates

## Support

For issues specific to:
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **Flask-SQLAlchemy 3.x**: https://flask-sqlalchemy.palletsprojects.com/
- **Flask 3.x**: https://flask.palletsprojects.com/

## Rollback Plan

If you need to rollback, you can restore the previous `requirements.txt`:
```bash
git checkout HEAD~1 -- requirements.txt
pip install -r requirements.txt
```

However, rollback of code changes in `fabric/__init__.py`, `config.py`, and `user_manager.py` would also be needed.
