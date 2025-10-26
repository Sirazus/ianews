import os
import re
import time
import ssl
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller  # CORREGIDO: era chromedriver_autautoinstaller

# Deshabilitar verificación de certificado SSL
ssl._create_default_https_context = ssl._create_unverified_context

# Constantes
MAX_RETRIES = 3
WAIT_TIME = 3
TIMEOUT = 10

def setup_driver():
    """Configura y retorna Selenium WebDriver"""
    chromedriver_autoinstaller.install()  # Instala automáticamente ChromeDriver compatible
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=options)

# Función de puntuación
def calculate_score(valuable, unvaluable):
    total = valuable + unvaluable
    if total == 0:
        return 0
    elif valuable == 0 and unvaluable != 0:
        return -10
    elif unvaluable == 0 and valuable != 0:
        return 10 + valuable
    else:
        return (valuable / total) * 10

def adjust_value_based_on_time(value, news_time_str):
    """Ajusta el valor según el tiempo de publicación de la noticia"""
    try:
        # Asume formato news_time_str como "YYYY-MM-DD HH:MM:SS"
        news_time = datetime.strptime(news_time_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        hours_diff = (now - news_time).total_seconds() / 3600
        if hours_diff <= 1:
            return value * 1.5
        elif hours_diff <= 3:
            return value * 1.2
        elif hours_diff > 24:
            return value * 0.8
        return value
    except ValueError:
        return value

def fetch_news_values(news_list, driver):
    """Obtiene las puntuaciones de valor de las noticias"""
    values_dict = {}
    for i, news in enumerate(news_list):
        link = news['link']
        if "t.me" in link or "mp.weixin.qq.com" in link:
            values_dict[link] = 0
            continue
        
        print(f"Procesando noticia {i+1}/{len(news_list)}: {news['title'][:60]}...")
        
        for attempt in range(MAX_RETRIES):
            try:
                driver.get(link)
                WebDriverWait(driver, TIMEOUT).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Intentar múltiples formas de obtener "vale" y "no vale"
                valuable = 0
                unvaluable = 0
                
                try:
                    valuable_element = driver.find_element(By.XPATH, "//*[contains(text(), '值得')]")
                    valuable_text = valuable_element.text
                    valuable_match = re.search(r'(\d+)', valuable_text)
                    if valuable_match:
                        valuable = int(valuable_match.group(1))
                except NoSuchElementException:
                    pass  # No encontrado, no pasa nada

                try:
                    unvaluable_element = driver.find_element(By.XPATH, "//*[contains(text(), '不值得')]")
                    unvaluable_text = unvaluable_element.text
                    unvaluable_match = re.search(r'(\d+)', unvaluable_text)
                    if unvaluable_match:
                        unvaluable = int(unvaluable_match.group(1))
                except NoSuchElementException:
                    pass  # No encontrado, no pasa nada

                # Intentar plan B
                if valuable == 0 and unvaluable == 0:
                    try:
                        valuable = int(driver.find_element(By.ID, "news_value_up").text)
                        unvaluable = int(driver.find_element(By.ID, "news_value_down").text)
                    except (NoSuchElementException, ValueError):
                        pass

                score = calculate_score(valuable, unvaluable)
                
                # Intentar obtener tiempo
                news_time_str = ""
                try:
                    # Intentar múltiples formas de obtener tiempo
                    time_element = driver.find_element(By.CSS_SELECTOR, "time.ago")
                    news_time_str = time_element.get_attribute('datetime')  # Asume formato "YYYY-MM-DD HH:MM:SS"
                except NoSuchElementException:
                    try:
                        time_element = driver.find_element(By.CSS_SELECTOR, ".meta-date")
                        news_time_str = time_element.text
                        # Asume formato "YYYY年MM月DD日 HH:MM" -> "YYYY-MM-DD HH:MM:SS"
                        if '年' in news_time_str:
                             news_time_obj = datetime.strptime(news_time_str, "%Y年%m月%d日 %H:%M")
                             news_time_str = news_time_obj.strftime("%Y-%m-%d %H:%M:%S")
                    except NoSuchElementException:
                        news_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Fallback

                adjusted_score = adjust_value_based_on_time(score, news_time_str)
                values_dict[link] = adjusted_score
                
                print(f"  > Puntuación: {score:.2f}, ajustada: {adjusted_score:.2f} (vale: {valuable}, no vale: {unvaluable})")
                
                time.sleep(WAIT_TIME)
                break  # Éxito, salir del bucle de reintentos

            except TimeoutException:
                print(f"  > Enlace timeout: {link} (intento {attempt + 1}/{MAX_RETRIES})")
                if attempt == MAX_RETRIES - 1:
                    values_dict[link] = 0
            except Exception as e:
                print(f"  > Error al procesar: {link} (intento {attempt + 1}/{MAX_RETRIES}) - {e}")
                if attempt == MAX_RETRIES - 1:
                    values_dict[link] = 0
                    
    return values_dict

def parse_news(news_md):
    """
    Parsea lista de noticias en Markdown
    Soporta formatos:
    - HTML: <p><a href="LINK">TITLE</a></p>
    - Markdown: [TITLE](LINK)
    """
    news_list = []
    
    # Intentar formato HTML primero
    pattern_html = re.compile(r'<p><a href="(.*?)">(.*?)</a></p>')
    matches = pattern_html.findall(news_md)
    
    if matches:
        for link, title in matches:
            news_list.append({'link': link, 'title': title})
        return news_list
    
    # Fallback: intentar formato Markdown
    pattern_md = re.compile(r'\[(.*?)\]\((.*?)\)')
    matches_md = pattern_md.findall(news_md)
    
    if matches_md:
        for title, link in matches_md:
            news_list.append({'link': link, 'title': title})
    
    return news_list

def sort_news_by_value(news_list, values_dict):
    """Ordena noticias por puntuación de valor"""
    # Filtrar noticias con puntuación -10 ("no vale la pena")
    filtered_list = [news for news in news_list if values_dict.get(news['link'], 0) > -10]
    
    # Ordenar por puntuación descendente
    sorted_list = sorted(filtered_list, key=lambda x: values_dict.get(x['link'], 0), reverse=True)
    return sorted_list

def format_news_to_md(sorted_news):
    """Formatea noticias ordenadas de vuelta a Markdown"""
    md_content = ""
    for news in sorted_news:
        md_content += f"<p><a href=\"{news['link']}\">{news['title']}</a></p>\n"
    return md_content

def switch_to_parent_if_src():
    """Verifica si el directorio actual termina en 'src', si es así cambia al directorio padre"""
    current_dir = os.getcwd()
    base_name = os.path.basename(current_dir)

    if base_name == 'src':
        parent_dir = os.path.dirname(current_dir)
        os.chdir(parent_dir)
        print(f'Cambiado al directorio padre: {parent_dir}')

def process_yesterday_news(yesterday, yesterday_news_filename):
    """Procesa las noticias de ayer"""
    with open(yesterday_news_filename, 'r', encoding='utf-8') as f:
        yesterday_news = f.read()
    if "(sorted)" in yesterday_news:
        print(f"{yesterday_news_filename} ya está ordenado, saltando procesamiento")
        return
    news_list = parse_news(yesterday_news)
    with setup_driver() as driver:
        values_dict = fetch_news_values(news_list, driver)
    sorted_news = sort_news_by_value(news_list, values_dict)
    formatted_md = format_news_to_md(sorted_news)
    with open(yesterday_news_filename, 'w', encoding='utf-8') as f:
        f.write(f"# 今日新闻 - {yesterday.strftime('%Y年%m月%d日')}(sorted)\n")
        f.write(formatted_md)
    print(f"Noticias ordenadas exitosamente y guardadas en {yesterday_news_filename}")

def main():
    start_time = time.time()
    switch_to_parent_if_src()
    tz = ZoneInfo('Asia/Shanghai')
    now = datetime.now(tz)
    yesterday = now - timedelta(days=1)
    year_month = yesterday.strftime("%Y-%m")
    yesterday_day = yesterday.strftime("%d")
    yesterday_folder_path = f"news_archive/{year_month}"
    yesterday_news_filename = f"{yesterday_folder_path}/{yesterday_day}.md"

    if os.path.exists(yesterday_news_filename):
        print(f"Comenzando a procesar {yesterday_news_filename}...")
        try:
            process_yesterday_news(yesterday, yesterday_news_filename)
        except Exception as e:
            print(f"Error al procesar {yesterday_news_filename}: {e}")
    else:
        print(f"Archivo {yesterday_news_filename} no existe, saltando procesamiento")

    end_time = time.time()
    print(f"Script completado, tiempo total: {end_time - start_time:.2f} segundos")

if __name__ == "__main__":
    main()