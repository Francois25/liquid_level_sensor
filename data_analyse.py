from datetime import datetime
import json

def send_data(mesure):
    date = datetime.today()
    date = date.strftime("%d.%m.%y %X")
    with open("niveau_eau.json", "r") as f:
        donnees = json.load(f)
    donnees[date]=mesure
    with open('niveau_eau.json', 'w') as json_file:
        json.dump((donnees), json_file, indent=0, ensure_ascii=False)
        print("Valeur ajouter au fichier json : ", date, mesure)
    return