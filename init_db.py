# init_db.py
from datetime import datetime, timedelta
from app import db, Service, Jornada, Attendance, create_app
import random
import os

app = create_app()
app.app_context().push()

# Borra y crea DB nueva
db.drop_all()
db.create_all()

# Crear servicios (hospitales / puestos / brigadas)
services = [
    Service(name="Hospital Central - Tunja", type="hospital", lat=5.5360, lon=-73.3670, status="activo", capacity=120),
    Service(name="Puesto de Salud Guateque", type="puesto", lat=5.3530, lon=-73.2860, status="activo", capacity=20),
    Service(name="Brigada móvil - Cómbita", type="brigada", lat=5.6667, lon=-73.4500, status="programada", capacity=50),
    Service(name="Puesto de Salud Chocontá", type="puesto", lat=5.065, lon=-73.286, status="activo", capacity=25)
]

for s in services:
    db.session.add(s)
db.session.commit()

# Jornadas
jornadas = [
    Jornada(title="Jornada de vacunación - Tunja", date=datetime.now() + timedelta(days=12), service_id=1, expected_attendees=200, resources="vacunas, personal"),
    Jornada(title="Brigada preventiva Cómbita", date=datetime.now() + timedelta(days=25), service_id=3, expected_attendees=80, resources="medicinas básicas"),
]
for j in jornadas:
    db.session.add(j)
db.session.commit()

# Atenciones históricas (attendance) - generar datos mensuales en los últimos 18 meses
start = datetime.now().replace(day=1) - timedelta(days=18*30)
for m in range(18):
    date = (start + timedelta(days=m*30)).replace(day=1)
    # simular variación estacional (más respiratorias en meses "lluviosos")
    base = 100 + 10*m
    seasonal = 50 if date.month in (3,4,5,9,10) else 0
    count = max(10, int(base + seasonal + random.gauss(0,20)))
    a = Attendance(date=date.strftime("%Y-%m-%d"), count=count, service_id=random.choice([1,2,4]))
    db.session.add(a)

db.session.commit()
print("Base de datos inicializada con datos de ejemplo.")
