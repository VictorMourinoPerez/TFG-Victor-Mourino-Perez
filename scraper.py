from selenium import webdriver
from selenium.webdriver.support.ui import Select

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import os
from datetime import date
import metar
#This example requires Selenium WebDriver 3.13 or newer


def format_ints(int):
    if int<10:
        return "0"+str(int)
    else:
        return str(int)


def scrapCompany(icao):
    page_content = ""
    if len(icao) != 0:
        if len(icao) == 8:
            icao = icao[2:len(icao)]
        if len(icao) == 6:
            pathWD = os.getcwd()
            program = "\\msedgedriver.exe"
            pathTWD = pathWD+program
            with webdriver.Edge(pathTWD) as driver:
                driver.implicitly_wait(10)
                sleep(1)
                url = "https://api.joshdouch.me/hex-airline.php?hex="+icao
                driver.get(url)
                page_content = driver.find_element_by_tag_name("body").text
                sleep(1)
                driver.close()
                return page_content
    else:
        return page_content


def scrapTypeCode(icaoList):
    newType = []
    if len(icaoList) != 0:
        pathWD = os.getcwd()
        program = "\\msedgedriver.exe"
        pathTWD = pathWD + program
        with webdriver.Edge(pathTWD) as driver:
            driver.implicitly_wait(10)
            driver.get("http://www.airframes.org/login")
            driver.find_element_by_name("user1").send_keys("alexasenjo")
            driver.find_element_by_name("passwd1").send_keys("weCzP74hjuW3seV" + Keys.ENTER)
            for icao in icaoList:
                driver.find_element_by_name("ica024").send_keys(icao + Keys.ENTER)
                WebDriverWait(driver, 2)
                sleep(5)
                a = driver.find_elements_by_tag_name("td")
                try:
                    newType.append([icao, a[19].text, a[20].text])
                except:
                    print(icao," not found")
            driver.close()
            return newType
    else:
        return []


months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto","Septiembre", "Octubre", "Noviembre", "Diciembre"]


def scrapMETAR(time):
    # time is a list of datetime objects
    metars = []
    pathWD = os.getcwd()
    program = "\\msedgedriver.exe"
    pathTWD = pathWD + program
    with webdriver.Edge(pathTWD) as driver:
            driver.implicitly_wait(10)
            driver.get("https://www.ogimet.com/metars.phtml")
            year = time[0].year
            yearf = time[-1].year
            month = time[0].month
            monthf = time[-1].month
            day = time[0].day
            dayf = time[-1].day

            driver.find_element_by_name("lugar").send_keys("LEBL")
            driver.find_element_by_xpath("/html/body/table/tbody/tr[2]/td[2]/form/table[1]/tbody/tr[2]/td[3]/select/option[2]").click()
            driver.find_element_by_xpath("/html/body/table/tbody/tr[2]/td[2]/form/table[1]/tbody/tr[2]/td[4]/select/option[2]").click()
            driver.find_element_by_xpath("/html/body/table/tbody/tr[2]/td[2]/form/table[1]/tbody/tr[2]/td[5]/select/option[2]").click()
            Select(driver.find_element_by_name("ano")).select_by_visible_text(str(year))
            Select(driver.find_element_by_name("anof")).select_by_visible_text(str(yearf))
            Select(driver.find_element_by_name("mes")).select_by_visible_text(months[month - 1])
            Select(driver.find_element_by_name("mesf")).select_by_visible_text(months[monthf - 1])
            Select(driver.find_element_by_name("day")).select_by_visible_text(format_ints(day))
            Select(driver.find_element_by_name("dayf")).select_by_visible_text(format_ints(dayf))
            Select(driver.find_element_by_name("hora")).select_by_visible_text("00")
            Select(driver.find_element_by_name("horaf")).select_by_visible_text("23")
            driver.find_element_by_name("enviar").click()
            sleep(1)
            WebDriverWait(driver, 5)
            myElem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'pre')))
            page_content = driver.find_element_by_tag_name("pre").text
            sleep(1)
            driver.close()

            page_content = page_content.split(str(year))
            if page_content == ['#Sorry, Your quota limit for slow queries rate has been reached']:
                print("METAR error: https://www.ogimet.com/metars.phtml. \nMessage error: #Sorry, Your quota limit for slow queries rate has been reached")
                return metars

            for metar in page_content:
                if metar[9:14] == "METAR":
                    metar = metar.replace(metar[0:9], "")
                    data = metar.split("\n")
                    data[0] = data[0].replace("=", "")
                    data[0] = data[0].strip()
                    if len(data) > 1:
                        data[1] = data[1].replace("=", "")
                        data[1] = data[1].strip()
                    metars.append((data[0]+" "+data[1]).strip())
            return metars



