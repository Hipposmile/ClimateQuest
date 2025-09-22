from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Safari WebDriver starten
driver = webdriver.Firefox()

# Deine Registrierungsseite öffnen
driver.get("http://127.0.0.1:8000/personals/register/")

# Kurz warten, bis Seite geladen ist
time.sleep(5)

# Felder ausfüllen
driver.find_element(By.ID, "username").send_keys("botuser123")
driver.find_element(By.ID, "password").send_keys("botpassword456")


# Button klicken (z. B. mit ID oder Name)
driver.find_element(By.ID, "register-button").click()