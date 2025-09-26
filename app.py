# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
    db.init_app(app)
    return app

app = create_app()

### MODELOS ###
class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    type = db.Column(db.String, nullable=False)   # hospital, puesto, brigada
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    status = db.Column(db.String, default='activo')
    capacity = db.Column(db.Integer, default=0)

class Jornada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    date = db.Column(db.String, nullable=False)  # ISO date
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    expected_attendees = db.Column(db.Integer, default=0)
    resources = db.Column(db.String, default='')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String, nullable=False)  # YYYY-MM-DD, we store month start
    count = db.Column(db.Integer, default=0)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))

### RUTAS FRONTEND ###
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')
        # Demo: credenciales hardcodeadas (en producción usar hashing y DB)
        if user == 'admin' and pwd == 'admin123':
            session['admin'] = True
            return redirect(url_for('admin'))
        return render_template('login.html', error="Credenciales inválidas")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect(url_for('login'))
    return render_template('admin.html')

### RUTAS API ###
@app.route('/api/services')
def api_services():
    services = Service.query.all()
    return jsonify([{
        'id': s.id, 'name': s.name, 'type': s.type, 'lat': s.lat, 'lon': s.lon,
        'status': s.status, 'capacity': s.capacity
    } for s in services])

@app.route('/api/jornadas')
def api_jornadas():
    js = Jornada.query.order_by(Jornada.date).all()
    return jsonify([{
        'id': j.id, 'title': j.title, 'date': j.date, 'service_id': j.service_id,
        'expected_attendees': j.expected_attendees, 'resources': j.resources
    } for j in js])

@app.route('/api/attendances')
def api_attendances():
    att = Attendance.query.order_by(Attendance.date).all()
    return jsonify([{'date': a.date, 'count': a.count, 'service_id': a.service_id} for a in att])

@app.route('/api/prediction')
def api_prediction():
    # Simple projection: tomar atenciones mensuales, promedio móvil y proyectar próximos 6 meses
    rows = Attendance.query.all()
    if not rows:
        return jsonify({'error': 'no data'}), 400
    df = pd.DataFrame([{'date': r.date, 'count': r.count} for r in rows])
    df['date'] = pd.to_datetime(df['date'])
    # Agrupar por mes
    dfm = df.groupby(pd.Grouper(key='date', freq='MS')).sum().reset_index()
    dfm = dfm.sort_values('date')
    dfm['month'] = dfm['date'].dt.strftime('%Y-%m')
    # simple moving average of last 3 months
    dfm['ma3'] = dfm['count'].rolling(3, min_periods=1).mean()
    last_ma = float(dfm['ma3'].iloc[-1])
    # tomar ligera estacionalidad basada en month-of-year averages
    dfm['moy'] = dfm['date'].dt.month
    monthly_avg = dfm.groupby('moy')['count'].mean().to_dict()
    # proyectar 6 meses
    import datetime as dt
    last_date = dfm['date'].iloc[-1]
    projections = []
    for i in range(1,7):
        nxt = (last_date + pd.DateOffset(months=i))
        base = last_ma
        season = monthly_avg.get(int(nxt.month), 0)
        # combinación simple: 60% base + 40% season normed
        season_norm = season if season>0 else 0
        proj = int(round(0.6*base + 0.4*season_norm))
        projections.append({'month': nxt.strftime('%Y-%m'), 'projected': proj})
    # devolver serie histórica y proyecciones
    history = [{'month': r['month'], 'count': int(r['count'])} for _, r in dfm.to_dict('index').items()]
    return jsonify({'history': history, 'projections': projections})

### ENDPOINTS ADMIN (CRUD mínimos para ejemplo) ###
@app.route('/api/admin/service', methods=['POST'])
def admin_create_service():
    if not session.get('admin'):
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json
    s = Service(name=data.get('name'), type=data.get('type'), lat=float(data.get('lat')), lon=float(data.get('lon')), status=data.get('status','activo'), capacity=int(data.get('capacity',0)))
    db.session.add(s)
    db.session.commit()
    return jsonify({'ok': True, 'id': s.id})

@app.route('/api/admin/jornada', methods=['POST'])
def admin_create_jornada():
    if not session.get('admin'):
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json
    j = Jornada(title=data.get('title'), date=data.get('date'), service_id=int(data.get('service_id')), expected_attendees=int(data.get('expected_attendees',0)), resources=data.get('resources',''))
    db.session.add(j)
    db.session.commit()
    return jsonify({'ok': True, 'id': j.id})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
