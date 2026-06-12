import asyncio
import asyncpg

async def main():
    try:
        print("Connecting to default postgres database...")
        conn = await asyncpg.connect("postgresql://postgres:Stek2003006.1234@localhost:5432/postgres")
        
        # Check if database exists
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'fhir_transformer'")
        
        if not exists:
            print("Database fhir_transformer does not exist. Creating...")
            await conn.execute("CREATE DATABASE fhir_transformer")
            print("Database created successfully.")
        else:
            print("Database fhir_transformer already exists.")
            
        await conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")

if __name__ == "__main__":
    asyncio.run(main())
