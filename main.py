from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import pytz

app = FastAPI()

#MongoDB
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["logdb"] 
log_collection = db["logs"] 


scheduler = AsyncIOScheduler()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.utcnow()

    
    response = await call_next(request)

    
    process_time = (datetime.utcnow() - start_time).total_seconds()

    log_data = {
        "method": request.method,
        "url": request.url.path,
        "status_code": response.status_code,
        "process_time": process_time,
        "timestamp": start_time
    }

    await log_collection.insert_one(log_data)  

    return response

async def delete_old_logs():
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    result = await log_collection.delete_many({"timestamp": {"$lt": seven_days_ago}})
    print(f"Deleted {result.deleted_count} logs older than 7 days.")

@app.on_event("startup")
async def startup_event():
    scheduler.add_job(delete_old_logs, "interval", days=1) 
    scheduler.start()

@app.get("/")
async def root():
    return {"message": "proverka-work!"}