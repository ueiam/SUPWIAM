import board
import busio
import digitalio
import adafruit_rfm9x
import sqlite3
from datetime import datetime
import time
import sys

# Configuration
DB_FILE = 'pm5300_data.db'
FREQUENCY = 433.0  # MHz

# Types de données et leurs descriptions
DATA_TYPES = {
    'V': 'Tension',
    'I': 'Courant',
    'P': 'Puissance',
    'F': 'Fréquence'
}

# Unités correspondant aux types de données
UNITS = {
    'V': 'V',
    'I': 'A',
    'P': 'W',
    'F': 'Hz'
}

def init_db():
    """Initialise la base de données pour les mesures PM5300"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        # Création de la table des appareils
        c.execute('''CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY,
                    device_name TEXT)''')

        # Création de la table des mesures
        c.execute('''CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    type TEXT,
                    phase INTEGER,
                    valeur REAL,
                    unite TEXT,
                    rssi INTEGER,
                    timestamp DATETIME,
                    FOREIGN KEY (device_id) REFERENCES devices(device_id)
                )''')

        conn.commit()
        print("Base de données initialisée avec succès")
        return True
    except sqlite3.Error as e:
        print(f"Erreur d'initialisation de la base de données: {e}")
        return False
    finally:
        if conn:
            conn.close()

def add_device(device_id, device_name):
    """Ajoute un appareil dans la base de données s'il n'existe pas"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        # Vérifier si le périphérique existe déjà
        c.execute("SELECT * FROM devices WHERE device_id = ?", (device_id,))
        if c.fetchone() is None:
            # Ajouter le périphérique
            c.execute("INSERT INTO devices (device_id, device_name) VALUES (?, ?)", (device_id, device_name))
            conn.commit()
            print(f"Appareil {device_id} ajouté avec succès.")
        else:
            print(f"Appareil {device_id} déjà présent dans la base.")
    except sqlite3.Error as e:
        print(f"Erreur d'ajout de l'appareil {device_id}: {e}")
    finally:
        if conn:
            conn.close()

def save_measurement(device_id, type_mesure, phase, valeur, rssi):
    """Sauvegarde une mesure dans la base de données"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        unite = UNITS.get(type_mesure, '')

        c.execute('''INSERT INTO measurements
                    (device_id, type, phase, valeur, unite, rssi, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (device_id, type_mesure, phase, valeur, unite, rssi, timestamp))

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Erreur de sauvegarde en base de données: {e}")
        return False
    finally:
        if conn:
            conn.close()

def parse_pm5300_message(message):
    """Parse un message au format ESP_ID:TYPE:PHASE:VALEUR"""
    try:
        # Supprimer le préfixe "<<<" si présent
        if message.startswith('<<<<'):
            message = message[4:]

        parts = message.split(':')
        if len(parts) != 4:
            return None

        esp_id = parts[0]  # Identifiant ESP32
        type_mesure = parts[1]
        phase = int(parts[2])
        valeur = float(parts[3])

        if type_mesure not in DATA_TYPES:
            return None

        return {
            'esp_id': esp_id,
            'type': type_mesure,
            'phase': phase,
            'valeur': valeur
        }
    except (ValueError, IndexError):
        return None

def setup_lora():
    """Configure le module LoRa"""
    try:
        # Configuration du bus SPI
        spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        cs = digitalio.DigitalInOut(board.CE1)  # Utiliser CE1 pour CS
        reset = digitalio.DigitalInOut(board.D25)  # GPIO 25 pour RESET

        # Initialisation du module LoRa RFM9x
        rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, FREQUENCY)
        rfm9x.tx_power = 23  # Configuration de la puissance d'émission

        print(f"Module LoRa initialisé sur la fréquence {FREQUENCY} MHz")
        return rfm9x
    except Exception as e:
        print(f"Erreur d'initialisation du module LoRa: {e}")
        return None

def print_measurement(data, rssi):
    """Affiche une mesure formatée dans la console"""
    type_desc = DATA_TYPES.get(data['type'], data['type'])
    unite = UNITS.get(data['type'], '')

    print(f"[{datetime.now().strftime('%H:%M:%S')}] ESP {data['esp_id']} - {type_desc} (Phase {data['phase']}): {data['valeur']} {unite} | RSSI: {rssi} dBm")

def main():
    """Programme principal"""
    print("Initialisation du récepteur LoRa pour PM5300...")

    # Initialisation de la base de données
    if not init_db():
        sys.exit(1)

    # Configuration du module LoRa
    rfm9x = setup_lora()
    if not rfm9x:
        sys.exit(1)

    last_stats_update = datetime.now()

    print("Système prêt - En attente de messages de la centrale...")
    try:
        while True:
            # Réception des données (timeout de 5 secondes)
            packet = rfm9x.receive(timeout=5.0)

            if packet is not None:
                try:
                    # Décodage du message
                    message = packet.decode('utf-8').strip()
                    rssi = rfm9x.last_rssi

                    # Analyse du message
                    data = parse_pm5300_message(message)

                    if data:
                        # Vérifier si le périphérique existe déjà dans la base de données, sinon l'ajouter
                        add_device(data['esp_id'], f"Device {data['esp_id']}")

                        # Affichage de la mesure
                        print_measurement(data, rssi)

                        # Sauvegarde en base de données
                        save_measurement(data['esp_id'], data['type'], data['phase'], data['valeur'], rssi)
                    else:
                        print(f"Message ignoré (format incorrect): {message}")
                except UnicodeDecodeError:
                    print(f"Message reçu non décodable: {packet}")

            # Mise à jour des statistiques quotidiennes toutes les heures
            current_time = datetime.now()
            if (current_time - last_stats_update).seconds > 3600:
                update_daily_stats()
                last_stats_update = current_time

    except KeyboardInterrupt:
        print("\nProgramme arrêté par l'utilisateur")
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    main()
