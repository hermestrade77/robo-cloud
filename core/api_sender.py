import requests

# ======================================
# URL DO RAILWAY
# ======================================

RAILWAY_API = "https://robo-cloud-production.up.railway.app"

# ======================================
# SEND
# ======================================

def send_data(data):

    print("\n====================")
    print("ENVIANDO DADOS...")
    print(data)

    try:

        response = requests.post(

            RAILWAY_API,

            json=data,

            timeout=15
        )

        print("STATUS:", response.status_code)

        print("RESPOSTA:", response.text)

    except Exception as e:

        print("ERRO API:", e)