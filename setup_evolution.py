import requests
import json
import webbrowser
import os

API_URL = "http://localhost:8080"
API_KEY = "tu_super_clave_secreta_123"
INSTANCE_NAME = "MiBot"

headers = {
    "apikey": API_KEY,
    "Content-Type": "application/json"
}

print("1. Creando instancia en Evolution API...")
create_data = {
    "instanceName": INSTANCE_NAME,
    "qrcode": True,
    "integration": "WHATSAPP-BAILEYS"
}

try:
    res = requests.post(f"{API_URL}/instance/create", json=create_data, headers=headers)
    data = res.json()
    
    # Extraer el código QR en Base64 que nos devuelve Evolution API
    qr_base64 = data.get("qrcode", {}).get("base64", "")
    
    if qr_base64:
        # Creamos un archivo HTML rápido para poder ver la imagen
        html_content = f"""
        <html>
        <body style="display:flex; justify-content:center; align-items:center; height:100vh; background-color:#f0f0f0;">
            <div style="text-align:center; background:white; padding:2rem; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                <h2 style="font-family:sans-serif;">Escanea este código con tu WhatsApp</h2>
                <img src="{qr_base64}" alt="QR Code" style="width: 300px; height: 300px;" />
            </div>
        </body>
        </html>
        """
        qr_file = os.path.abspath("qr.html")
        with open(qr_file, "w") as f:
            f.write(html_content)
        
        print("Abriendo el código QR en tu navegador...")
        webbrowser.open(f"file://{qr_file}")
    else:
        print("⚠️ La instancia ya existe o no se pudo generar el QR.")
        print("Si ya existe, Evolution no te da un QR nuevo hasta que borres la instancia o te desconectes.")
        
except Exception as e:
    print(f"Error al crear instancia: {e}")

print("\n2. Configurando Webhook para que se comunique con FastAPI...")
webhook_data = {
    "webhook": {
        "enabled": True,
        "url": "http://host.docker.internal:8000/webhook",
        "byEvents": False,
        "base64": False,
        "events": [
            "MESSAGES_UPSERT"
        ]
    }
}

try:
    res2 = requests.post(f"{API_URL}/webhook/set/{INSTANCE_NAME}", json=webhook_data, headers=headers)
    if res2.status_code in [200, 201]:
        print("✅ Webhook configurado exitosamente!")
    else:
        print(f"❌ Error al configurar webhook: {res2.text}")
except Exception as e:
    print(f"Error en webhook: {e}")

print("\n--- PROCESO TERMINADO ---")
print("1. Escanea el QR si se abrió en tu navegador.")
print("2. En otra terminal, levanta tu bot usando: uvicorn main:app --reload")
