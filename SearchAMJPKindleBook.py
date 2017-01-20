from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import re
import time
import datetime

amazon_jp_kindle_search = "https://www.amazon.co.jp/s/ref=nb_sb_noss_1?__mk_ja_JP=%E3%82%AB%E3%82%BF%E3%82%AB%E3%83%8A" \
                          "&url=search-alias%3Ddigital-text&field-keywords="
amazon_light_novel_ranking = "https://www.amazon.co.jp/s/ref=sr_pg_1?rh=n%3A2250738051%2Cn%3A%212250739051%2Cn%3A" \
                             "2275256051%2Cn%3A2410280051&ie=UTF8&qid=1484064136&ajr=2"
debug = False
total_buy = "まとめ買い"
search_keys = ["狼と香辛料", "キノの旅", "さくら荘のペットな彼女", "冴えない彼女の育てかた", "ダンジョンに出会い",
               "この素晴らしい世界に祝福を", "アクセル・ワールド"]

search_author = ["桜庭 一樹", "小林 泰三", "米澤 穂信"]
mark_books = []
search_page = 4
min_percent = 30
max_price = 350


def get_current_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def find_result_in_page(webdriver):
    return webdriver.find_elements(By.XPATH, "//li[contains(@id, 'result_')]")


def find_price_on_total_buy(webdriver, link):
    return


def check_is_author(result, author):
    for a_tag in result.find_elements_by_class_name("a-link-normal"):
        if author in a_tag.text:
            return True
    for color_secondary in result.find_elements_by_class_name("a-color-secondary"): # for not the first author
        if "span" in color_secondary.tag_name and author in color_secondary.text:
            return True
    return False


def need_mark_book_by_prices(prices):
    for price_percent in filter(lambda price: "%" in price.text, prices):
        percent = re.findall(r'\d+', price_percent.text)
        if len(percent) > 0 and int(percent[0]) >= min_percent:
            return True
    for real_price in filter(lambda price: "￥" in price.text, prices):
        r_price = re.findall(r'\d+', real_price.text.replace(",", ""))
        if len(r_price) > 0 and int(r_price[0]) <= max_price:
            return True
    return False


def read_current_page(webdriver, page, key, file, check_title=True, check_author=False):
    print("current page: {}".format(page))
    file.write("current page: {}".format(page) + "\n")
    results = find_result_in_page(webdriver)
    not_about = []
    for result in results:
        if result is not None:
            book_name = result.find_element_by_tag_name("h2")
            if check_title and key not in book_name.text:
                not_about.append(book_name.text)
                if len(not_about) > 4:  # not about more than 4, then break
                    raise FileExistsError("key not found!")
                continue
            if check_author and not check_is_author(result, key):
                not_about.append(book_name.text)
                if len(not_about) > 4:  # not about more than 4, then break
                    raise FileExistsError("key not found!")
                continue
            prices = result.find_elements_by_class_name("a-color-price")
            mark_book = need_mark_book_by_prices(prices)
            link = result.find_element_by_class_name("s-access-detail-page").get_attribute("href")
            print("book name:" + book_name.text)
            print(" ".join([price.text for price in prices]))
            print("link:" + link)
            file.write("book name:" + book_name.text + "\n")
            file.write(" ".join([price.text for price in prices]) + "\n")
            file.write("Link:" + link + "\n")
            if mark_book:
                mark_books.append((book_name.text, " ".join([price.text for price in prices]), link))


def get_books(driver, url, filename, check_title=True, check_author=False):
    driver.get(url)
    page_n = driver.find_element(By.ID, "pagn")
    page = 1
    if page_n is not None:
        page_next_link = page_n.find_element(By.CLASS_NAME, "pagnRA")
        pages = page_n.find_elements(By.CLASS_NAME, "pagnLink")
        print("current pages:" + " ".join([page.text for page in pages]))
        with open(filename + ".txt", "w") as file:
            if page_next_link is not None:
                while page <= search_page:
                    try:
                        read_current_page(driver, page, filename, file, check_title, check_author)
                    except FileExistsError as e:
                        print("file not found, stop search")
                        break
                    try:
                        link = WebDriverWait(driver, 8).until(EC.visibility_of_element_located((By.ID, "pagnNextLink")))
                    except Exception as e:
                        link = None
                    if link is None:
                        print("link null, cannot jump")
                        break
                    ActionChains(driver).move_to_element(link) \
                        .send_keys(Keys.ARROW_DOWN) \
                        .send_keys(Keys.ARROW_DOWN).perform()
                    time.sleep(2)
                    link.click()
                    page += 1


def search_by_title(driver, search_key):
    get_books(driver, amazon_jp_kindle_search + search_key, search_key)


def search_by_author(driver, author):
    get_books(driver, amazon_jp_kindle_search + author, author, check_title=False, check_author=True)


options = webdriver.ChromeOptions()
options.add_argument("--incognito")  # private mode

driver = webdriver.Chrome(chrome_options=options)

try:
    for author in search_author:
        search_by_author(driver, author)
    for key in search_keys:
        search_by_title(driver, key)
    get_books(driver, amazon_light_novel_ranking, get_current_time() + "_" + "ranking", False)
except Exception as e:
    print(e)
time.sleep(5)
if len(mark_books) > 0:
    print("mark books")
    with open(get_current_time() + "_" + "mark_book.txt", "w") as mark_file:
        for book in mark_books:
            for text in book:
                mark_file.write(str(text) + "\n")
driver.close()
