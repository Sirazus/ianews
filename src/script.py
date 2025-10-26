import os
import time
import difflib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import chromedriver_autoinstaller  # 确保导入 chromedriver_autoinstaller

def setup_driver():
    """设置并返回Selenium WebDriver"""
    chromedriver_autoinstaller.install()  # 自动安装匹配的 ChromeDriver
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"Error setting up driver: {e}")
        raise

def fetch_all_news(date_str):
    """
    Scrapea la página de archivo de un día específico (método mucho más rápido).
    Recibe la fecha en formato 'YYYY-MM-DD'.
    """
    driver = setup_driver()
    url = f"https://www.ithome.com/list/{date_str}.html"
    print(f"Abriendo URL de archivo (método superior): {url}")
    
    driver.get(url)

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.datel li'))
        )
        print("Página de archivo cargada.")
    except Exception as e:
        print(f"No se pudo cargar la lista del archivo: {e}")
        driver.quit()
        return []

    news_items = driver.find_elements(By.CSS_SELECTOR, 'ul.datel li')
    print(f"Se encontraron {len(news_items)} artículos en total.")

    news_data = []
    for item in news_items:
        try:
            category = item.find_element(By.CSS_SELECTOR, 'a.c').text
            title = item.find_element(By.CSS_SELECTOR, 'a.t').text
            link = item.find_element(By.CSS_SELECTOR, 'a.t').get_attribute('href')
            time_str = item.find_element(By.CSS_SELECTOR, 'i').text
            time_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            news_data.append({'category': category, 'title': title, 'link': link, 'time': time_obj})
        
        except Exception as e:
            print(f"Error parseando un artículo: {e}. Saltando.") 
            
    driver.quit()
    print("WebDriver cerrado.")
    return news_data

def ensure_dir_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def write_news_file(filename, date_str):
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# 今日新闻 - {date_str}\n")
            
def is_similar(entry1, entry2, threshold=0.9):
    ratio = difflib.SequenceMatcher(None, entry1, entry2).ratio()
    ratio_rounded = round(ratio, 4)  # 保留两位小数
    if 0.99 > ratio_rounded >= threshold:
        print(f"Detectando similitud (puede ser duplicado): {entry1[:50]}...")
        print(f"Similaridad: {ratio_rounded}")
    return ratio_rounded > threshold

def save_news_to_markdown(date_obj, new_news):
    """ 
    Modificado para recibir un objeto 'date' (el de ayer)
    y guardar TODO lo de la página, sin filtrar por fecha.
    """
    year_month = date_obj.strftime("%Y-%m")
    folder_path = f"news_archive/{year_month}"
    ensure_dir_exists(folder_path)
    
    month_news_filename = f"{folder_path}/00.md"
    
    # El archivo de destino es el de AYER (ej. 26.md)
    day_filename = f"{folder_path}/{date_obj.strftime('%d')}.md"
    write_news_file(day_filename, date_obj.strftime('%Y年%m月%d日'))
    
    # Cargar las noticias que ya existen para evitar duplicados
    if os.path.exists(month_news_filename):
        with open(month_news_filename, 'r', encoding='utf-8') as f:
            existing_month_news = f.read()
    else:
        existing_month_news = "# 本月新闻\n"
        with open(month_news_filename, 'w', encoding='utf-8') as f:
            f.write(existing_month_news)
    
    news_set = set(existing_month_news.splitlines())
    news_written_count = 0
    
    for news in new_news:
        markdown_entry = f"- [{news['title']}]({news['link']})\n"
        
        # --- ¡CAMBIO IMPORTANTE! ---
        # Hemos eliminado el filtro de fecha:
        # if news_time.date() == date_obj.date():
        #
        # Ahora confiamos en que la página que scrapeamos (26.html)
        # contiene las noticias que queremos guardar en 26.md.
        #
        # Solo filtramos por duplicados:
        
        is_new_entry = all(not is_similar(markdown_entry, existing_entry) for existing_entry in news_set)
        
        if is_new_entry:
            news_set.add(markdown_entry)
            news_written_count += 1
            
            # Escribimos en el archivo mensual
            with open(month_news_filename, 'a', encoding='utf-8') as month_file:
                month_file.write(markdown_entry)
            
            # Escribimos en el archivo de AYER (ej. 26.md)
            with open(day_filename, 'a', encoding='utf-8') as day_file:
                day_file.write(markdown_entry)
        # else:
            # Opcional: imprimir si se salta por duplicado
            # print(f"Noticia saltada (duplicada): {news['title']}")

    if news_written_count > 0:
        print(f"新闻保存成功，本次更新了 {news_written_count} 条新闻。")
    else:
        print("没有新的新闻需要更新。")

def switch_to_parent_if_src():
    """检查当前目录的最后一级是否是src，如果是，则切换到上一级目录"""
    current_dir = os.getcwd()
    base_name = os.path.basename(current_dir)

    if base_name == 'src':
        parent_dir = os.path.dirname(current_dir)
        os.chdir(parent_dir)
        print(f'切换到上一级目录: {parent_dir}')

def main():
    start_time = time.time()
    switch_to_parent_if_src()
    tz = ZoneInfo('Asia/Shanghai') # Hora de China
    now = datetime.now(tz)
    
    # 1. Calculamos la fecha de AYER (según la hora de China)
    yesterday = now - timedelta(days=1)
    
    print("当前时间 (China)：", now.strftime("%Y-%m-%d %H:%M:%S %Z"))
    
    # 2. Formateamos la fecha de AYER para la URL
    date_str_for_url = yesterday.strftime('%Y-%m-%d')
    
    print(f"开始爬取 {date_str_for_url} 的所有新闻...")
    try:
        # 3. Pasamos esa fecha a la función de scrapeo
        new_news = fetch_all_news(date_str_for_url)
        
        print(f"新闻爬取完成，共爬取到 {len(new_news)} 条新闻。")
        
        # 4. Guardamos usando el objeto 'yesterday'
        save_news_to_markdown(yesterday, new_news)
        
    except Exception as e:
        print(f"An error occurred: {e}")
        
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"写入新闻完成，总耗时: {elapsed_time:.2f} 秒")

if __name__ == '__main__':
    main()