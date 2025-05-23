import requests

def enviar_notificacao_telegram(token, chat_id, mensagem):
    url = f"https://api.telegram.org/bot{"8102034090:AAEJFwf4Hx7aaHEKzUx0Ob6lQE_GWuVQRzQ"}/sendMessage"
    data = {
        "chat_id": 6113530990,
        "text": mensagem,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=data)
    return response.ok
