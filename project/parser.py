from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep

from models_back import (
    BankBranch, Coords, ExchangeRate, BankOrg, Currency
)

USD = 'https://myfin.by/currency/usd'

class Parser:
    def __init__(self, debug_flag: bool = False):
        try:
            options = webdriver.ChromeOptions()
            self.debug_flag = debug_flag
            if not self.debug_flag:
                options.add_argument('--headless')
            self.driver = webdriver.Chrome(options=options)
        except Exception as e:
            print(f'Ошибка при создании драйвера: {e}')
    
    def _get_page(self, url) -> webdriver.Chrome:
        self.driver.get(url)
        return self.driver

    def _press_button(self, button_xPath: str):
        try:
            button = WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, button_xPath))
            )
            button.click()
            if self.debug_flag:
                print(f'Нажата кнопка: {button_xPath}')
        except Exception as e:
            print(f'Кнопка {button_xPath} не была нажата. Ошибка: {e}')
    
    def get_branch(self, url: str, now_open: bool = True) -> list[BankBranch]:
        driver = self._get_page(url)
        answer = []

        target_currency = self._extract_currency_from_url(url)
        print(f"[DEBUG] Парсинг валюты: {target_currency} (из URL: {url})")

        self._press_button('/html/body/div[4]/div/div[3]/button[1]')
        sleep(2)
        self._press_button('//*[@id="deposit-rate-tabs"]/li[2]/a')
        if now_open:
            self._press_button('//*[@id="deposit-rate-tabs"]/li[2]/a')
        sleep(3)
        table = driver.find_element(By.XPATH, '//*[@id="currency-table-filials"]/table')
        sleep(7)

        i = 2
        while True:
            try:
                if i % 20 == 0:
                    self._press_button('//*[@id="load-more-filials"]')
                    sleep(2)

                el = table.find_element(By.ID, f'bank-row-{i}')
                courses = el.find_elements(By.CLASS_NAME, 'currencies-courses__currency-cell')
                tds = el.find_elements(By.TAG_NAME, 'td')
                adress = tds[0].find_element(By.CLASS_NAME, 'currencies-courses__branch-name').text
                bank_name = tds[0].find_element(By.CLASS_NAME, 'currencies-courses__bank-name').text
                sell_course = courses[0].text.strip()
                buy_course = courses[1].text.strip()

                if not sell_course or not buy_course:
                    i += 2
                    continue

                coords = tds[7].get_attribute("data-fillial-coords")
                lat, lon = coords.replace('"', '').replace('[', '').replace(']', '').split(',')

                ans = BankBranch(
                    bank_org=BankOrg(bank_name),
                    address=adress,
                    coords=Coords(float(lon), float(lat)),
                    exchange_rates=(
                        ExchangeRate(curr_from=Currency.BYN, curr_to=target_currency, rate=float(buy_course)),
                        ExchangeRate(curr_from=target_currency, curr_to=Currency.BYN, rate=float(sell_course))
                    ),
                )
                answer.append(ans)
                i += 2

            except Exception as e:
                print(f'[DEBUG] Закончились отделения. Всего загружено: {len(answer)}')
                break

        return answer

    def _extract_currency_from_url(self, url: str) -> Currency:
        """Определяет валюту из URL типа 'https://myfin.by/currency/usd'"""
        currency_code = url.split('/')[-1].upper()
        try:
            return Currency[currency_code]
        except KeyError:
            return Currency.USD

    def __del__(self):
        try:
            self.driver.quit()
            print('Parser stopped')
        except:
            pass

if __name__ == "__main__":
    par = Parser(debug_flag=True)
    res = par.get_branch(USD)
    print(res)