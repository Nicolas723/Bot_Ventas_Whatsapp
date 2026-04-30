from db import init_db

if __name__ == "__main__":
    print("Conectando a Supabase y creando tablas...")
    try:
        init_db()
        print("✅ Tablas creadas correctamente en Supabase.")
    except Exception as e:
        print(f"❌ Error: {e}")
