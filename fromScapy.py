from scapy.all import rdpcap, TCP, IP
from scapy.layers.http import HTTPRequest
import re
import requests
import hashlib
import os
import pandas as pd
from openpyxl import load_workbook

# Récupération de la clé API depuis une variable d'environnement
VT_API_KEY = "1956eab1c727de4fd81c76716322f923013071bdd0886a46e05beb2e44f7bd04"
print("VirusTotal API Key:", VT_API_KEY)
VT_URL_IP = "https://www.virustotal.com/api/v3/ip_addresses/"
VT_URL_FILE = "https://www.virustotal.com/api/v3/files/"
HEADERS = {"x-apikey": VT_API_KEY} if VT_API_KEY else {}

# Liste de fichiers connus comme malveillants (basée sur ton analyse manuelle)
KNOWN_MALICIOUS_FILES = ["actiV.bin"]

# Mapping des types de menaces VirusTotal vers MITRE ATT&CK (simplifié pour l'exemple)
MITRE_MAPPING = {
    "trojan": ["Initial Access", "Execution", "Persistence"],
    "malware": ["Execution", "Persistence", "Defense Evasion"],
    "phishing": ["Initial Access", "Credential Access"],
    "botnet": ["Command and Control", "Lateral Movement"],
    "ddos": ["Impact"],
    "ransomware": ["Execution", "Impact"],
    "worm": ["Lateral Movement", "Collection"],
}

# Fonction pour catégoriser une menace selon MITRE ATT&CK
def categorize_mitre(threat_types):
    mitre_stages = set()
    for threat in threat_types:
        threat = threat.lower()
        for key, stages in MITRE_MAPPING.items():
            if key in threat:
                mitre_stages.update(stages)
    return list(mitre_stages) if mitre_stages else ["Unknown"]

# Fonction pour vérifier une IP sur VirusTotal et récupérer les détails
def check_ip_virustotal(ip):
    try:
        response = requests.get(f"{VT_URL_IP}{ip}", headers=HEADERS, timeout=10)
        print("f checking IP: {ip} -> Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            stats = data['data']['attributes']['last_analysis_stats']
            is_malicious = stats['malicious'] > 0
            details = {
                "is_malicious": is_malicious,
                "malicious_count": stats['malicious'],
                "suspicious_count": stats['suspicious'],
                "type_of_threat": [],
                "attack_type": [],
                "last_analysis_date": data['data']['attributes'].get('last_analysis_date', 'N/A'),
                "country": data['data']['attributes'].get('country', 'N/A'),
                "city": data['data']['attributes'].get('city', 'N/A'),
                "as_owner": data['data']['attributes'].get('as_owner', 'N/A'),
                "mitre_stages": [],
            }
            # Récupérer les détails des moteurs de détection
            if is_malicious:
                results = data['data']['attributes']['last_analysis_results']
                for engine, result in results.items():
                    if result['category'] in ['malicious', 'suspicious']:
                        threat = result.get('result', 'Unknown threat')
                        attack = result.get('method', 'Unknown attack')
                        details['type_of_threat'].append(threat)
                        details['attack_type'].append(attack)
                # Catégoriser selon MITRE ATT&CK
                details['mitre_stages'] = categorize_mitre(details['type_of_threat'])
            
            # Afficher les détails dans le terminal
            print(f"\n=== Détails pour l'IP {ip} ===")
            print(f"Malveillante : {is_malicious}")
            print(f"Nombre de détections malveillantes : {details['malicious_count']}")
            print(f"Nombre de détections suspectes : {details['suspicious_count']}")
            print(f"Types de menaces : {', '.join(details['type_of_threat']) if details['type_of_threat'] else 'N/A'}")
            print(f"Types d'attaques : {', '.join(details['attack_type']) if details['attack_type'] else 'N/A'}")
            print(f"Étapes MITRE ATT&CK : {', '.join(details['mitre_stages']) if details['mitre_stages'] else 'N/A'}")
            print(f"Dernière analyse : {details['last_analysis_date']}")
            print(f"Pays : {details['country']}")
            print(f"Ville : {details['city']}")
            print(f"Propriétaire AS : {details['as_owner']}")
            print("====================\n")
            
            return details
        else:
            print(f"Erreur lors de la vérification de l'IP {ip} : {response.status_code}")
            return {"is_malicious": False}
    except requests.RequestException as e:
        print(f"Erreur réseau lors de la vérification de l'IP {ip} : {e}")
        return {"is_malicious": False}

# Fonction pour calculer le hash d'un fichier
def get_file_hash(filename):
    hasher = hashlib.sha256()
    try:
        with open(filename, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
    except FileNotFoundError:
        print(f"Fichier {filename} non trouvé dans le répertoire courant.")
        return None

# Fonction pour vérifier un fichier sur VirusTotal et récupérer les détails
def check_file_virustotal(file_hash):
    try:
        response = requests.get(f"{VT_URL_FILE}{file_hash}", headers=HEADERS, timeout=10)
        print(f"Checking File Hash: {file_hash} -> Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            stats = data['data']['attributes']['last_analysis_stats']
            is_malicious = stats['malicious'] > 0
            details = {
                "is_malicious": is_malicious,
                "malicious_count": stats['malicious'],
                "suspicious_count": stats['suspicious'],
                "type_of_threat": [],
                "attack_type": [],
                "last_analysis_date": data['data']['attributes'].get('last_analysis_date', 'N/A'),
                "first_submission_date": data['data']['attributes'].get('first_submission_date', 'N/A'),
                "mitre_stages": [],
            }
            # Récupérer les détails des moteurs de détection
            if is_malicious:
                results = data['data']['attributes']['last_analysis_results']
                for engine, result in results.items():
                    if result['category'] in ['malicious', 'suspicious']:
                        threat = result.get('result', 'Unknown threat')
                        attack = result.get('method', 'Unknown attack')
                        details['type_of_threat'].append(threat)
                        details['attack_type'].append(attack)
                # Catégoriser selon MITRE ATT&CK
                details['mitre_stages'] = categorize_mitre(details['type_of_threat'])
            
            # Afficher les détails dans le terminal
            print(f"\n=== Détails pour le fichier (hash: {file_hash}) ===")
            print(f"Malveillant : {is_malicious}")
            print(f"Nombre de détections malveillantes : {details['malicious_count']}")
            print(f"Nombre de détections suspectes : {details['suspicious_count']}")
            print(f"Types de menaces : {', '.join(details['type_of_threat']) if details['type_of_threat'] else 'N/A'}")
            print(f"Types d'attaques : {', '.join(details['attack_type']) if details['attack_type'] else 'N/A'}")
            print(f"Étapes MITRE ATT&CK : {', '.join(details['mitre_stages']) if details['mitre_stages'] else 'N/A'}")
            print(f"Dernière analyse : {details['last_analysis_date']}")
            print(f"Première soumission : {details['first_submission_date']}")
            print("====================\n")
            
            return details
        else:
            print(f"Erreur lors de la vérification du fichier {file_hash} : {response.status_code}")
            return {"is_malicious": False}
    except requests.RequestException as e:
        print(f"Erreur réseau lors de la vérification du fichier {file_hash} : {e}")
        return {"is_malicious": False}

# Fonction pour analyser le fichier PCAP
def analyse_pcap(fichier_pcap):
    packets = rdpcap(fichier_pcap)
    http_requests = []
    ip_list = set()
    
    for packet in packets:
        # Extraction des IPs
        if packet.haslayer(IP):
            ip_list.add(packet[IP].src)
            ip_list.add(packet[IP].dst)
        
        # Détection des requêtes HTTP
        try:
            if packet.haslayer(HTTPRequest):
                host = packet[HTTPRequest].Host.decode(errors="ignore") if packet[HTTPRequest].Host else ""
                path = packet[HTTPRequest].Path.decode(errors="ignore") if packet[HTTPRequest].Path else ""
                method = packet[HTTPRequest].Method.decode(errors="ignore") if packet[HTTPRequest].Method else ""
                full_url = f"http://{host}{path}"
                
                if method == "GET":
                    filename = re.findall(r"[^/]+$", path)
                    filename = filename[0] if filename else "Unknown"
                    http_requests.append({
                        "method": method,
                        "url": full_url,
                        "filename": filename
                    })
            
            # Détection des requêtes HTTP sur des ports non standards (comme 8000)
            if packet.haslayer(TCP) and packet.haslayer("Raw"):
                if packet[TCP].dport in [80, 8000]:  # Inclure le port 8000
                    raw_data = packet["Raw"].load.decode(errors="ignore")
                    if "GET" in raw_data and "HTTP" in raw_data:
                        # Extraire l'URL manuellement
                        lines = raw_data.split("\n")
                        for line in lines:
                            if line.startswith("GET"):
                                get_line = line.split()
                                if len(get_line) > 1:
                                    path = get_line[1]
                                    # Chercher la ligne Host
                                    host = ""
                                    for h_line in lines:
                                        if h_line.startswith("Host:"):
                                            host = h_line.split("Host:")[1].strip()
                                            break
                                    if host:
                                        full_url = f"http://{host}{path}"
                                        filename = re.findall(r"[^/]+$", path)
                                        filename = filename[0] if filename else "Unknown"
                                        http_requests.append({
                                            "method": "GET",
                                            "url": full_url,
                                            "filename": filename
                                        })
        except Exception as e:
            print(f"Erreur lors de l'analyse d'un paquet : {e}")
            continue
    
    return http_requests, list(ip_list)

# Analyse du fichier PCAP
pcap_file = r"C:\Users\telma\jeuPython\API.pcap"
http_requests, ips = analyse_pcap(pcap_file)

# Vérification des IPs sur VirusTotal
ip_details = {}
for ip in ips:
    ip_details[ip] = check_ip_virustotal(ip)

malicious_ips = [ip for ip, details in ip_details.items() if details["is_malicious"]]

# Vérification des fichiers téléchargés sur VirusTotal
file_details = {}
malicious_files = []
for req in http_requests:
    filename = req['filename']
    file_hash = get_file_hash(filename)
    if file_hash:
        file_details[filename] = check_file_virustotal(file_hash)
    else:
        file_details[filename] = {"is_malicious": False}
    
    # Vérifier si le fichier est dans la liste des fichiers connus comme malveillants
    if filename in KNOWN_MALICIOUS_FILES:
        if not file_details[filename]["is_malicious"]:
            print(f"{filename} marqué comme malveillant (basé sur la liste des fichiers connus).")
            file_details[filename]["is_malicious"] = True
            file_details[filename]["mitre_stages"] = categorize_mitre(["trojan"])  # On suppose que actiV.bin est un trojan
    
    if file_details[filename]["is_malicious"]:
        malicious_files.append(filename)

# Vérifications avant écriture
print("=== Vérifications avant écriture ===")
print("Requêtes HTTP trouvées:", http_requests)
print("Adresses IP extraites:", ips)
print("IP malveillantes détectées:", malicious_ips)
print("Fichiers malveillants détectés:", malicious_files)

# Préparer les données pour le tableau
max_rows = max(len(http_requests), len(malicious_files), len(malicious_ips))

# Colonnes de base
http_requests_col = [req['url'] for req in http_requests] + [""] * (max_rows - len(http_requests))
all_files_col = [req['filename'] for req in http_requests] + [""] * (max_rows - len(http_requests))
malicious_files_col = malicious_files + [""] * (max_rows - len(malicious_files))
malicious_ips_col = malicious_ips + [""] * (max_rows - len(malicious_ips))

# Colonnes supplémentaires pour les détails des IPs malveillantes
ip_malicious_count_col = [""] * max_rows
ip_suspicious_count_col = [""] * max_rows
ip_threat_types_col = [""] * max_rows
ip_attack_types_col = [""] * max_rows
ip_mitre_stages_col = [""] * max_rows
ip_last_analysis_date_col = [""] * max_rows
ip_country_col = [""] * max_rows
ip_city_col = [""] * max_rows
ip_as_owner_col = [""] * max_rows

# Remplir les colonnes pour les IPs malveillantes
for i, ip in enumerate(malicious_ips):
    details = ip_details[ip]
    ip_malicious_count_col[i] = details.get("malicious_count", "N/A")
    ip_suspicious_count_col[i] = details.get("suspicious_count", "N/A")
    ip_threat_types_col[i] = ", ".join(details.get("type_of_threat", [])) if details.get("type_of_threat") else "N/A"
    ip_attack_types_col[i] = ", ".join(details.get("attack_type", [])) if details.get("attack_type") else "N/A"
    ip_mitre_stages_col[i] = ", ".join(details.get("mitre_stages", [])) if details.get("mitre_stages") else "N/A"
    ip_last_analysis_date_col[i] = details.get("last_analysis_date", "N/A")
    ip_country_col[i] = details.get("country", "N/A")
    ip_city_col[i] = details.get("city", "N/A")
    ip_as_owner_col[i] = details.get("as_owner", "N/A")

# Colonnes supplémentaires pour les détails des fichiers malveillants
file_malicious_count_col = [""] * max_rows
file_suspicious_count_col = [""] * max_rows
file_threat_types_col = [""] * max_rows
file_attack_types_col = [""] * max_rows
file_mitre_stages_col = [""] * max_rows
file_last_analysis_date_col = [""] * max_rows
file_first_submission_date_col = [""] * max_rows

# Remplir les colonnes pour les fichiers malveillants
for i, filename in enumerate(malicious_files):
    details = file_details[filename]
    file_malicious_count_col[i] = details.get("malicious_count", "N/A")
    file_suspicious_count_col[i] = details.get("suspicious_count", "N/A")
    file_threat_types_col[i] = ", ".join(details.get("type_of_threat", [])) if details.get("type_of_threat") else "N/A"
    file_attack_types_col[i] = ", ".join(details.get("attack_type", [])) if details.get("attack_type") else "N/A"
    file_mitre_stages_col[i] = ", ".join(details.get("mitre_stages", [])) if details.get("mitre_stages") else "N/A"
    file_last_analysis_date_col[i] = details.get("last_analysis_date", "N/A")
    file_first_submission_date_col[i] = details.get("first_submission_date", "N/A")

# Créer un DataFrame avec pandas
data = {
    "Requêtes HTTP": http_requests_col,
    "Tous les fichiers": all_files_col,
    "Fichiers malveillants": malicious_files_col,
    "Détails fichiers - Nombre de détections malveillantes": file_malicious_count_col,
    "Détails fichiers - Nombre de détections suspectes": file_suspicious_count_col,
    "Détails fichiers - Types de menaces": file_threat_types_col,
    "Détails fichiers - Types d'attaques": file_attack_types_col,
    "Détails fichiers - Étapes MITRE ATT&CK": file_mitre_stages_col,
    "Détails fichiers - Dernière analyse": file_last_analysis_date_col,
    "Détails fichiers - Première soumission": file_first_submission_date_col,
    "IPs malveillantes": malicious_ips_col,
    "Détails IPs - Nombre de détections malveillantes": ip_malicious_count_col,
    "Détails IPs - Nombre de détections suspectes": ip_suspicious_count_col,
    "Détails IPs - Types de menaces": ip_threat_types_col,
    "Détails IPs - Types d'attaques": ip_attack_types_col,
    "Détails IPs - Étapes MITRE ATT&CK": ip_mitre_stages_col,
    "Détails IPs - Dernière analyse": ip_last_analysis_date_col,
    "Détails IPs - Pays": ip_country_col,
    "Détails IPs - Ville": ip_city_col,
    "Détails IPs - Propriétaire AS": ip_as_owner_col,
}
df = pd.DataFrame(data)

# Écriture dans un fichier Excel
excel_file = "résultats.xlsx"
try:
    # Écrire le DataFrame dans un fichier Excel
    df.to_excel(excel_file, index=False, engine="openpyxl")

    # Charger le fichier Excel pour ajuster la largeur des colonnes
    workbook = load_workbook(excel_file)
    worksheet = workbook.active

    # Ajuster la largeur des colonnes
    column_widths = {
        "A": 50,  # Requêtes HTTP
        "B": 20,  # Tous les fichiers
        "C": 20,  # Fichiers malveillants
        "D": 30,  # Détails fichiers - Nombre de détections malveillantes
        "E": 30,  # Détails fichiers - Nombre de détections suspectes
        "F": 30,  # Détails fichiers - Types de menaces
        "G": 30,  # Détails fichiers - Types d'attaques
        "H": 30,  # Détails fichiers - Étapes MITRE ATT&CK
        "I": 30,  # Détails fichiers - Dernière analyse
        "J": 30,  # Détails fichiers - Première soumission
        "K": 20,  # IPs malveillantes
        "L": 30,  # Détails IPs - Nombre de détections malveillantes
        "M": 30,  # Détails IPs - Nombre de détections suspectes
        "N": 30,  # Détails IPs - Types de menaces
        "O": 30,  # Détails IPs - Types d'attaques
        "P": 30,  # Détails IPs - Étapes MITRE ATT&CK
        "Q": 30,  # Détails IPs - Dernière analyse
        "R": 20,  # Détails IPs - Pays
        "S": 20,  # Détails IPs - Ville
        "T": 30,  # Détails IPs - Propriétaire AS
    }
    for col, width in column_widths.items():
        worksheet.column_dimensions[col].width = width

    # Sauvegarder les modifications
    workbook.save(excel_file)
    print(f"Résultats sauvegardés avec succès dans {excel_file}")

except Exception as e:
    print(f"Erreur lors de l'écriture dans le fichier Excel : {e}")