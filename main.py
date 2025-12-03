import json
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Gemini API üçün lazımi kitabxanalar
from google import genai
from google.genai import types
from google.genai.errors import APIError

# --- Konfiqurasiya ---
API_KEY = "AIzaSyBV0H9QyqN-jwYD-TMPdqNW9LRL5nQdozw"
GEMINI_MODEL = "gemini-2.5-flash"

# --- Mərc URL-ləri ---
urls_array = [
  
    {
        "url": "https://www.misli.az/idman-novleri-canli-merc-detal/futbol/2521108",
        "home_team": "Fenerbahçe",
        "away_team": "Galatasaray"
    },
    {
        "url": "https://www.misli.az/idman-novleri-canli-merc-detal/futbol/2521119",
        "home_team": "Samsunspor",
        "away_team": "Alanyaspor"
    }
 

]

# --- Selenium Setup ---
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--window-size=1920,1080")

# Driver-i başlat
try:
    print("🌍 Chrome brauzeri başladılır (Headless Mode)...")
    driver = webdriver.Chrome(service=Service(), options=chrome_options)
except Exception as e:
    print(f"❌ Xəta: Chrome Driver başlatıla bilmədi. Zəhmət olmasa Chrome brauzerinin quraşdırıldığına əmin olun. {e}")
    exit()

all_data = []

# --- 1. Selenium ilə məlumatların toplanması ---
print("\n--- 1. Mərc Məlumatlarının Toplanması ---")
for item in urls_array:
    url = item["url"]
    home_team_manual = item.get("home_team", "")
    away_team_manual = item.get("away_team", "")

    print(f"\n🔗 Yüklənir: {home_team_manual} vs {away_team_manual} matçı üçün səhifə...")
    driver.get(url)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".marketList"))
        )
        time.sleep(2)

        markets = driver.find_elements(By.CSS_SELECTOR, ".marketList .itemDetailPanel")

        if not markets:
            print("⚠️ Heç bir market tapılmadı. Növbəti URL-ə keçilir.")
            continue

        match_data = {
            "url": url,
            "home_team": home_team_manual,
            "away_team": away_team_manual,
            "markets": []
        }

        for market in markets:
            try:
                market_name_element = market.find_element(By.CSS_SELECTOR, ".marketHeader .marketTitle")
                market_name = market_name_element.text.strip()
                odds_data = []
                odds = market.find_elements(By.CSS_SELECTOR, ".marketOdds .oddItem")

                for odd in odds:
                    try:
                        odd_name = odd.find_element(By.CSS_SELECTOR, ".oddName").text.strip()
                        odd_value = odd.find_element(By.CSS_SELECTOR, ".oddValue").text.strip()
                        odds_data.append({"odd_name": odd_name, "odd_value": odd_value})
                    except:
                        continue

                if odds_data:
                    match_data["markets"].append({
                        "market_name": market_name,
                        "odds": odds_data
                    })
            except:
                continue

        all_data.append(match_data)
        print(f"✅ {len(match_data['markets'])} market tapıldı.")

    except Exception as e:
        print(f"[x] Xəta: Səhifə yüklənməsi zamanı xəta. {e}")

driver.quit()
print("✅ Chrome brauzeri bağlandı. Məlumat toplama bitdi.")

if not all_data:
    print("\n[!] Analiz üçün heç bir məlumat toplanmadı. Proqram dayandırılır.")
    exit()

# --- 2. Gemini API-yə ardıcıl sorğu göndərilməsi ---
print("\n--- 2. Gemini API-yə Analiz Sorğuları Göndərilir ---")
final_analysis_results = []

try:
    client = genai.Client(api_key=API_KEY)

    # Google Search alətini aktivləşdirmək üçün konfiqurasiya
    config = types.GenerateContentConfig(
        tools=[{"google_search": {}}]
    )

    for data in all_data:
        home_team = data['home_team']
        away_team = data['away_team']
        scraped_data_json = json.dumps(data, indent=4, ensure_ascii=False)

        # Matç üçün Xüsusi Prompt
        prompt = (
            f"Aşağıdakı {home_team} vs {away_team} futboll matçı üçün mərc əmsalları (odds) verilmişdir: \n"
            f"```json\n{scraped_data_json}\n```\n\n"
            f"Mərc əmsallarını və Google Search vasitəsilə tapdığın:\n"
            f"1. Komandaların son oyunları, \n"
            f"2. Bir-birləri ilə qarşılaşmaları, \n"
            f"3. Cədvəl vəziyyətləri,\n"
            f"4. Zədə/cəza məlumatlarını analiz et.\n"
            f"Analizin sonunda yalnız və yalnız bu üç kateqoriyada qısa mərc tövsiyəsi ver:\n"
            f"1. Ən Yaxşı Seçim (Ən etibarlı və yaxşı əmsallı proqnoz):\n"
            f"2. 100% Gələ Biləcək Seçim (Çox yüksək ehtimallı, lakin əmsalı aşağı ola bilər):\n"
            f"3. Risqli Seçim (Yüksək əmsallı, lakin uğursuzluq riski yüksək olan proqnoz):\n"
            f"Cavabını yalnız Azərbaycan dilində, bu 3 kateqoriyanı ardıcıl bullet point və ya başlıqlarla təqdim et. Heç bir əlavə əsaslandırma, giriş və ya nəticə yazma."
        )

        print(f"\n⚡ Analiz edilir: {home_team} vs {away_team}...")
        
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=config
            )

            final_analysis_results.append({
                "match": f"{home_team} vs {away_team}",
                "url": data['url'],
                "analysis": response.text
            })
            print(f"✅ {home_team} vs {away_team} üçün analiz uğurla alındı.")

        except APIError as e:
            print(f"❌ Gemini API Xətası ({home_team} vs {away_team}): {e}")
            final_analysis_results.append({
                "match": f"{home_team} vs {away_team}",
                "analysis": f"API sorğusunda xəta baş verdi: {e}"
            })
        except Exception as e:
            print(f"❌ Gözlənilməyən Xəta ({home_team} vs {away_team}): {e}")
            final_analysis_results.append({
                "match": f"{home_team} vs {away_team}",
                "analysis": f"Gözlənilməyən xəta: {e}"
            })

except APIError as e:
    print(f"\n[x] ÜMUMİ GEMINI API XƏTASI: {e}")
    print("❗ Zəhmət olmasa API açarınızın düzgün olduğundan və limitin bitmədiyindən əmin olun.")
    exit()


# --- 3. Bütün Nəticələrin Birgə Təqdimatı ---
print("\n\n##################################################")
print("           🏆 BÜTÜN MATÇLAR ÜZRƏ ÜMUMİ ANALİZ 🏆")
print("##################################################")

for result in final_analysis_results:
    match = result['match']
    analysis = result['analysis']

    print(f"\n\n--- ⚽ MATÇ: {match} ---")
    print("--------------------------------------------------")
    print(analysis)
    print("--------------------------------------------------")

print("\n##################################################")