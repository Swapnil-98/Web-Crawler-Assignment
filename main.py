from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from selectorlib import Extractor
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import presence_of_element_located
import numpy as np
import requests
import json
import time

from selenium.webdriver.support.select import Select

def search_amazon(item, user_defined_sorting, low_price=None, high_price=None, pincode=400072):
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get('https://www.amazon.in/')
    wait = WebDriverWait(driver, 5)
    search_box = driver.find_element_by_id('twotabsearchtextbox').send_keys(item)
    search_button = driver.find_element_by_id("nav-search-submit-text").click()

    driver.implicitly_wait(10)

   

    if low_price is not None and high_price is not None:
        try:
            low_price_text = driver.find_element_by_id("low-price").send_keys(low_price)
            high_price_text = driver.find_element_by_id("high-price").send_keys(high_price)
            # go_button = driver.find_element_by_xpath(price_button_xpath).click()
            # go_button = driver.find_element_by_class_name("a-button-input").click()
            go_button = driver.find_element_by_xpath("//li[@id='p_36/price-range']//span[@class='a-list-item']//form//span[@class='a-button a-spacing-top-mini a-button-base s-small-margin-left']//span[@class='a-button-inner']//input[@type='submit']").click()
        except NoSuchElementException:
            print("Low price, high price fields not found...")
            print("Ignoring...")
    else:
        print("Either of the prices were not given, ignoring this step...")

    address_open = driver.find_element_by_id("glow-ingress-line2").click()
    driver.implicitly_wait(5)
    text_pincode = driver.find_element_by_id("GLUXZipUpdateInput").send_keys(pincode)
    # go_button = driver.find_element_by_class_name("a-button-input").click()
    # wait.until(presence_of_element_located((By.XPATH, "//input[@type='submit' and @aria-labelledby='GLUXZipUpdate-announce']")))
    go_button = driver.find_element_by_xpath("//input[@type='submit' and @aria-labelledby='GLUXZipUpdate-announce']").click()
    time.sleep(8)

    try:
        # num_page = driver.find_element_by_xpath('//*[@class="a-pagination"]/li[6]')
        num_page = driver.find_element_by_xpath("//ul[@class='a-pagination']/li[@class='a-disabled' and @aria-disabled='true']")
        num_pages = int(num_page.text)
    except NoSuchElementException:
        # num_page = driver.find_element_by_class_name('a-last').click()
        num_page = None
     
    driver.implicitly_wait(5)

    url_list = []
    if num_page is None:
        num_pages = 0

    i = 0
    while True:
        page_ = i + 1
        url_list.append(driver.current_url)
        driver.implicitly_wait(5)
        # This is basically clicking "NEXT"
        click_next = driver.find_element_by_class_name('a-last')
        if "a-disabled" in click_next.get_attribute("class"):
            break
        click_next.click()
        i += 1
        print("Page " + str(page_) + " grabbed")

    driver.quit()


    with open('search_results_urls.txt', 'w') as filehandle:
        for result_page in url_list:
            filehandle.write('%s\n' % result_page)

    print("---DONE---")

def scrape(url):

    headers = {
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'referer': 'https://www.amazon.in/',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }

    # Download the page using requests
    print("Downloading %s"%url)
    r = requests.get(url, headers=headers)
    # Simple check to check if page was blocked (Usually 503)
    if r.status_code > 500:
        if "To discuss automated access to Amazon data please contact" in r.text:
            print("Page %s was blocked by Amazon. Please try using better proxies\n"%url)
        else:
            print("Page %s must have been blocked by Amazon as the status code was %d"%(url,r.status_code))
        return None
    # Pass the HTML of the page and create
    return e.extract(r.text)

def write_to_file():
    with open("search_results_urls.txt",'r') as urllist, open('search_results_output.json','w') as outfile:
        count_products = 0
        individual_products = 1
        for url in urllist.read().splitlines():
            data = scrape(url)
            if data:
                count_products += len(data['products'])
                for product in data['products']:
                    product['search_url'] = url
                    if individual_products <= product_count:
                        print("Saving Product: %s"%product['title'].encode('utf8'))
                        json.dump(product,outfile)
                        outfile.write("\n")
                        # sleep(5)
                    else:
                        print("We are done taking {} number of products".format(individual_products))
                        return
                    individual_products += 1
# Create an Extractor by reading from the YAML file
e = Extractor.from_yaml_file('search_results.yml')

# Write to output files
write_to_file()
