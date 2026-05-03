import requests
import os
import webbrowser

API_URL = "http://localhost:8080"
API_KEY = "tu_super_clave_secreta_123"
INSTANCE_NAME = "MiBot"

headers = {
    "apikey": API_KEY,
    "Content-Type": "application/json"
}

print("Obteniendo nuevo código QR...")
try:
    res = requests.get(f"{API_URL}/instance/connect/{INSTANCE_NAME}", headers=headers)
    data = res.json()
    
    qr_base64 = data.get("base64", "")
    
    if qr_base64:
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
        
        print("¡Listo! Abriendo el código QR en tu navegador...")
        webbrowser.open(f"file://{qr_file}")
    else:
        print("No se recibió QR. Detalles:", data)
except Exception as e:
    print(f"Error: {e}")
