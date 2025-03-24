import psycopg2
from psycopg2 import sql

# Step 1: Connect as the 'postgres' user to check/create the database
conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="postgres",  # Replace with the password for the 'postgres' user
    host="localhost"
)
conn.autocommit = True

# Check if the database already exists
cursor = conn.cursor()
cursor.execute("""
    SELECT 1 FROM pg_database WHERE datname = 'ec2_manager';
""")
database_exists = cursor.fetchone()

if not database_exists:
    # Create the database if it does not exist
    cursor.execute("CREATE DATABASE ec2_manager;")
else:
    print("Database 'ec2_manager' already exists. Skipping creation.")

cursor.close()
conn.close()

# Step 2: Connect as 'ec2_user' to create the table
conn = psycopg2.connect(
    dbname="ec2_manager",
    user="ec2_user",
    password="aws",  # Password for 'ec2_user'
    host="localhost"
)
cursor = conn.cursor()

# Check if the table already exists
cursor.execute("""
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'instances'
    );
""")
table_exists = cursor.fetchone()[0]

if not table_exists:
    # Create the table if it does not exist
    cursor.execute("""
    CREATE TABLE instances (
        id SERIAL PRIMARY KEY,
        instance_name VARCHAR(255),
        instance_id VARCHAR(255),
        public_ip VARCHAR(255),
        ports VARCHAR(255),
        username VARCHAR(255),
        password VARCHAR(255),
        auto_terminate_time INTEGER
    );
    """)
    print("Table 'instances' created successfully.")
else:
    print("Table 'instances' already exists. Skipping creation.")

conn.commit()
cursor.close()
conn.close()
