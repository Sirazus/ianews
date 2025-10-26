# Estándar
import os
import re
import sys
import time
from datetime import datetime, timedelta

# Localización y zona horaria
from zoneinfo import ZoneInfo 

# Peticiones y configuración
import requests
import configparser

# Bibliotecas de correo (Comentadas por solicitud)
# import smtplib
# from email.mime.text import MIMEText

# Traducción
# from googletrans import Translator # Eliminado
from deep_translator import GoogleTranslator # Añadido

# --- INICIO DE CAMBIO ---
# Mantenemos 'translator' como variable global si se usa en múltiples sitios,
# pero lo inicializaremos dentro de main() para configurar 'source' y 'target' una vez.
# O, si solo se usa en main, lo definimos allí.
# Por ahora, solo importamos.
# translator = Translator() # Eliminado
# --- FIN DE CAMBIO ---


# Obtener variables de entorno
def get_env_variable(name):
    try:
        return os.environ[name]
    except KeyError:
        # Modificado para no salir si faltan variables de correo
        print(f"Advertencia: Variable de entorno {name} no encontrada.")
        return None

# --- FUNCIONALIDAD DE NOTION Y CORREO DESACTIVADA ---
# La función fetch_notion_users se usaba para obtener correos, ya no es necesaria.
# def fetch_notion_users(api_key, database_id):
#     url = f"https://api.notion.com/v1/databases/{database_id}/query"
#     headers = {
#         "Authorization": f"Bearer {api_key}",
#         "Notion-Version": "2021-05-13",
#         "Content-Type": "application/json"
#     }
#     response = requests.post(url, headers=headers)
#     if response.status_code != 200:
#         raise Exception("Failed to fetch data from Notion API: " + response.text) 
#     data = response.json()
#     users = []
#     for result in data.get("results", []):
#         user_data = {}
#         properties = result.get("properties", {})
#         
#         # Extraer nombre (ajusta 'Name' si la propiedad se llama diferente)
#         if "Name" in properties and properties["Name"]["type"] == "title":
#             user_data["name"] = properties["Name"]["title"][0]["plain_text"]
#             
#         # Extraer email (ajusta 'Email' si la propiedad se llama diferente)
#         if "Email" in properties and properties["Email"]["type"] == "email":
#             user_data["email"] = properties["Email"]["email"]
#             
#         if user_data:
#             users.append(user_data)
#     return users

# Configuración de correo (Comentada)
# MAIL_HOST = get_env_variable('MAIL_HOST')
# MAIL_PORT = get_env_variable('MAIL_PORT')
# MAIL_USER = get_env_variable('MAIL_USER')
# MAIL_PASS = get_env_variable('MAIL_PASS')
# SENDER = get_env_variable('SENDER')

# Función de envío de correo (Comentada)
# def send_email(receiver, title, content):
#     if not all([MAIL_HOST, MAIL_PORT, MAIL_USER, MAIL_PASS, SENDER]):
#         print("Faltan variables de entorno para el correo. Omitiendo envío.")
#         return
# 
#     message = MIMEText(content, 'html', 'utf-8')
#     message['From'] = Header("Noticias Diarias", 'utf-8')
#     message['To'] = Header(receiver, 'utf-8')
#     message['Subject'] = Header(title, 'utf-8')
# 
#     try:
#         smtpObj = smtplib.SMTP_SSL(MAIL_HOST, MAIL_PORT)
#         smtpObj.login(MAIL_USER, MAIL_PASS)
#         smtpObj.sendmail(SENDER, [receiver], message.as_string())
#         print(f"Correo enviado exitosamente a {receiver}")
#     except smtplib.SMTPException as e:
#         print(f"Error al enviar correo a {receiver}: {e}")

def main():
    config = configparser.ConfigParser()
    config_path = 'config.ini'

    if not os.path.exists(config_path):
        print(f"Error: Archivo de configuración '{config_path}' no encontrado.")
        sys.exit(1)
        
    config.read(config_path, encoding='utf-8')

    # --- OBTENCIÓN DE USUARIOS DESACTIVADA ---
    # api_key = get_env_variable('NOTION_API_KEY')
    # database_id = get_env_variable('NOTION_DATABASE_ID')
    # if not api_key or not database_id:
    #     print("Faltan variables de Notion. Omitiendo la obtención de usuarios.")
    #     notion_users = []
    # else:
    #     try:
    #         notion_users = fetch_notion_users(api_key, database_id)
    #     except Exception as e:
    #         print(f"Error al obtener usuarios de Notion: {e}")
    #         notion_users = []

    tz = ZoneInfo('Asia/Shanghai')
    yesterday = datetime.now(tz) - timedelta(days=1)
    year_month = yesterday.strftime("%Y-%m")
    yesterday_day = yesterday.strftime("%d")

    yesterday_folder_path = f"news_archive/{year_month}"
    yesterday_news_filename = f"{yesterday_folder_path}/{yesterday_day}.md"
    
    subject = f"Noticias de Ayer - {yesterday.strftime('%Y-%m-%d')}"

    if not os.path.exists(yesterday_news_filename):
        print(f"Archivo de noticias no encontrado: {yesterday_news_filename}")
        return

    # Leer noticias de ayer
    with open(yesterday_news_filename, 'r', encoding='utf-8') as f:
        yesterday_news = f.read()

    # Extraer títulos y links (Asumiendo formato <p><a href="...">...</a></p>)
    # Ajusta este patrón si el formato de tu .md es diferente
    pattern = r'<p><a href=\"(.*?)\">(.*?)</a></p>'
    matches = re.findall(pattern, yesterday_news)
    
    if not matches:
        # Fallback por si el formato es Markdown simple: [texto](link)
        pattern_md = r'\[(.*?)\]\((.*?)\)'
        matches_md = re.findall(pattern_md, yesterday_news)
        # Reordenar para que coincida con (link, title)
        matches = [(link, title) for title, link in matches_md]

    if not matches:
        print("No se encontraron noticias con el patrón esperado. Verifique el formato del archivo .md")
        return

    # Traducir títulos al español
    print("Iniciando traducción al español...")
    
    # --- INICIO DE CAMBIO ---
    # Inicializamos el traductor con los idiomas de origen y destino
    translator = GoogleTranslator(source='zh-CN', target='es')
    # --- FIN DE CAMBIO ---
    
    translated_news = []
    for link, title in matches:
        try:
            # Añadimos un pequeño retraso para no sobrecargar la API de traducción
            time.sleep(0.5) 
            # --- INICIO DE CAMBIO ---
            # La sintaxis de deep-translator es más simple
            title_es = translator.translate(title)
            # title_es = translator.translate(title, src='zh-cn', dest='es').text # Eliminado
            # --- FIN DE CAMBIO ---
        except Exception as e:
            print(f"Error traduciendo: {title} -> {e}")
            title_es = f"{title} (Traducción fallida)"  # Fallback
        translated_news.append({'link': link, 'title': title_es})
        print(f"Traducido: {title} -> {title_es}")

    # Generar HTML (o Markdown) con títulos traducidos
    formatted_news = ''
    for news in translated_news:
        # Guardamos en el mismo formato que leímos (HTML <p><a>)
        formatted_news += f'<p><a href=\"{news["link"]}\">{news["title"]}</a></p>\n'
        # Si prefieres formato Markdown:
        # formatted_news += f"- [{news['title']}]({news['link']})\n"


    # Guardar en archivo local
    output_folder = "news_archive/es" # Carpeta para noticias en español
    os.makedirs(output_folder, exist_ok=True)
    output_file = f"{output_folder}/{yesterday.strftime('%Y-%m-%d')}.md"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# {subject}\n\n")
        f.write(formatted_news)

    print(f"\nNoticias traducidas y guardadas exitosamente en: {output_file}")

    # --- BUCLE DE ENVÍO DE CORREO DESACTIVADO ---
    # print("\nIniciando envío de correos...")
    # for user in notion_users:
    #     if user.get('email'):
    #         print(f"Enviando email a {user['email']}...")
    #         send_email(user['email'], subject, formatted_news)
    #     else:
    #         print(f"Usuario {user.get('name', 'Desconocido')} no tiene email.")

    print("Proceso completado (solo guardado local).")

if __name__ == '__main__':
    main()

