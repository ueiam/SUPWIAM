from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, timedelta
import functools

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_tres_complexe'

DB_FILE = 'pm5300_data.db'
AUTH_DB = 'users.db'

# Décorateur pour exiger l'authentification
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

# Initialisation de la base de données utilisateurs
def init_auth_db():
    conn = sqlite3.connect(AUTH_DB)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

# Récupère les données de la base sans générer de valeurs aléatoires
def get_last_values(device_id, limit=10):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            SELECT type, phase, valeur, unite, timestamp
            FROM measurements
            WHERE device_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (device_id, limit))
        results = c.fetchall()
        return results
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

def get_history_data(device_id, days=7):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        # Calculer la date limite
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

        # Récupérer les données pour chaque type de mesure
        types = ['V', 'I', 'P', 'F']
        results = {}

        for type_code in types:
            c.execute('''
                SELECT type, phase, valeur, unite, timestamp
                FROM measurements
                WHERE device_id = ? AND type = ? AND timestamp > ?
                ORDER BY timestamp ASC
            ''', (device_id, type_code, cutoff_date))
            results[type_code] = c.fetchall()

        return results
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return {type_code: [] for type_code in ['V', 'I', 'P', 'F']}
    finally:
        conn.close()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('welcome'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect(AUTH_DB)
        c = conn.cursor()
        c.execute('SELECT id, username, password FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if user and user[2] == password:  # En production, utiliser une méthode sécurisée de hachage
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Connexion réussie!', 'success')
            return redirect(url_for('welcome'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'danger')
    
    return render_template('auth.html', action='login')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect(AUTH_DB)
        c = conn.cursor()
        
        try:
            c.execute('''
            INSERT INTO users (username, email, password, created_at) 
            VALUES (?, ?, ?, ?)
            ''', (username, email, password, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            flash('Compte créé avec succès! Vous pouvez vous connecter.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Ce nom d\'utilisateur ou email est déjà utilisé', 'danger')
        finally:
            conn.close()
    
    return render_template('auth.html', action='signup')

@app.route('/logout')
def logout():
    session.clear()
    flash('Vous avez été déconnecté', 'info')
    return redirect(url_for('login'))

@app.route('/welcome')
@login_required
def welcome():
    username = session.get('username', 'Utilisateur')
    return render_template('welcome.html', username=username)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    device_id = None
    esp_data = []

    if request.method == 'POST':
        device_id = request.form.get('device_id', type=int)
        if device_id and 1 <= device_id <= 9:
            esp_data = get_last_values(device_id)
    else:
        device_id = request.args.get('device_id', type=int)
        if device_id and 1 <= device_id <= 9:
            esp_data = get_last_values(device_id)

    return render_template('dashboard.html',
                         esp_data=esp_data,
                         device_id=device_id,
                         username=session.get('username', 'Utilisateur'))

@app.route('/historique/<int:device_id>')
@login_required
def historique(device_id):
    if not (1 <= device_id <= 9):
        return redirect(url_for('dashboard'))

    # Récupérer la période sélectionnée (par défaut 7 jours)
    days = request.args.get('days', default=7, type=int)

    # Récupérer les données d'historique    # Récupérer les données d'historique
    history_data = get_history_data(device_id, days)

    return render_template('historique.html',
                         device_id=device_id,
                         selected_days=days,
                         voltage_data=history_data['V'],
                         current_data=history_data['I'],
                         power_data=history_data['P'],
                         freq_data=history_data['F'],
                         username=session.get('username', 'Utilisateur'))
# Initialiser la base de données d'authentification au démarrage
if __name__ == '__main__':
    init_auth_db()
    app.run(host='0.0.0.0', port=5010, debug=True)
