import json
import os
from flask import Flask, render_template, request, jsonify
import plotly.graph_objs as go
import plotly.io as pio
from datetime import datetime
from snmp_monitor import SNMPMonitor  # Importer le module SNMPMonitor
import logging
import subprocess
import platform

# Configurer le système de logging
LOG_FILE = "app.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Application démarrée.")


app = Flask(__name__)

# Fichier JSON pour sauvegarder les équipements
EQUIPMENT_FILE = "equipment.json"
# Fichier JSON pour le journal de trafic réseau
TRAFFIC_LOG_FILE = "traffic_log.json"

# Charger les équipements à partir du fichier JSON
def load_equipments():
    if not os.path.exists(EQUIPMENT_FILE):
        return []
    with open(EQUIPMENT_FILE, "r") as file:
        equipments = json.load(file)
    for index, equipment in enumerate(equipments):
        if "id" not in equipment:
            equipment["id"] = index + 1  # Assigner un ID unique basé sur l'index
    save_equipments(equipments)
    return equipments

# Sauvegarder les équipements dans le fichier JSON
def save_equipments(equipments):
    with open(EQUIPMENT_FILE, "w") as file:
        json.dump(equipments, file, indent=4)

# Charger le journal de trafic réseau
def load_traffic_log():
    if not os.path.exists(TRAFFIC_LOG_FILE):
        return []
    with open(TRAFFIC_LOG_FILE, "r") as file:
        logs = []
        for line in file:
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return logs

# Sauvegarder le journal de trafic réseau
def save_traffic_log(data):
    with open(TRAFFIC_LOG_FILE, "a") as file:
        json.dump(data, file)
        file.write("\n")

@app.route("/")
def index():
    equipments = load_equipments()
    for equipment in equipments:
        # Utilise directement l'IP telle qu'elle est définie
        equipment["display_ip"] = equipment["ip"]
        
        # Vérifie l'état avec la fonction corrigée
        equipment["status"] = check_equipment_status(equipment["ip"])
    
    return render_template("index.html", equipments=equipments)




@app.route("/add", methods=["POST"])
def add_equipment():
    name = request.form.get("name")
    ip = request.form.get("ip")
    description = request.form.get("description")
    if not name or not ip:
        logging.warning("Tentative d'ajout d'un équipement avec des champs manquants.")
        return jsonify({"error": "Name and IP address are required"}), 400
    equipments = load_equipments()
    new_id = max([equipment.get("id", 0) for equipment in equipments], default=0) + 1
    equipment = {
        "id": new_id,
        "name": name,
        "ip": ip,
        "description": description
    }
    equipments.append(equipment)
    save_equipments(equipments)
    return jsonify({"message": "Equipment added successfully"}), 200

@app.route("/monitor/<int:id>", methods=["GET"])
def monitor_equipment(id):
    equipments = load_equipments()
    equipment = next((e for e in equipments if e["id"] == id), None)
    if not equipment:
        return jsonify({"error": "Equipment not found"}), 404

    monitor = SNMPMonitor(equipment["ip"], "public")
    sys_name = monitor.get_snmp_data("1.3.6.1.2.1.1.5.0")  # Nom de l'équipement (sysName)
    sys_uptime = monitor.get_snmp_data("1.3.6.1.2.1.1.3.0")  # Temps de fonctionnement (sysUpTime)

    return jsonify({
        "name": sys_name if sys_name else "Unknown",
        "uptime": sys_uptime if sys_uptime else "Unknown"
    })

@app.route("/traffic/<int:id>", methods=["GET"])
def monitor_traffic(id):
    equipments = load_equipments()
    equipment = next((e for e in equipments if e["id"] == id), None)
    if not equipment:
        logging.warning(f"Équipement introuvable pour la surveillance de trafic (ID: {id}).")
        return jsonify({"error": "Equipment not found"}), 404

    monitor = SNMPMonitor(equipment["ip"], "public")
    in_octets = monitor.get_in_octets()
    out_octets = monitor.get_out_octets()

    traffic_data = {
        "timestamp": datetime.now().isoformat(),
        "equipment_id": id,
        "in_octets": in_octets,
        "out_octets": out_octets
    }
    save_traffic_log(traffic_data)

    logging.info(f"Surveillance de trafic pour l'équipement ID {id} : {traffic_data}")
    return jsonify({
        "in_octets": in_octets if in_octets is not None else "Unknown",
        "out_octets": out_octets if out_octets is not None else "Unknown"
    })

@app.route("/graph/<int:id>", methods=["GET"])
def generate_graph(id):
    logs = load_traffic_log()
    filtered_logs = [log for log in logs if log.get("equipment_id") == id]
    if not filtered_logs:
        return render_template("graph.html", graph="<p>No data available for this equipment.</p>")

    timestamps = [log["timestamp"] for log in filtered_logs]
    in_octets = [int(log["in_octets"]) for log in filtered_logs if log.get("in_octets")]
    out_octets = [int(log["out_octets"]) for log in filtered_logs if log.get("out_octets")]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=timestamps, y=in_octets, mode="lines+markers", name="In Octets"))
    fig.add_trace(go.Scatter(x=timestamps, y=out_octets, mode="lines+markers", name="Out Octets"))
    fig.update_layout(
        title="Traffic Evolution",
        xaxis_title="Timestamp",
        yaxis_title="Octets",
        legend_title="Traffic Type"
    )

    graph_html = pio.to_html(fig, full_html=False)
    return render_template("graph.html", graph=graph_html)

@app.route("/delete/<int:id>", methods=["POST"])
def delete_equipment(id):
    equipments = load_equipments()
    equipment = next((e for e in equipments if e["id"] == id), None)
    if not equipment:
        logging.warning(f"Tentative de suppression d'un équipement inexistant (ID: {id}).")
        return jsonify({"error": "Equipment not found"}), 404

    equipments = [e for e in equipments if e["id"] != id]
    save_equipments(equipments)
    logging.info(f"Équipement supprimé : {equipment}")
    return jsonify({"message": "Equipment deleted successfully"}), 200

@app.route("/update/<int:id>", methods=["POST"])
def update_equipment(id):
    equipments = load_equipments()
    equipment = next((e for e in equipments if e["id"] == id), None)

    if not equipment:
        return jsonify({"error": "Equipment not found"}), 404

    # Récupérer les nouvelles données du formulaire
    name = request.form.get("name")
    ip = request.form.get("ip")
    description = request.form.get("description")

    # Mettre à jour les informations de l'équipement
    equipment["name"] = name
    equipment["ip"] = ip
    equipment["description"] = description

    save_equipments(equipments)

    return jsonify({"message": "Equipment updated successfully"}), 200

@app.route("/graph/data/<int:id>")
def fetch_graph_data(id):
    print("Request arguments:", request.args)
    logs = load_traffic_log()
    filtered_logs = [log for log in logs if log.get("equipment_id") == id]

    # Logs pour vérifier les paramètres
    print("Start Date:", request.args.get("start_date"))
    print("End Date:", request.args.get("end_date"))
    print("Show In:", request.args.get("show_in"))
    print("Show Out:", request.args.get("show_out"))

    # Filtrer par date
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    if start_date:
        start_date = datetime.fromisoformat(start_date)
        filtered_logs = [log for log in filtered_logs if datetime.fromisoformat(log["timestamp"]) >= start_date]
    if end_date:
        end_date = datetime.fromisoformat(end_date)
        filtered_logs = [log for log in filtered_logs if datetime.fromisoformat(log["timestamp"]) <= end_date]

    # Logs pour vérifier les données filtrées
    print("Filtered Logs After Dates:", filtered_logs)

    # Déterminer les traces à afficher
    show_in = request.args.get("show_in", "true").lower() == "true"
    show_out = request.args.get("show_out", "true").lower() == "true"
    print("Show In:", show_in, "Show Out:", show_out)

    timestamps = [log["timestamp"] for log in filtered_logs]
    in_octets = [int(log["in_octets"]) for log in filtered_logs if log.get("in_octets")]
    out_octets = [int(log["out_octets"]) for log in filtered_logs if log.get("out_octets")]

    fig = go.Figure()
    if show_in:
        fig.add_trace(go.Scatter(x=timestamps, y=in_octets, mode="lines+markers", name="In Octets"))
    if show_out:
        fig.add_trace(go.Scatter(x=timestamps, y=out_octets, mode="lines+markers", name="Out Octets"))

    # Vérifiez si des données sont ajoutées à la figure
    print("Figure data:", fig.data)

    fig.update_layout(
        title="Traffic Evolution",
        xaxis_title="Timestamp",
        yaxis_title="Octets",
        legend_title="Traffic Type"
    )

    return pio.to_html(fig, full_html=False)

@app.route("/logs", methods=["GET"])
def view_logs():
    """
    Affiche les logs de l'application dans un tableau interactif.
    """
    if not os.path.exists(LOG_FILE):
        return render_template("logs.html", logs=[])

    with open(LOG_FILE, "r") as file:
        logs = file.readlines()

    # Envoyer les logs directement au modèle HTML
    return render_template("logs.html", logs=logs)

import subprocess
import platform

def check_equipment_status(ip):
    """
    Vérifie si une machine est accessible.
    Retourne 'OK' si un ping répond, sinon 'KO'.
    """
    
    try:
        # Détection du système d'exploitation
        if platform.system().lower() == "windows":
            # Commande pour Windows
            result = subprocess.run(["ping", "-n", "1", ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            # Commande pour Linux/Unix
            result = subprocess.run(["ping", "-c", "1", ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Vérification du code de retour
        if result.returncode == 0:
            return "OK"
        else:
            return "KO"
    except Exception as e:
        print(f"Erreur lors de la vérification de l'état pour {ip}: {e}")
        return "KO"


if __name__ == "__main__":
    app.run(debug=True)
