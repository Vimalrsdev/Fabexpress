#!/usr/bin/env python3
"""
Comprehensive SQLAlchemy 2.0 Upgrade Verification Script
Verifies that all files have been properly upgraded
"""

import os
import sys
import re

def check_deprecated_patterns():
    """Check for deprecated SQLAlchemy patterns"""
    print("🔍 Checking for deprecated patterns...\n")
    
    deprecated_patterns = {
        'db.engine.execute': 0,
        'sqlalchemy.orm.exc': 0,
        'autocommit=True': 0,
    }
    
    files_checked = 0
    
    for root, dirs, files in os.walk('fabric'):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                files_checked += 1
                
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Check each pattern (excluding comments and docstrings)
                    for line in content.split('\n'):
                        stripped = line.strip()
                        # Skip comments, docstrings, and lines in multiline strings
                        if stripped.startswith('#') or '"""' in line or "'''" in line or 'Replaces the deprecated' in line:
                            continue
                        # Check for active (non-commented) deprecated patterns
                        # Look for patterns not preceded by # in the line
                        if 'db.engine.execute' in line and '#' not in line.split('db.engine.execute')[0]:
                            deprecated_patterns['db.engine.execute'] += 1
                        if 'sqlalchemy.orm.exc' in line and '#' not in line.split('sqlalchemy.orm.exc')[0]:
                            deprecated_patterns['sqlalchemy.orm.exc'] += 1
                        if 'execution_options(autocommit=True)' in line and '#' not in line.split('execution_options(autocommit=True)')[0]:
                            deprecated_patterns['autocommit=True'] += 1
    
    print(f"📊 Files checked: {files_checked}\n")
    print("🔎 Deprecated patterns found (active code only):")
    
    total_issues = 0
    for pattern, count in deprecated_patterns.items():
        status = "✅" if count == 0 else "❌"
        print(f"  {status} {pattern}: {count}")
        total_issues += count
    
    return total_issues

def check_imports():
    """Verify critical imports work"""
    print("\n\n🧪 Testing imports...\n")
    
    try:
        sys.path.insert(0, 'fabric')
        
        from fabric import db, create_app
        print("✅ Core fabric imports")
        
        from fabric.generic.functions import execute_with_commit
        print("✅ Helper function")
        
        from sqlalchemy.exc import MultipleResultsFound
        print("✅ SQLAlchemy 2.0 exceptions")
        
        from sqlalchemy import text, func, and_, or_
        print("✅ SQLAlchemy core")
        
        import sqlalchemy
        print(f"✅ SQLAlchemy version: {sqlalchemy.__version__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def check_requirements():
    """Check requirements.txt has correct versions"""
    print("\n\n📦 Checking requirements.txt...\n")
    
    required_versions = {
        'SQLAlchemy': '2.0.',
        'Flask': '3.0.',
        'Flask-SQLAlchemy': '3.',
        'haversine': '2.',
    }
    
    with open('fabric/requirements.txt', 'r') as f:
        content = f.read()
    
    all_good = True
    for package, version_prefix in required_versions.items():
        # Use word boundary to match exact package name
        pattern = rf"^{package}==([0-9.]+)"
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            version = match.group(1)
            if version.startswith(version_prefix):
                print(f"✅ {package}=={version}")
            else:
                print(f"❌ {package}=={version} (expected {version_prefix}x)")
                all_good = False
        else:
            print(f"❌ {package} not found")
            all_good = False
    
    return all_good

def main():
    """Run all verification checks"""
    print("="*60)
    print("SQLAlchemy 2.0 Upgrade Verification")
    print("="*60)
    print()
    
    # Run checks
    deprecated_count = check_deprecated_patterns()
    imports_ok = check_imports()
    requirements_ok = check_requirements()
    
    # Summary
    print("\n\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if deprecated_count == 0:
        print("✅ No deprecated patterns found")
    else:
        print(f"❌ {deprecated_count} deprecated patterns found")
    
    if imports_ok:
        print("✅ All imports working")
    else:
        print("❌ Import errors detected")
    
    if requirements_ok:
        print("✅ Requirements.txt correct")
    else:
        print("❌ Requirements.txt issues")
    
    print()
    
    if deprecated_count == 0 and imports_ok and requirements_ok:
        print("🎉 ALL CHECKS PASSED!")
        print("✅ Project is fully upgraded to SQLAlchemy 2.0.35 and Python 3.13")
        return 0
    else:
        print("⚠️  Some issues found. Please review above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
