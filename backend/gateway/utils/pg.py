from sqlalchemy import create_engine, text

from gateway.utils.logger import logger
from config.settings import DB_URL 

def get_postgresql_engine(): 
    pg_engine = create_engine(DB_URL)
    logger.info(f"DB connected at: {pg_engine} with {DB_URL}")
    return pg_engine

def insert_work_id(work_id: str):
    pg_engine = get_postgresql_engine()
    with pg_engine.connect() as conn: 
        try: 
            stmt = text("INSERT INTO meeting_summary (work_id) VALUES (:work_id)")
            conn.execute(stmt, {"work_id": str(work_id)})
            conn.commit()
            print(f"[+] Inserted work_id: {work_id} with {conn}")
        except Exception as e:
            print("[-] Error inserting:", e)

