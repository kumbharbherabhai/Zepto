# from sys import implementation
from traceback import print_tb

import jmespath
from curl_cffi  import requests

import json
# import test_for
# from pincode import header
# import requests
# from test_for import *


headerfile = open('headers.json', 'r', encoding='utf-8')
headerdata = json.load(headerfile)
paramsfile = open('param.json', 'r', encoding='utf-8')
paramsdata = json.load(paramsfile)


# json_data = test_for.data_param
response = requests.post('https://cdn.bff.zeptonow.com/api/v3/search',impersonate="chrome124", headers=headerdata, json=paramsdata)

print(response.json())

# response = requests.post('https://cdn.bff.zeptonow.com/api/v3/search',impersonate="chrome124", cookies=cookies, headers=headers, json=json_data)


print(response.status_code)
data = response.json()

all_products = []

# loop through all layout blocks
for layout in data.get("layout", []):
    items = jmespath.search("data.resolver.data.items", layout)
    if items:
        for item in items:
            name           = jmespath.search('productResponse.product.name', item)
            brand          = jmespath.search('productResponse.product.brand', item)
            mrp_raw        = jmespath.search('productResponse.productVariant.mrp', item)
            price_raw      = jmespath.search('productResponse.discountedSellingPrice', item)

            mrp            = mrp_raw / 100 if mrp_raw else None
            selling_price  = price_raw / 100 if price_raw else None
            discount_per   = round((mrp - selling_price) / mrp * 100, 2) if mrp else 0
            saving_money   = (mrp - selling_price) if (mrp and selling_price) else 0

            avg_rating     = jmespath.search('productResponse.productVariant.ratingSummary.averageRating', item)
            total_reviews  = jmespath.search('productResponse.productVariant.ratingSummary.totalRatings', item)
            url=jmespath.search('productResponse.productVariant.id',item)
            full_url= "https://www.zepto.com/pn/UNKNOWN-SLUG/pvid/"+f'{url}'
            image_path=jmespath.search("productResponse.productVariant.images[0].name",item)
            image_url="https://cdn.zeptonow.com/production/cms/product_variant/"+f"{image_path}"
            all_products.append({
                "name": name,
                "brand": brand,
                "mrp": mrp,
                "selling_price": selling_price,
                "discount_percent": discount_per,
                "saving_money": saving_money,
                "average_rating": avg_rating,
                "total_reviews": total_reviews,
                "full_url":full_url,
                "URL":url,
                "image_url":image_url
            })

# print all products
for idx, p in enumerate(all_products, start=1):
    print(f"Product {idx}")
    for k, v in p.items():
        print(f"{k}: {v}")
    print()

