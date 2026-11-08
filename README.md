#  Supervision à distance de centrales de mesure par LoRa

Projet de fin d'études : système de **supervision à distance d'installations électriques** basé sur la technologie **LoRa** (Long Range), sans connexion Internet.

Les valeurs de **tension, courant, puissance et fréquence** mesurées par des centrales de mesure sont collectées par des **ESP32**, transmises en LoRa vers un **Raspberry Pi** (serveur central), stockées dans une base **SQLite3** et affichées sur une **interface web** accessible depuis n'importe quel navigateur.

---

##  Contexte et problématique

La surveillance efficace des installations électriques devient de plus en plus pressante, surtout lorsque ces installations sont **dispersées géographiquement**. Les méthodes de supervision classiques y sont peu adaptées, coûteuses ou techniquement limitées.

Notre solution s'appuie sur LoRa, reconnue pour sa **grande portée** et sa **faible consommation énergétique**. Elle offre un dispositif **économique, flexible et évolutif**, adapté aux environnements industriels ou isolés.

---

##  Architecture du système

```
Centrale de mesure (PM5300)
        │  (mesures V, I, P, F)
        ▼
     ESP32  ──── LoRa ────►  Récepteur LoRa + Raspberry Pi
                                      │
                                      ▼
                             Base SQLite3 (pm5300_data.db)
                                      │
                                      ▼
                          Serveur Flask (interface web)
                                      │
                                      ▼
                       Navigateur (PC, tablette, téléphone)
```

1. Les **ESP32** relèvent tension, courant, puissance et fréquence sur chaque centrale de mesure.
2. Les données sont envoyées en **LoRa** au serveur central (jusqu'à 9 appareils supervisés).
3. Le **Raspberry Pi** reçoit, traite et enregistre les mesures dans **SQLite3**.
4. L'**interface web Flask** affiche les valeurs en direct et l'historique sous forme de graphiques.

---

##  Fonctionnalités

- Authentification des utilisateurs (inscription, connexion, déconnexion)
- Tableau de bord : dernières mesures d'un appareil choisi (1 à 9)
- Historique graphique sur une période réglable (par défaut 7 jours)
- Mesures suivies : **tension (V)**, **courant (I)**, **puissance (P)**, **fréquence (F)**
- Fonctionnement **hors ligne**, sans Internet

---

##  Structure du projet

| Fichier | Rôle |
|---|---|
| `app113.py` | Application web Flask : authentification, tableau de bord, historique |
| `test12.py` | `<à vérifier : réception LoRa / insertion des mesures dans la base>` |
| `auth.html` | Page de connexion et d'inscription |
| `welcome.html` | Page d'accueil après connexion |
| `dashboard.html` | Tableau de bord des dernières mesures |
| `historique.html` | Graphiques de l'historique |

>  Flask cherche les pages HTML dans un dossier nommé **`templates/`**. Place `auth.html`, `welcome.html`, `dashboard.html` et `historique.html` dans ce dossier, sinon l'application affichera une erreur `TemplateNotFound`.

Arborescence attendue :

```
.
├── app113.py
├── test12.py
└── templates/
    ├── auth.html
    ├── welcome.html
    ├── dashboard.html
    └── historique.html
```

---

##  Matériel

- Centrales de mesure `<PM5300>`
- Microcontrôleurs **ESP32** + module LoRa `<ex. SX1276 / RFM95>`
- **Raspberry Pi** `<modèle>` + récepteur LoRa
- Antennes LoRa `<fréquence, ex. 868 MHz>`

---

##  Installation

```bash
git clone https://github.com/<ton-pseudo>/supervision-lora-centrales.git
cd supervision-lora-centrales
python3 -m venv myenv
source myenv/bin/activate
pip install flask
```

Les modules `sqlite3`, `datetime` et `functools` sont déjà inclus dans Python.

---

##  Lancer l'application

```bash
cd supervision-lora-centrales
source myenv/bin/activate
python3 app113.py
```

Puis ouvrir dans un navigateur : **`http://<IP_DU_PI>:5010`**

Au premier lancement, la base des utilisateurs `users.db` est créée automatiquement. Crée un compte depuis la page d'inscription (`/signup`), puis connecte-toi.

**Arrêter :** `Ctrl+C` dans le terminal.

---

##  Base de données

| Base | Contenu |
|---|---|
| `pm5300_data.db` | Mesures reçues des ESP32, table `measurements` |
| `users.db` | Comptes utilisateurs, créée automatiquement |

Colonnes de la table `measurements` :

| Colonne | Description |
|---|---|
| `device_id` | Numéro de l'appareil (1 à 9) |
| `type` | `V` tension, `I` courant, `P` puissance, `F` fréquence |
| `phase` | Phase mesurée |
| `valeur` | Valeur mesurée |
| `unite` | Unité (V, A, W, Hz) |
| `timestamp` | Date et heure (`AAAA-MM-JJ HH:MM:SS`) |

---

##  Pages de l'interface

| Route | Description |
|---|---|
| `/login` | Connexion |
| `/signup` | Création de compte |
| `/welcome` | Page d'accueil |
| `/dashboard` | Dernières mesures d'un appareil |
| `/historique/<id>?days=7` | Historique de l'appareil sur N jours |
| `/logout` | Déconnexion |

---

##  Sécurité (à améliorer pour la production)

- Les mots de passe sont actuellement stockés **en clair** : utiliser `werkzeug.security` (`generate_password_hash` / `check_password_hash`).
- Remplacer `secret_key` par une clé longue et aléatoire, hors du code.
- Désactiver `debug=True` en production.

---

##  Structure du mémoire

1. **Chapitre 1** : composants matériels choisis et leur rôle dans le système
2. **Chapitre 2** : réalisation concrète, des premiers tests à l'intégration complète
3. **Chapitre 3** : analyse des résultats, perspectives d'amélioration, difficultés rencontrées et solutions apportées

---

##  Perspectives

- Alertes en cas de dépassement de seuils
- Export des mesures (CSV)
- Plus d'appareils supervisés
- Hachage des mots de passe et accès sécurisé (HTTPS)

---

##  Auteurs

`AIT ABDENNAIM WIAM ` : Projet de fin d'études, `EST AGADIR `, `2024>`

##  Licence

MIT
