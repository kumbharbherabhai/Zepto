import json
import jmespath
from curl_cffi import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Get user input for product search
search = input("Enter Your Product: ")


# Chrome options
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

try:
    # Initialize WebDriver
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.zeptonow.com/")

    # Wait until search input is visible (max 20 sec)
    wait = WebDriverWait(driver, 20)
    try:
        search_input = wait.until(
            EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Search for over 5000 products"]'))
        )
    except Exception as e:
        print(f"Error finding search input: {e}")
        driver.quit()
        exit()

    # Type product name and submit
    print(f"Searching for: {search}")
    search_input.send_keys(search)
    search_input.send_keys(Keys.ENTER)

    # Wait for API request to trigger
    api_url = None
    headers = None
    post_data = None
    start_time = time.time()
    while time.time() - start_time < 15:
        logs = driver.get_log("performance")
        for entry in logs:
            message = json.loads(entry["message"])
            msg = message["message"]

            if msg.get("method") == "Network.requestWillBeSent":
                request = msg.get("params", {}).get("request", {})
                url = request.get("url", "")
                if "cdn.bff.zeptonow.com/api/v3/search" in url:
                    api_url = url
                    headers = request.get("headers", {})
                    post_data = request.get("postData", {})
                    print("\n✅ Found Search API Call")
                    print("URL:", api_url)
                    print("\n🔹 Headers:")
                    print(json.dumps(headers, indent=2))
                    print("\n🔹 Post Data:")
                    print(post_data)
                    break
        if api_url:
            break
        time.sleep(0.5)  # Short sleep to avoid overloading CPU

    if not api_url:
        print("Error: Search API call not found in network logs")
        driver.quit()
        exit()

    # Extract cookies from browser session
    cookies = {cookie["name"]: cookie["value"] for cookie in driver.get_cookies()}

    # Make API request
    try:
        response = requests.post(
            api_url,
            impersonate="chrome124",
            headers=headers,
            json=json.loads(post_data) if post_data else {},
            cookies=cookies
        )
        response.raise_for_status()
        data = response.json()
        print("\n🔹 Raw API Response:")
        print(json.dumps(data, indent=2))  # Print raw response for debugging
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        driver.quit()
        exit()
    except json.JSONDecodeError as e:
        print(f"Failed to parse API response as JSON: {e}")
        driver.quit()
        exit()

    # Parse products using jmespath
    all_products = []
    for layout in data.get("layout", []):
        items = jmespath.search("data.resolver.data.items", layout)
        if not items:
            print("Warning: No items found in layout")
            continue
        for item in items:
            name = jmespath.search('productResponse.product.name', item)
            brand = jmespath.search('productResponse.product.brand', item)
            mrp_raw = jmespath.search('productResponse.productVariant.mrp', item)
            price_raw = jmespath.search('productResponse.discountedSellingPrice', item)

            # Debug missing fields
            if not name:
                print("Warning: Product name is None")
            if not brand:
                print("Warning: Brand is None")
            if not mrp_raw:
                print("Warning: MRP is None")
            if not price_raw:
                print("Warning: Selling price is None")

            mrp = mrp_raw / 100 if mrp_raw else None
            selling_price = price_raw / 100 if price_raw else None
            discount_per = round((mrp - selling_price) / mrp * 100, 2) if mrp and selling_price else 0
            saving_money = (mrp - selling_price) if mrp and selling_price else 0

            avg_rating = jmespath.search('productResponse.productVariant.ratingSummary.averageRating', item)
            total_reviews = jmespath.search('productResponse.productVariant.ratingSummary.totalRatings', item)
            url = jmespath.search('productResponse.productVariant.id', item)
            full_url = f"https://www.zepto.com/pn/UNKNOWN-SLUG/pvid/{url}" if url else None
            image_path = jmespath.search("productResponse.productVariant.images[0].name", item)
            image_url = f"https://cdn.zeptonow.com/production/cms/product_variant/{image_path}" if image_path else None

            all_products.append({
                "name": name,
                "brand": brand,
                "mrp": mrp,
                "selling_price": selling_price,
                "discount_percent": discount_per,
                "saving_money": saving_money,
                "average_rating": avg_rating,
                "total_reviews": total_reviews,
                "full_url": full_url,
                "URL": url,
                "image_url": image_url
            })

    if not all_products:
        print("Error: No products found in API response")
    else:
        # Print all products
        for idx, product in enumerate(all_products, start=1):
            print(f"\nProduct {idx}")
            for key, value in product.items():
                print(f"{key}: {value}")

except Exception as e:
    print(f"Error: {e}")
finally:
    driver.quit()