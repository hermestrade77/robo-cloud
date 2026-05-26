import random

def obter_dados():

    # 🔴 SIMULAÇÃO (trocar por MT5 depois)
    data = []

    price = 2000

    for i in range(200):
        price += random.uniform(-5, 5)

        data.append({
            "close": price
        })

    return data