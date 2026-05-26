import requests

RAILWAY_API = "http://127.0.0.1:8080/update"

def send_data(data):

    print("\n====================")
    print("ENVIANDO API...")
    print(data)

    try:

        response = requests.post(

            RAILWAY_API,

            json=data,

            timeout=10
        )

        print("STATUS:", response.status_code)

        print("RESPOSTA:", response.text)

    except Exception as e:

        print("ERRO API:", e)