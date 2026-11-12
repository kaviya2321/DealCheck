"""
Safe database migration script for DealCheck.
Creates new tables (users, invites, encrypted_messages) and adds missing columns
to the deals table without modifying or losing existing records.
"""
import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "dealcheck.db"

def run_migration():
    print(f"[Migration] Connecting to database at {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 1. Create users table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id VARCHAR(64) PRIMARY KEY,
        email VARCHAR(256) UNIQUE NOT NULL,
        hashed_password VARCHAR(256) NOT NULL,
        name VARCHAR(128) NOT NULL,
        created_at DATETIME,
        updated_at DATETIME
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_id ON users (id);")
    print("[Migration] Users table verified.")

    # 2. Create invites table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invites (
        id VARCHAR(64) PRIMARY KEY,
        deal_id VARCHAR(64) NOT NULL,
        token VARCHAR(64) UNIQUE NOT NULL,
        status VARCHAR(32) DEFAULT 'SENT',
        expires_at DATETIME NOT NULL,
        opened_at DATETIME,
        created_at DATETIME
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_invites_token ON invites (token);")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_invites_deal_id ON invites (deal_id);")
    print("[Migration] Invites table verified.")

    # 3. Create encrypted_messages table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS encrypted_messages (
        id VARCHAR(64) PRIMARY KEY,
        deal_id VARCHAR(64) NOT NULL,
        sender_id VARCHAR(64) NOT NULL,
        encrypted_content TEXT NOT NULL,
        message_type VARCHAR(32) DEFAULT 'chat',
        is_private_to_buyer INTEGER DEFAULT 0,
        created_at DATETIME
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_encrypted_messages_deal_id ON encrypted_messages (deal_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_encrypted_messages_sender_id ON encrypted_messages (sender_id);")
    print("[Migration] Encrypted messages table verified.")

    # 4. Check existing columns in deals table
    cursor.execute("PRAGMA table_info(deals);")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"[Migration] Existing deals columns: {len(columns)}")

    new_columns = [
        ("buyer_id", "VARCHAR(64)"),
        ("seller_id", "VARCHAR(64)"),
        ("status", "VARCHAR(32) DEFAULT 'ACTIVE'"),
        ("invite_token", "VARCHAR(64)"),
        ("buyer_agreed", "INTEGER DEFAULT 0"),
        ("seller_agreed", "INTEGER DEFAULT 0")
    ]

    for col_name, col_type in new_columns:
        if col_name not in columns:
            print(f"[Migration] Adding column {col_name} ({col_type}) to deals table...")
            cursor.execute(f"ALTER TABLE deals ADD COLUMN {col_name} {col_type};")

    conn.commit()
    conn.close()
    print("[Migration] All migrations completed successfully!")

if __name__ == "__main__":
    run_migration()
