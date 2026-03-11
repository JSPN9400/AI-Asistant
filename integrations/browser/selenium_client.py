from __future__ import annotations

import os
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from assistant.paths import data_dir

os.environ.setdefault("SE_CACHE_PATH", str((data_dir() / ".selenium-cache").resolve()))


class SeleniumBrowser:
    def __init__(self, headless: bool = False):
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        self.driver = webdriver.Chrome(options=options)

    def google_search(self, query: str) -> list[str]:
        self.driver.get("https://www.google.com")
        search_box = self.driver.find_element(By.NAME, "q")
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(2)
        links = self.driver.find_elements(By.CSS_SELECTOR, "a h3")
        titles = [el.text for el in links[:5] if el.text]
        return titles

    def open_url(self, url: str) -> None:
        self.driver.get(url)

    def get_page_title(self) -> str:
        return self.driver.title

    def close(self) -> None:
        self.driver.quit()

