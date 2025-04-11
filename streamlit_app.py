import streamlit as st
import os
import base64
import csv
import requests
from io import BytesIO
from PIL import Image

# === CONFIG (from secrets or env) ===
SHOPIFY_TOKEN = st.secrets["SHOPIFY_TOKEN"]
SHOPIFY_STORE = st.secrets["SHOPIFY_STORE"]
LWA_CLIENT_ID = st.secrets["LWA_CLIENT_ID"]
LWA_CLIENT_SECRET = st.secrets["LWA_CLIENT_SECRET"]
REFRESH_TOKEN = st.secrets["REFRESH_TOKEN"]
SELLER_ID = st.secrets["SELLER_ID"]
MARKETPLACE_ID = st.secrets["MARKETPLACE_ID"]

ACCESSORY_IMAGES = [
    "https://m.media-amazon.com/images/I/71gy1ba4WmL._AC_SX569_.jpg",
    "https://m.media-amazon.com/images/I/71DUS9nCUjL._AC_SX569_.jpg",
    "https://m.media-amazon.com/images/I/81UU9p0A4aL._AC_SX569_.jpg",
    "https://m.media-amazon.com/images/I/81qLAI2RmBL._AC_SX569_.jpg",
    "https://m.media-amazon.com/images/I/71HvcLmnGkL._AC_SX569_.jpg"
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

PRICES = [
    21.99, 22.99, 27.99, 21.99, 22.99, 27.99, 27.99,
    21.99, 22.99, 27.99, 27.99, 27.99, 21.99, 22.99,
    27.99, 27.99, 21.99, 22.99, 27.99, 27.99, 27.99,
    21.99, 22.99, 27.99, 21.99, 22.99, 27.99
]

BULLETS = [
    "🎨 High-Quality Ink Printing",
    "🎖️ Proudly Veteran-Owned",
    "👶 Comfort and Convenience",
    "🎁 Perfect Baby Shower Gift",
    "📏 Versatile Sizing & Colors"
]

DESCRIPTION = "<p>Celebrate the arrival of your little one with a beautifully printed baby bodysuit from NOFO VIBES. Crafted for comfort and made with love!</p>"

def get_amazon_access_token():
    r = requests.post("https://api.amazon.com/auth/o2/token", data={
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": LWA_CLIENT_ID,
        "client_secret": LWA_CLIENT_SECRET
    })
    r.raise_for_status()
    return r.json()["access_token"]

def upload_to_shopify(image_bytes, title):
    encoded = base64.b64encode(image_bytes).decode()
    url = f"https://{SHOPIFY_STORE}/admin/api/2023-01/products.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_TOKEN,
        "Content-Type": "application/json"
    }
    data = {
        "product": {
            "title": title,
            "images": [{"attachment": encoded}]
        }
    }
    r = requests.post(url, json=data, headers=headers)
    r.raise_for_status()

    product_data = r.json()
    images = product_data.get("product", {}).get("images", [])

    if not images:
        raise Exception("Shopify product created, but image URL was not returned. Image may not have uploaded successfully.")

    return images[0]["src"]

def generate_amazon_feed(title, image_url):
    feed_data = BytesIO()
    writer = csv.writer(feed_data, delimiter="\t")
    writer.writerow([
        "item_sku", "item_name", "brand_name", "feed_product_type", "update_delete",
        "parent_child", "parent_sku", "relationship_type", "variation_theme",
        "standard_price", "quantity", "main_image_url",
        "other_image_url1", "other_image_url2", "other_image_url3",
        "other_image_url4", "other_image_url5",
        "bullet_point1", "bullet_point2", "bullet_point3",
        "bullet_point4", "bullet_point5", "product_description"
    ])
    writer.writerow([
        f"{title}-Parent", f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute",
        "NOFO VIBES", "infant-and-toddler-bodysuits", "Update",
        "parent", "", "", "Size", "", "", image_url,
        *ACCESSORY_IMAGES, *BULLETS, DESCRIPTION
    ])
    for i, var in enumerate(VARIATIONS):
        size, color, sleeve = var.split()[0], var.split()[1], var.split()[-2:]
        abbr = "SS" if "Short" in sleeve else "LS"
        sku = f"{title}-{size}-{color}-{abbr}".replace(" ", "")
        writer.writerow([
            sku, f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute",
            "NOFO VIBES", "infant-and-toddler-bodysuits", "Update",
            "child", f"{title}-Parent", "variation", "Size",
            PRICES[i], 999, image_url, *ACCESSORY_IMAGES,
            *BULLETS, DESCRIPTION
        ])
    feed_data.seek(0)
    return feed_data

def submit_feed(feed_file, access_token):
    doc_req = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/documents",
        headers={
            "x-amz-access-token": access_token,
            "Content-Type": "application/json"
        },
        json={"contentType": "text/tab-separated-values;charset=UTF-8"}
    )
    doc_req.raise_for_status()
    doc = doc_req.json()
    requests.put(doc["url"], data=feed_file.read(), headers={
        "Content-Type": "text/tab-separated-values;charset=UTF-8"
    }).raise_for_status()
    feed_file.seek(0)
    feed_req = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds",
        headers={
            "x-amz-access-token": access_token,
            "Content-Type": "application/json"
        },
        json={
            "feedType": "POST_FLAT_FILE_LISTINGS_DATA",
            "marketplaceIds": [MARKETPLACE_ID],
            "inputFeedDocumentId": doc["feedDocumentId"]
        }
    )
    feed_req.raise_for_status()
    return feed_req.json()["feedId"]

st.title("🍼 Shopify + Amazon Auto-Uploader")

uploaded_file = st.file_uploader("Upload PNG File", type="png")
if uploaded_file:
    image = Image.open(uploaded_file)
    title = os.path.splitext(uploaded_file.name)[0].replace("-", " ").replace("_", " ").title()
    st.image(image, caption=title, use_container_width=True)

    if st.button("📤 Upload & Submit Feed"):
        try:
            image_bytes = uploaded_file.read()
            st.info("Uploading to Shopify...")
            img_url = upload_to_shopify(image_bytes, title)

            st.info("Generating feed file...")
            feed = generate_amazon_feed(title, img_url)

            st.info("Submitting to Amazon...")
            token = get_amazon_access_token()
            feed_id = submit_feed(feed, token)

            st.success(f"✅ Feed Submitted! ID: {feed_id}")
        except Exception as e:
            st.error(f"❌ Error: {e}")
