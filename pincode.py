import json
import time

from attr import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import  subprocess

search=input("Enter The Your Product")

# Chrome options
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

driver = webdriver.Chrome(options=options)
driver.get("https://www.zeptonow.com/")


# 🔹 Wait until search input is visible (max 20 sec)
wait = WebDriverWait(driver, 20)
time.sleep(2)
clickinput = wait.until(
    EC.visibility_of_element_located((By.XPATH, '//a[@aria-label="Search for products"]'))
)
time.sleep(2)
clickinput.click()
time.sleep(2)

search_input = wait.until(
    EC.visibility_of_element_located((By.XPATH, '//input[@placeholder="Search for over 5000 products"]'))
)
time.sleep(2)
# 🔹 Type product name
search_input.send_keys(search)
search_input.send_keys(Keys.ENTER)

# Wait for API request to trigger
time.sleep(5)

# 🔹 Get network logs
logs = driver.get_log("performance")

headerflag, paramflag = 0, 0
for entry in logs:
    message = json.loads(entry["message"])
    msg = message["message"]

    if msg.get("method") == "Network.requestWillBeSent":
        request = msg.get("params", {}).get("request", {})
        url = request.get("url", "")

        if "cdn.bff.zeptonow.com/api/v3/search" in url:
            print("\n✅ Found Search API Call")
            print("URL:", url)
            print("\n🔹 Headers:")

            header=request.get("headers", {})

            try:
                if header != {}:
                    if header['session_id'] and header['store_id'] and header['store_ids'] and header['x-csrf-secret'] and header['x-xsrf-token']:

                     # print("\n🔹 Post Data:" + f"{header}")
                        headerfile = open('headers.json', 'w', encoding='utf-8')
                        headerfile.write(json.dumps(header))
                        headerfile.close()

                        headerflag += 1
            except:
                pass

            post_data_raw = request.get("postData", "")

            try:
                if post_data_raw:
                    data_param = json.loads(post_data_raw)  # Convert string to dict

                    if all(k in data_param for k in ['query', 'pageNumber', 'mode', 'intentId']):
                        with open('param.json', 'w', encoding='utf-8') as paramfile:
                            json.dump(data_param, paramfile, indent=2)
                        paramflag += 1
            except Exception as e:
                print("❌ Error while parsing postData:", e)

            if headerflag == 1 and paramflag == 1:
                break

subprocess.run(["python", "main.py"])