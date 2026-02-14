"""
Test Neon Database Connection

Verifies connection to Neon PostgreSQL database
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("="*70)
print("  NEON DATABASE CONNECTION TEST")
print("="*70)
print()

# Check DATABASE_URL
database_url = os.getenv('DATABASE_URL')

if not database_url:
    print("❌ DATABASE_URL not found in .env file")
    print()
    print("Please update .env file with your Neon connection string.")
    print("Get it from: https://console.neon.tech")
    print()
    print("Your Neon details:")
    print("  Organization: org-ancient-wildflower-07117017")
    print("  Project: tiny-hall-51975564")
    exit(1)

print(f"✓ DATABASE_URL found")
print(f"  Database: {database_url.split('@')[1].split('/')[1].split('?')[0] if '@' in database_url else 'Unknown'}")
print(f"  Host: {database_url.split('@')[1].split('/')[0] if '@' in database_url else 'Unknown'}")
print()

# Test connection
print("🔌 Testing connection...")

try:
    from app.neon_config import get_connection_manager
    
    manager = get_connection_manager()
    
    # Test connection
    if manager.test_connection():
        print("✅ Connection successful!")
        print()
        
        # Get connection info
        info = manager.get_connection_info()
        
        print("📊 Database Information:")
        print(f"  PostgreSQL Version: {info.get('postgresql_version', 'N/A')}")
        print(f"  Database: {info.get('database', 'N/A')}")
        print(f"  User: {info.get('user', 'N/A')}")
        print(f"  Server: {info.get('server_address', 'N/A')}:{info.get('server_port', 'N/A')}")
        print(f"  Pool Size: {info.get('pool_size', 'N/A')}")
        print(f"  SSL Mode: {info.get('ssl_mode', 'N/A')}")
        print()
        
        # Check tables
        from sqlalchemy import text, inspect
        
        with manager.engine.connect() as conn:
            # Get all tables
            inspector = inspect(manager.engine)
            tables = inspector.get_table_names()
            
            print(f"📋 Tables ({len(tables)}):")
            if tables:
                for table in tables:
                    # Get row count
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"  ✓ {table}: {count} rows")
            else:
                print("  (No tables found - database needs to be initialized)")
        
        print()
        print("="*70)
        print("✅ Neon database is ready!")
        print("="*70)
        
    else:
        print("❌ Connection failed - check your DATABASE_URL")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
    print()
    print("Common issues:")
    print("  1. Invalid connection string format")
    print("  2. Wrong username/password")
    print("  3. Database doesn't exist")
    print("  4. Network/firewall issues")
    print()
    print("Make sure your DATABASE_URL in .env is correct.")
