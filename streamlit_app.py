import streamlit as st
import requests
import os
import json
from PIL import Image
from io import BytesIO

# === CREDENTIALS ===
SHOPIFY_TOKEN = st.secrets["SHOPIFY_TOKEN"]
SHOPIFY_STORE = st.secrets["SHOPIFY_STORE"]
IMGBB_API_KEY = st.secrets["IMGBB_API_KEY"]
LWA_CLIENT_ID = st.secrets["LWA_CLIENT_ID"]
LWA_CLIENT_SECRET = st.secrets["LWA_CLIENT_SECRET"]
REFRESH_TOKEN = st.secrets["REFRESH_TOKEN"]
MARKETPLACE_ID = st.secrets["MARKETPLACE_ID"]
SELLER_ID = st.secrets["SELLER_ID"]

DESCRIPTION = "Celebrate the arrival of your little one with a beautifully printed baby bodysuit from NOFO VIBES. Crafted for comfort and made with love!"
BULLETS = [
    "🎨 High-Quality Ink Printing",
    "🎖️ Proudly Veteran-Owned",
    "👶 Comfort and Convenience",
    "🎁 Perfect Baby Shower Gift",
    "🔯 Versatile Sizing & Colors"
]

VARIATIONS = [
    "Newborn White Short Sleeve", "Newborn White Long Sleeve", "Newborn Natural Short Sleeve",
    "0-3M White Short Sleeve", "0-3M White Long Sleeve", "0-3M Pink Short Sleeve", "0-3M Blue Short Sleeve",
    "3-6M White Short Sleeve", "3-6M White Long Sleeve", "3-6M Blue Short Sleeve", "3-6M Pink Short Sleeve",
    "6M Natural Short Sleeve", "6-9M White Short Sleeve", "6-9M White Long Sleeve", "6-9M Pink Short Sleeve",
    "6-9M Blue Short Sleeve", "12M White Short Sleeve", "12M White Long Sleeve", "12M Natural Short Sleeve",
    "12M Pink Short Sleeve", "12M Blue Short Sleeve", "18M White Short Sleeve", "18M White Long Sleeve",
    "18M Natural Short Sleeve", "24M White Short Sleeve", "24M White Long Sleeve", "24M Natural Short Sleeve"
]

def upload_and_create_shopify_product(uploaded_file, title_slug, title_full):
    uploaded_file.seek(0)
    imgbb_url = "https://api.imgbb.com/1/upload"
    files = {
        "key": (None, IMGBB_API_KEY),
        "name": (None, title_slug),
        "image": uploaded_file
    }
    response = requests.post(imgbb_url, files=files)
    response.raise_for_status()
    image_url = response.json()["data"]["url"]

    shopify_url = f"https://{SHOPIFY_STORE}/admin/api/2023-01/products.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "product": {
            "title": title_full,
            "handle": title_slug,
            "body_html": DESCRIPTION,
            "vendor": "NOFO VIBES",
            "product_type": "Baby Bodysuit",
            "tags": "baby,funny,onesie,cute,custom",
            "images": [{"src": image_url}]
        }
    }
    r = requests.post(shopify_url, json=payload, headers=headers)
    r.raise_for_status()
    shopify_product = r.json()
    shopify_image_url = shopify_product["product"]["images"][0]["src"]
    return shopify_image_url

def generate_amazon_json_feed(title, image_url):
    import random
    variations = [
        "Newborn White Short Sleeve", "Newborn White Long Sleeve", "Newborn Natural Short Sleeve",
        "0-3M White Short Sleeve", "0-3M White Long Sleeve", "0-3M Pink Short Sleeve", "0-3M Blue Short Sleeve",
        "3-6M White Short Sleeve", "3-6M White Long Sleeve", "3-6M Blue Short Sleeve", "3-6M Pink Short Sleeve",
        "6M Natural Short Sleeve", "6-9M White Short Sleeve", "6-9M White Long Sleeve", "6-9M Pink Short Sleeve",
        "6-9M Blue Short Sleeve", "12M White Short Sleeve", "12M White Long Sleeve", "12M Natural Short Sleeve",
        "12M Pink Short Sleeve", "12M Blue Short Sleeve", "18M White Short Sleeve", "18M White Long Sleeve",
        "18M Natural Short Sleeve", "24M White Short Sleeve", "24M White Long Sleeve", "24M Natural Short Sleeve"
    ]

    def format_slug(title):
        slug = ''.join([w[0] for w in title.split() if w]).upper()[:3]
        return f"{slug}-{random.randint(1000, 9999)}"

    def format_variation_sku(slug, variation):
        parts = variation.split()
        size = parts[0].replace("Newborn", "NB").replace("0-3M", "03M").replace("3-6M", "36M") \
                       .replace("6-9M", "69M").replace("6M", "06M").replace("12M", "12M") \
                       .replace("18M", "18M").replace("24M", "24M")
        color = parts[1][0].upper()
        sleeve = "SS" if "Short" in variation else "LS"
        return f"{slug}-{size}-{color}-{sleeve}"

    def extract_color_and_sleeve(variation):
        color_map = "White"
        sleeve_type = "Short Sleeve" if "Short" in variation else "Long Sleeve"
        for word in variation.split():
            if word.lower() in ["white", "pink", "blue", "natural"]:
                color_map = word.capitalize()
        return color_map, sleeve_type

    slug = format_slug(title)
    parent_sku = f"{slug}-PARENT"
    messages = [{
        "messageId": 1,
        "sku": parent_sku,
        "operationType": "UPDATE",
        "productType": "LEOTARD",
        "requirements": "LISTING",
        "attributes": {
            "item_name": [{"value": f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute"}],
            "brand": [{"value": "NOFO VIBES"}],
            "item_type_keyword": [{"value": "infant-and-toddler-bodysuits"}],
            "product_description": [{"value": DESCRIPTION}],
            "bullet_point": [{"value": b} for b in BULLETS],
            "target_gender": [{"value": "female"}],
            "age_range_description": [{"value": "Infant"}],
            "material": [{"value": "Cotton"}, {"value": "Spandex"}],
            "department": [{"value": "Baby Girls"}],
            "variation_theme": [{"name": "SIZE/COLOR"}],
            "parentage_level": [{"value": "parent"}],
            "model_number": [{"value": title}],
            "model_name": [{"value": title}],
            "import_designation": [{"value": "Imported"}],
            "country_of_origin": [{"value": "US"}],
            "condition_type": [{"value": "new_new"}],
            "batteries_required": [{"value": False}],
            "fabric_type": [{"value": "100% cotton"}],
            "supplier_declared_dg_hz_regulation": [{"value": "not_applicable"}],            
            "supplier_declared_has_product_identifier_exemption": [{"value": True }]            
        }
    }]

    for idx, variation in enumerate(variations, start=2):
        sku = format_variation_sku(slug, variation)
        color_map, sleeve_type = extract_color_and_sleeve(variation)

        messages.append({
            "messageId": idx,
            "sku": sku,
            "operationType": "UPDATE",
            "productType": "LEOTARD",
            "requirements": "LISTING",
            "attributes": {
                "item_name": [{"value": f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute"}],
                "brand": [{"value": "NOFO VIBES"}],
                "item_type_keyword": [{"value": "infant-and-toddler-bodysuits"}],
                "product_description": [{"value": DESCRIPTION}],
                "bullet_point": [{"value": b} for b in BULLETS[:2]],
                "target_gender": [{"value": "female"}],
                "age_range_description": [{"value": "Infant"}],
                "material": [{"value": "Cotton"}, {"value": "Spandex"}],
                "department": [{"value": "Baby Girls"}],
                "variation_theme": [{"name": "SIZE/COLOR"}],
                "parentage_level": [{"value": "child"}],
                "child_parent_sku_relationship": [{
                    "child_relationship_type": "variation",
                    "parent_sku": parent_sku
                }],
                "size": [{"value": variation}],
                "style": [{"value": sleeve_type}],
                "model_number": [{"value": "CrewNeckBodysuit"}],
                "model_name": [{"value": "Crew Neck Bodysuit"}],
                "import_designation": [{"value": "Made in USA"}],
                "country_of_origin": [{"value": "US"}],
                "condition_type": [{"value": "new_new"}],
                "batteries_required": [{"value": False}],
                "fabric_type": [{"value": "100% cotton"}],
                "supplier_declared_dg_hz_regulation": [{"value": "not_applicable"}],          
                "supplier_declared_has_product_identifier_exemption": [{"value": True }],
                "care_instructions": [{"value": "Machine Wash"}],
                "sleeve": [{"value": sleeve_type}],
                "color": [{"value": "multi"}],
                "list_price": [{"currency": "USD", "value": 19.99}],
                "item_package_dimensions": [{
                    "length": {"value": 25.4, "unit": "centimeters"},
                    "width": {"value": 20.32, "unit": "centimeters"},
                    "height": {"value": 2.54, "unit": "centimeters"}
                }],
                "item_package_weight": [{"value": 0.12, "unit": "kilograms"}],
                "main_product_image_locator": [{
                    "media_location": image_url,
                    "marketplace_id": "ATVPDKIKX0DER"
                }],
                "purchasable_offer": [{
                    "currency": "USD",
                    "our_price": [{"schedule": [{"value_with_tax": 21.99}]}],
                    "marketplace_id": "ATVPDKIKX0DER"
                }],
                "fulfillment_availability": [{
                    "quantity": 999,
                    "fulfillment_channel_code": "DEFAULT",
                    "marketplace_id": "ATVPDKIKX0DER"
                }]
            }
        })

    return json.dumps({
        "header": {
            "sellerId": SELLER_ID,
            "version": "2.0",
            "issueLocale": "en_US"
        },
        "messages": messages
    }, indent=2)


def get_amazon_access_token():
    r = requests.post("https://api.amazon.com/auth/o2/token", data={
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": LWA_CLIENT_ID,
        "client_secret": LWA_CLIENT_SECRET
    })
    r.raise_for_status()
    return r.json()["access_token"]

def submit_amazon_json_feed(json_feed, access_token):
    doc_res = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/documents",
        headers={"x-amz-access-token": access_token, "Content-Type": "application/json"},
        json={"contentType": "application/json"}
    )
    doc_res.raise_for_status()
    doc = doc_res.json()

    upload = requests.put(doc["url"], data=json_feed.encode("utf-8"), headers={"Content-Type": "application/json"})
    upload.raise_for_status()

    feed_res = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds",
        headers={"x-amz-access-token": access_token, "Content-Type": "application/json"},
        json={
            "feedType": "JSON_LISTINGS_FEED",
            "marketplaceIds": [MARKETPLACE_ID],
            "inputFeedDocumentId": doc["feedDocumentId"]
        }
    )
    feed_res.raise_for_status()
    return feed_res.json()["feedId"]

def check_amazon_feed_status(feed_id, access_token):
    res = requests.get(
        f"https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds/{feed_id}",
        headers={"x-amz-access-token": access_token, "Content-Type": "application/json"}
    )
    res.raise_for_status()
    return res.json()

def download_amazon_processing_report(feed_status, access_token):
    doc_id = feed_status.get("resultFeedDocumentId")
    if not doc_id:
        return "Processing report not available yet."

    doc_info = requests.get(
        f"https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/documents/{doc_id}",
        headers={"x-amz-access-token": access_token}
    ).json()

    report = requests.get(doc_info["url"])
    report.raise_for_status()
    return report.text

# === UI ===
st.title("🍼 Upload PNG → List to Shopify + Amazon")

uploaded_file = st.file_uploader("Upload PNG File", type="png")
if uploaded_file:
    uploaded_file.seek(0)
    image = Image.open(uploaded_file)
    file_stem = os.path.splitext(uploaded_file.name)[0]
    title_full = file_stem.replace("-", " ").replace("_", " ").title() + " - Baby Bodysuit"
    handle = file_stem.lower().replace(" ", "-").replace("_", "-") + "-baby-bodysuit"
    st.image(image, caption=title_full, use_container_width=True)

    if st.button("📤 Submit to Shopify + Amazon"):
        try:
            st.info("Uploading to ImgBB + Creating product on Shopify...")
            uploaded_file.seek(0)
            image_url = upload_and_create_shopify_product(uploaded_file, handle, title_full)

            st.success("✅ Shopify Product Created")

            st.info("Generating Amazon Feed...")
            token = get_amazon_access_token()
            json_feed = generate_amazon_json_feed(file_stem, image_url)
            st.code(json_feed, language='json')

            st.info("Submitting Feed to Amazon...")
            feed_id = submit_amazon_json_feed(json_feed, token)
            st.success(f"✅ Feed Submitted to Amazon — Feed ID: {feed_id}")

            st.info("Checking Feed Status...")
            status = check_amazon_feed_status(feed_id, token)
            st.code(json.dumps(status, indent=2))

            if status.get("processingStatus") == "DONE":
                st.info("Downloading Processing Report...")
                report = download_amazon_processing_report(status, token)
                st.code(report)
            else:
                st.warning("⚠️ Feed not processed yet. Please check again later.")
        except Exception as e:
            st.error(f"❌ Error: {e}")
