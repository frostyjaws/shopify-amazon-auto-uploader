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
    return image_url

def abbreviate_title(title):
    return ''.join([word[0] for word in title.split()][:3]).upper()

def clean_variation(var):
    parts = var.split()
    size = parts[0].replace("-", "")
    color = parts[1][:3].upper()
    sleeve = "SS" if "Short" in var else "LS"
    return size, color, sleeve

def generate_amazon_json_feed(title, image_url):
    title_abbr = abbreviate_title(title)
    rand_suffix = str(random.randint(1000, 9999))
    variations = [
        "Newborn White Short Sleeve", "Newborn White Long Sleeve", "Newborn Natural Short Sleeve",
        "0-3M White Short Sleeve", "0-3M White Long Sleeve", "0-3M Pink Short Sleeve", "0-3M Blue Short Sleeve",
        "3-6M White Short Sleeve", "3-6M White Long Sleeve", "3-6M Blue Short Sleeve", "3-6M Pink Short Sleeve",
        "6M Natural Short Sleeve", "6-9M White Short Sleeve", "6-9M White Long Sleeve", "6-9M Pink Short Sleeve",
        "6-9M Blue Short Sleeve", "12M White Short Sleeve", "12M White Long Sleeve", "12M Natural Short Sleeve",
        "12M Pink Short Sleeve", "12M Blue Short Sleeve", "18M White Short Sleeve", "18M White Long Sleeve",
        "18M Natural Short Sleeve", "24M White Short Sleeve", "24M White Long Sleeve", "24M Natural Short Sleeve"
    ]

    messages = [{
        "messageId": 1,
        "operationType": "UPSERT",
        "sku": f"{title_abbr}{rand_suffix}-Parent",
        "productType": "infant_and_toddler_bodysuits",
        "attributes": {
            "title": [{"value": f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute"}],
            "brand": [{"value": "NOFO VIBES"}],
            "product_description": [{"value": "Celebrate the arrival of your little one with a beautifully printed baby bodysuit from NOFO VIBES. Crafted for comfort and made with love!"}],
            "bullet_point": [
                {"value": "High-Quality Ink Printing"},
                {"value": "Proudly Veteran-Owned"},
                {"value": "Comfort and Convenience"},
                {"value": "Perfect Baby Shower Gift"},
                {"value": "Versatile Sizing & Colors"}
            ],
            "manufacturer": [{"value": "NOFO VIBES"}],
            "department": [{"value": "unisex-baby"}],
            "variationTheme": [{"value": "size_name"}],
            "parentage": [{"value": "parent"}],
            "country_of_origin": [{"value": "US"}],
            "condition_type": [{"value": "new_new"}],
            "batteries_required": [{"value": False}],
            "supplier_declared_dg_hz_regulation": [{"value": "not_applicable"}]
        }
    }]

    for i, var in enumerate(variations):
        size, color, sleeve = clean_variation(var)
        sku = f"{title_abbr}{rand_suffix}-{size}-{color}-{sleeve}"
        messages.append({
            "messageId": i + 2,
            "operationType": "UPSERT",
            "sku": sku,
            "productType": "infant_and_toddler_bodysuits",
            "attributes": {
                "title": [{"value": f"{title} - {var}"}],
                "brand": [{"value": "NOFO VIBES"}],
                "product_description": [{"value": "Celebrate the arrival of your little one with a beautifully printed baby bodysuit from NOFO VIBES. Crafted for comfort and made with love!"}],
                "bullet_point": [
                    {"value": "High-Quality Ink Printing"},
                    {"value": "Proudly Veteran-Owned"},
                    {"value": "Comfort and Convenience"},
                    {"value": "Perfect Baby Shower Gift"},
                    {"value": "Versatile Sizing & Colors"}
                ],
                "manufacturer": [{"value": "NOFO VIBES"}],
                "department": [{"value": "unisex-baby"}],
                "variationTheme": [{"value": "size_name"}],
                "parentage": [{"value": "child"}],
                "parent_sku": [{"value": f"{title_abbr}{rand_suffix}-Parent"}],
                "size_name": [{"value": var}],
                "main_image": [{"value": image_url}],
                "country_of_origin": [{"value": "US"}],
                "condition_type": [{"value": "new_new"}],
                "batteries_required": [{"value": False}],
                "supplier_declared_dg_hz_regulation": [{"value": "not_applicable"}]
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


def generate_inventory_feed_json(title, seller_id):
    variations = [
        "Newborn White Short Sleeve", "Newborn White Long Sleeve", "Newborn Natural Short Sleeve",
        "0-3M White Short Sleeve", "0-3M White Long Sleeve", "0-3M Pink Short Sleeve", "0-3M Blue Short Sleeve",
        "3-6M White Short Sleeve", "3-6M White Long Sleeve", "3-6M Blue Short Sleeve", "3-6M Pink Short Sleeve",
        "6M Natural Short Sleeve", "6-9M White Short Sleeve", "6-9M White Long Sleeve", "6-9M Pink Short Sleeve",
        "6-9M Blue Short Sleeve", "12M White Short Sleeve", "12M White Long Sleeve", "12M Natural Short Sleeve",
        "12M Pink Short Sleeve", "12M Blue Short Sleeve", "18M White Short Sleeve", "18M White Long Sleeve",
        "18M Natural Short Sleeve", "24M White Short Sleeve", "24M White Long Sleeve", "24M Natural Short Sleeve"
    ]
    def abbreviate_title(title):
        return ''.join([word[0] for word in title.split()][:3]).upper()
    title_abbr = abbreviate_title(title)
    rand_suffix = "2847"
    messages = []
    for i, var in enumerate(variations):
        parts = var.split()
        size = parts[0].replace("-", "")
        color = parts[1][:3].upper()
        sleeve = "SS" if "Short" in var else "LS"
        sku = f"{title_abbr}{rand_suffix}-{size}-{color}-{sleeve}"
        messages.append({
            "messageId": i + 1,
            "operationType": "UPDATE",
            "sku": sku,
            "quantity": {"value": 999}
        })
    return {
        "header": {"sellerId": seller_id, "version": "2.0"},
        "messages": messages
    }

def submit_inventory_feed(inventory_feed, access_token):
    doc_res = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/documents",
        headers={"x-amz-access-token": access_token, "Content-Type": "application/json"},
        json={"contentType": "application/json"}
    )
    doc_res.raise_for_status()
    doc = doc_res.json()
    upload = requests.put(doc["url"], data=json.dumps(inventory_feed).encode("utf-8"),
                          headers={"Content-Type": "application/json"})
    upload.raise_for_status()
    feed_res = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds",
        headers={"x-amz-access-token": access_token, "Content-Type": "application/json"},
        json={
            "feedType": "POST_INVENTORY_AVAILABILITY_DATA",
            "marketplaceIds": [MARKETPLACE_ID],
            "inputFeedDocumentId": doc["feedDocumentId"]
        }
    )
    feed_res.raise_for_status()
    return feed_res.json()["feedId"]


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
            # st.code(json_feed, language='json')

            st.info("Submitting Feed to Amazon...")
            feed_id = submit_amazon_json_feed(json_feed, token)
            st.success(f"✅ Feed Submitted to Amazon — Feed ID: {feed_id}")
            st.info("📦 Submitting Inventory Feed...")
            inventory_json = generate_inventory_feed_json(file_stem.replace("-", " "), SELLER_ID)
            inventory_feed_id = submit_inventory_feed(inventory_json, token)
            st.success(f"✅ Inventory Feed Submitted — Feed ID: {inventory_feed_id}")

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
