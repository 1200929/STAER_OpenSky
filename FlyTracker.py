import requests
import sqlite3
import folium
from flask import Flask, render_template, request
import os

app = Flask(__name__, static_folder='static')

lon_min, lat_min = -180, -90
lon_max, lat_max = 180, 90

user_name = 'V4NDO'
password = 'Pl3namente'

def create_database():
    with sqlite3.connect('Airplane.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE AircraftInfo (
                id INTEGER PRIMARY KEY,
                icao24 TEXT,
                callsign TEXT,
                origin_country TEXT,
                time_position INTEGER,
                last_contact INTEGER,
                longitude REAL,
                latitude REAL,
                on_ground INTEGER,
                velocity REAL,
                true_track REAL,
                vertical_rate REAL,
                sensors TEXT,
                baro_altitude REAL,
                squawk TEXT,
                spi INTEGER,
                position_source INTEGER
            )
        ''')

def call_api_and_populate_db():
    url_data = f'https://{user_name}:{password}@opensky-network.org/api/states/all?' \
               f'lamin={lat_min}&lomin={lon_min}&lamax={lat_max}&lomax={lon_max}'
    response = requests.get(url_data)
    data = response.json()

    with sqlite3.connect('Airplane.db') as conn:
        cursor = conn.cursor()
        for aircraft in data['states']:
            icao24 = aircraft[0]
            callsign = aircraft[1]
            origin_country = aircraft[2]
            time_position = aircraft[3]
            last_contact = aircraft[4]
            longitude = aircraft[5]
            latitude = aircraft[6]

            cursor.execute('''
                INSERT INTO AircraftInfo (icao24, callsign, origin_country, time_position, last_contact, longitude, latitude, ...)
                VALUES (?, ?, ?, ?, ?, ?, ?, ...)
            ''', (icao24, callsign, origin_country, time_position, last_contact, longitude, latitude, ...))

@app.route('/', methods=['GET', 'POST'])
def index():
    selected_country = None
    min_velocity = 0  

    if request.method == 'POST':
        selected_country = request.form.get('country')
        input_min_velocity = request.form.get('velocity')

        if input_min_velocity is not None and input_min_velocity != '':
            try:
                min_velocity = float(input_min_velocity)
            except ValueError:
                min_velocity = 0

    if not os.path.exists('Airplane.db'):
        create_database()
        call_api_and_populate_db()

    m = folium.Map(location=[0, 0], zoom_start=2)

    with sqlite3.connect('Airplane.db') as conn:
        cursor = conn.cursor()
        query = "SELECT latitude, longitude, callsign, origin_country, velocity FROM AircraftInfo"
        conditions = []
        if selected_country:
            conditions.append(f"origin_country = '{selected_country}'")
        if min_velocity is not None:
            conditions.append(f"velocity >= {min_velocity}")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            latitude, longitude, callsign, origin_country, velocity = row
            if latitude is not None and longitude is not None:
                folium.Marker([latitude, longitude], popup=f"Call Sign: {callsign}<br>Origin Country: {origin_country}<br>Velocity: {velocity}").add_to(m)

    return render_template('index.html', map=m._repr_html_())

if __name__ == '__main__':
    app.run(debug=True)
