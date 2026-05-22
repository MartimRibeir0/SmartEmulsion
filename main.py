from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
from sensores import sensor_manager
from database import get_history, get_weekly_summary

app = FastAPI(title="Emulsão Smart API")
templates = Jinja2Templates(directory="templates")

# Modelo para receber o pedido de reposição
class FillRequest(BaseModel):
    tank_id: int
    target_level_percent: float
    target_oil_percent: float
    oil_to_add: float
    water_to_add: float

class TankSync(BaseModel):
    name: str
    capacity: float

# Iniciar monitorização ao arrancar a app
@app.on_event("startup")
async def startup_event():
    sensor_manager.start_monitoring(interval=5)

@app.post("/api/sync_tank")
async def sync_tank(tank: TankSync):
    sensor_manager.current_data["tank_name"] = tank.name
    sensor_manager.current_data["capacity"] = tank.capacity
    return {"status": "success"}

@app.get("/api/sensors/history")
async def get_sensors_history(tank_name: str = "Tanque Principal"):
    return get_history(tank_name)

@app.get("/api/sensors/weekly")
async def get_sensors_weekly(tank_name: str = "Tanque Principal"):
    return get_weekly_summary(tank_name)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/sensors")
async def get_sensors():
    return sensor_manager.read_sensors()

@app.post("/api/fill")
async def trigger_fill(req: FillRequest):
    # Calcular litros alvo com base na percentagem e capacidade
    capacity = sensor_manager.current_data["capacity"]
    target_liters = (req.target_level_percent / 100) * capacity
    
    # Iniciar processo de enchimento em background
    sensor_manager.process_fill(target_liters, req.oil_to_add)
    
    return {"status": "success", "message": "Enchimento iniciado"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
