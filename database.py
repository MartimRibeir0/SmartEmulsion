import sqlite3
from datetime import datetime

DATABASE_NAME = "emulsao_smart.db"

def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabela para as Leituras dos Sensores
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sensor_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        tank_name TEXT,
        ph REAL,
        oil_concentration REAL,
        level REAL
    )
    ''')
    
    # Tabela para Configurações
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_email TEXT,
        receiver_email TEXT,
        report_time TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Base de dados SQLite (Nativa) inicializada com sucesso!")

def save_reading(tank_name, ph, oil, level):
    conn = get_connection()
    cursor = conn.cursor()
    # Usar datetime.now() do Python para garantir hora local correta
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
    INSERT INTO sensor_readings (timestamp, tank_name, ph, oil_concentration, level)
    VALUES (?, ?, ?, ?, ?)
    ''', (now, tank_name, ph, oil, level))
    conn.commit()
    conn.close()

def get_history(tank_name, limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT timestamp, ph, oil_concentration, level 
    FROM sensor_readings 
    WHERE tank_name = ? 
    ORDER BY timestamp DESC 
    LIMIT ?
    ''', (tank_name, limit))
    rows = cursor.fetchall()
    conn.close()
    # Inverter para ordem cronológica (antigo -> novo)
    return [dict(row) for row in reversed(rows)]

def get_weekly_summary(tank_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT 
        DATE(timestamp) as date, 
        MAX(ph) as max_ph, 
        AVG(level) as avg_level, 
        MAX(oil_concentration) as max_oil
    FROM sensor_readings 
    WHERE tank_name = ?
    GROUP BY DATE(timestamp)
    ORDER BY date DESC
    LIMIT 7
    ''', (tank_name,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

if __name__ == "__main__":
    init_db()
