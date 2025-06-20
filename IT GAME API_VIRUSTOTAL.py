from scapy.all import rdpcap, TCP, IP
from scapy.layers.http import HTTPRequest
import re
import requests
import hashlib
import os
import csv

# Clé API VirusTotal
VT_API_KEY = "1956eab1c727de4fd81c76716322f923013071bdd0886a46e05beb2e44f7bd04"
VT_URL_IP = "https://www.virustotal.com/api/v3/ip_addresses/"
VT_URL_FILE = "https://www.virustotal.com/api/v3/files/"
HEADERS = {"x-apikey": VT_API_KEY} if VT_API_KEY else {}

# Fonction pour vérifier une IP sur VirusTotal
def check_ip_virustotal(ip):
    response = requests.get(f"{VT_URL_IP}{ip}", headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        return data['data']['attributes']['last_analysis_stats']['malicious'] > 0
    return False

# Fonction pour calculer le hash d'un fichier
def get_file_hash(filename):
    hasher = hashlib.sha256()
    try:
        with open(filename, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
    except FileNotFoundError:
        return None

# Fonction pour vérifier un fichier sur VirusTotal
def check_file_virustotal(file_hash):
    response = requests.get(f"{VT_URL_FILE}{file_hash}", headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        return data['data']['attributes']['last_analysis_stats']['malicious'] > 0
    return False

# Fonction pour analyser le fichier PCAP
def analyse_pcap(fichier_pcap):
    packets = rdpcap(fichier_pcap)
    http_requests = []
    ip_list = set()
    
    for packet in packets:
        if packet.haslayer(IP):
            ip_list.add(packet[IP].src)
            ip_list.add(packet[IP].dst)
        
        if packet.haslayer(HTTPRequest):
            host = packet[HTTPRequest].Host.decode() if packet[HTTPRequest].Host else ""
            path = packet[HTTPRequest].Path.decode() if packet[HTTPRequest].Path else ""
            method = packet[HTTPRequest].Method.decode() if packet[HTTPRequest].Method else ""
            full_url = f"http://{host}{path}"
            
            if method == "GET":
                filename = re.findall(r"[^/]+$", path)
                filename = filename[0] if filename else "Unknown"
                http_requests.append({
                    "method": method,
                    "url": full_url,
                    "filename": filename
                })
    
    return http_requests, list(ip_list)

# Analyse du fichier PCAP
pcap_file = r"C:\Users\telma\jeuPython\API.pcap"
http_requests, ips = analyse_pcap(pcap_file)

# Vérification des IPs sur VirusTotal
malicious_ips = [ip for ip in ips if check_ip_virustotal(ip)]

# Vérification des fichiers téléchargés sur VirusTotal
malicious_files = []
for req in http_requests:
    file_hash = get_file_hash(req['filename'])
    if file_hash and check_file_virustotal(file_hash):
        malicious_files.append(req['filename'])

# Affichage des résultats dans le terminal
print("Requêtes HTTP trouvées:", http_requests)
print("Adresses IP extraites:", ips)
print("IP malveillantes détectées:", malicious_ips)
print("Fichiers malveillants détectés:", malicious_files)

# Enregistrement des résultats dans un fichier CSV
csv_file = "resultats_analyse.csv"

if not (http_requests or ips or malicious_ips or malicious_files):
    print("Aucune donnée à écrire dans le fichier CSV.")
else:
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # En-têtes
        writer.writerow(["Catégorie", "Donnée"])

        # Écriture des requêtes HTTP
        writer.writerow(["Requêtes HTTP", ""])
        for req in http_requests:
            writer.writerow(["", f"{req['method']} {req['url']} ({req['filename']})"])

        # Écriture des IPs extraites
        writer.writerow(["Adresses IP extraites", ""])
        for ip in ips:
            writer.writerow(["", ip])

        # Écriture des IPs malveillantes
        writer.writerow(["IP malveillantes détectées", ""])
        for ip in malicious_ips:
            writer.writerow(["", ip])

        # Écriture des fichiers malveillants
        writer.writerow(["Fichiers malveillants détectés", ""])
        for file in malicious_files:
            writer.writerow(["", file])

    print(f"Les résultats ont été enregistrés dans {csv_file}")
