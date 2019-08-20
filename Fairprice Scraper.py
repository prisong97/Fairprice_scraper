#!/usr/bin/env python
# coding: utf-8

# In[94]:


#imports 

import warnings
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.common.keys import Keys
from random import randint
import pandas as pd
import time
import re

warnings.filterwarnings("ignore")
options = Options()
options.add_argument("start-maximized")
options.add_argument("disable-infobars")
options.add_argument("--disable-extensions")
driver = webdriver.Chrome(chrome_options = options)
driver.set_page_load_timeout(25)


# In[95]:


class Fairprice:
    
    def __init__(self):
        url  = 'https://www.fairprice.com.sg'
        driver.get(url)
    
    def get_text(self, product_name):
        return [s.get_attribute("textContent").encode('utf-8').strip() for s in product_name]
    
    def clean_product_name_text(self, product_name_text):
        cleaned_product_name_text = []
        for s in product_name_text:
            s = s.replace('Full Page', '')
            s = s.replace('\n', '')
            s = s.replace('\t', '')
            s = " ".join(s.split())
            cleaned_product_name_text.append(s)
        return cleaned_product_name_text
    

    def collect_items(self, search_query):
        ind = 0
        product_name = []
        product_price = []
        product_url = []
        in_stock = []
        offer_discount = []
        search_bar = driver.find_element_by_css_selector('#SimpleSearchForm_SearchTerm')
        search_bar.send_keys(search_query)
        time.sleep(randint(2, 5))
        driver.find_element_by_xpath('//*[@id="submitButton_ACCE_Label"]').click()
        while ind == 0:
            for i in range(5):
                driver.execute_script("window.scrollTo(0, window.scrollY + 500)")
                time.sleep(randint(2, 5))
                try:
                    element = driver.find_element_by_xpath('//*[@id="WC_SearchBasedNavigationResults_LoadMoreProducts"]')
                    webdriver.ActionChains(driver).move_to_element(element).click(element).perform()
                except:
                    for i in range(2):
                        driver.execute_script("window.scrollTo(0, window.scrollY + 500)")
                        time.sleep(randint(1, 3))
                    ind = 1

        products = driver.find_elements_by_class_name('pdt_list_wrap')
        for product in products:
            product_name.append(product.find_element_by_css_selector('div.pdt_name'))
            product_price.append(product.find_element_by_class_name('pdt_C_price'))
            product_url.append(product.find_element_by_css_selector('a').get_attribute('href'))
            try:
                product_instock = product.find_element_by_css_selector('div.addCartBck')
                product_available = "Yes"
            except:
                product_available = "No"
            try:
                product_offer = product.find_element_by_css_selector('span.pdt_stock.offer')
                offer = "Yes"
            except:
                offer = "No"
            in_stock.append(product_available)
            offer_discount.append(offer)
        product_name_text = self.get_text(product_name)
        cleaned_product_name_text = self.clean_product_name_text(product_name_text)
        
        product_price_text = self.get_text(product_price)
        cleaned_price_text = [float(price.replace('$', '')) for price in product_price_text]
        
        items = pd.DataFrame({"Product Name": cleaned_product_name_text, "Product Price": cleaned_price_text, "in-stock": in_stock, "offer": offer_discount, "product url": product_url})
        return items    
    
    def within_budget(self, search_query, min_budget, max_budget):
        min_budget = min_budget.replace('$', '')
        min_budget = float(min_budget)
        max_budget = max_budget.replace('$', '')
        max_budget = float(max_budget)
        assert 0 <= min_budget <= max_budget
        products = self.collect_items(search_query)
        products = products.sort_values(by=['Product Price'])
        under_budget = products[(products['Product Price'] >= min_budget) & (products['Product Price'] <= max_budget)]
        return under_budget
    
    def relevant_products_within_budget(self, search_query, min_budget, max_budget):
        amount_saved = []
        offer_date = []
        other_comments = []
        under_budget = self.within_budget(search_query, min_budget, max_budget)
        relevant_products = under_budget[under_budget["in-stock"] == "Yes"]
        n = len(relevant_products.index)
        if n < 10:
            result = relevant_products.head(n)
        else:
            result = relevant_products.head(10)            
        offer = result["offer"].tolist()
        product_url = result["product url"].tolist()
        for index in range(len(offer)):
            if offer[index] == "Yes":
                driver.get(product_url[index])
                time.sleep(randint(2, 5))
                try:
                    savings = driver.find_element_by_css_selector('div.custom_saving.pdt_stock.offer')
                    amount = savings.get_attribute("textContent").encode('utf-8').strip()
                    amount = amount.replace("SAVING", "")
                    date = driver.find_element_by_css_selector('div.custom_offerDate')
                    date = date.get_attribute("textContent").encode('utf-8').strip()
                    date = date.replace("Till", "")
                except:
                    amount = ""
                    date = ""
                try:
                    comments = driver.find_elements_by_css_selector('a.pdt_h_txt.gray')
                    comments_text = self.get_text(comments)
                    comments_text = self.clean_product_name_text(comments_text)
                    if len(comments_text) < 5:
                        comments_text = ""
                except:
                    comments_text = ""
            else:
                amount = ""
                date = ""
                comments_text = ""
                       
            amount_saved.append(amount)
            offer_date.append(date)
            other_comments.append(comments_text) 
                
        result['savings'] = amount_saved
        result['offer lapse'] = offer_date
        result['other comments'] = other_comments
          
        return result        
        


# In[98]:


test = Fairprice()
#test.relevant_products_within_budget(#'Search item', 
                                     #'Minimum cost',
                                     #'Maximum cost')
#E.g. test.relevant_products_within_budget('Chocolate milk', '$2.50', '$5.60')

