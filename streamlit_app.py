def upload_and_create_shopify_product(uploaded_file, title_slug, title_full):
    # === Upload to ImgBB ===
    imgbb_api_key = st.secrets["IMGBB_API_KEY"]
    imgbb_url = "https://api.imgbb.com/1/upload"
    uploaded_file.seek(0)  # Make sure it's rewinded
    files = {
        "key": (None, imgbb_api_key),
        "name": (None, title_slug),
        "image": uploaded_file  # Raw PNG upload
    }

    response = requests.post(imgbb_url, files=files)

    if not response.ok:
        raise Exception(f"ImgBB Upload Failed: {response.status_code} - {response.text}")
    image_url = response.json()["data"]["url"]

    # === Create Shopify Product ===
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
    product = r.json()["product"]

    if not product.get("images"):
        raise Exception("Image upload failed — Shopify didn't return an image.")

    return product["images"][0]["src"]

import streamlit as st
import os
import csv
import base64
import requests
from io import BytesIO
from PIL import Image

# === CREDENTIALS ===
SHOPIFY_TOKEN = st.secrets["SHOPIFY_TOKEN"]
SHOPIFY_STORE = st.secrets["SHOPIFY_STORE"]
LWA_CLIENT_ID = st.secrets["LWA_CLIENT_ID"]
LWA_CLIENT_SECRET = st.secrets["LWA_CLIENT_SECRET"]
REFRESH_TOKEN = st.secrets["REFRESH_TOKEN"]
SELLER_ID = st.secrets["SELLER_ID"]
MARKETPLACE_ID = st.secrets["MARKETPLACE_ID"]

# === STATIC DATA ===
ACCESSORY_IMAGES = [
    "https://m.media-amazon.com/images/I/71gy1ba4WmL._AC_SX569_.jpg",
    "https://m.media-amazon.com/images/I/71DUS9nCUjL._AC_SX569_.jpg",
    "https://m.media-amazon.com/images/I/81UU9p0A4aL._AC_SX569_.jpg",
    "https://m.media-amazon.com/images/I/81qLAI2RmBL._AC_SX569_.jpg",
    "https://m.media-amazon.com/images/I/71HvcLmnGkL._AC_SX569_.jpg"
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
        try:
            r.raise_for_status()
            token_response = r.json()
            st.write("✅ Token Response:", token_response)
            return token_response["access_token"]
        except Exception as e:
            st.error(f"❌ Token Request Failed: {r.status_code} - {r.text}")
            raise

def generate_amazon_feed(title, image_url):
    variations = [
        "Newborn White Short Sleeve", "Newborn White Long Sleeve", "Newborn Natural Short Sleeve",
        "0-3M White Short Sleeve", "0-3M White Long Sleeve", "0-3M Pink Short Sleeve", "0-3M Blue Short Sleeve",
        "3-6M White Short Sleeve", "3-6M White Long Sleeve", "3-6M Blue Short Sleeve", "3-6M Pink Short Sleeve",
        "6M Natural Short Sleeve", "6-9M White Short Sleeve", "6-9M White Long Sleeve", "6-9M Pink Short Sleeve",
        "6-9M Blue Short Sleeve", "12M White Short Sleeve", "12M White Long Sleeve", "12M Natural Short Sleeve",
        "12M Pink Short Sleeve", "12M Blue Short Sleeve", "18M White Short Sleeve", "18M White Long Sleeve",
        "18M Natural Short Sleeve", "24M White Short Sleeve", "24M White Long Sleeve", "24M Natural Short Sleeve"
    ]
    prices = [21.99, 22.99, 27.99] * 9
    feed = BytesIO()
    writer = csv.writer(feed, delimiter="\t")
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
    for i, var in enumerate(variations):
        size, color, sleeve = var.split()[0], var.split()[1], var.split()[-2:]
        abbr = "SS" if "Short" in sleeve else "LS"
        sku = f"{title}-{size}-{color}-{abbr}".replace(" ", "")
        writer.writerow([
            sku, f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute",
            "NOFO VIBES", "infant-and-toddler-bodysuits", "Update",
            "child", f"{title}-Parent", "variation", "Size",
            prices[i], 999, image_url, *ACCESSORY_IMAGES,
            *BULLETS, DESCRIPTION
        ])
    feed.seek(0)
    return feed

def submit_amazon_feed(feed_file, access_token):
    doc_req = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/documents",
        headers={"x-amz-access-token": access_token, "Content-Type": "application/json"},
        json={"contentType": "text/tab-separated-values;charset=UTF-8"}
    )
    doc = doc_req.json()
    requests.put(doc["url"], data=feed_file.read(), headers={
        "Content-Type": "text/tab-separated-values;charset=UTF-8"
    })
    feed_file.seek(0)
    feed_req = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds",
        headers={"x-amz-access-token": access_token, "Content-Type": "application/json"},
        json={"feedType": "POST_FLAT_FILE_LISTINGS_DATA", "marketplaceIds": [MARKETPLACE_ID], "inputFeedDocumentId": doc["feedDocumentId"]}
    )
    return feed_req.json()["feedId"]

# === STREAMLIT UI ===
st.title("🍼 Upload PNG → Auto-List to Shopify + Amazon")

uploaded_file = st.file_uploader("Upload PNG File", type="png")
if uploaded_file:
    image_bytes = uploaded_file.read()
    uploaded_file.seek(0)  # 🔁 rewind so we can read it again
    image = Image.open(uploaded_file)

    file_stem = os.path.splitext(uploaded_file.name)[0]
    title_full = file_stem.replace("-", " ").replace("_", " ").title() + " - Baby Boy Girl Clothes Bodysuit Funny Cute"
    handle = file_stem.lower().replace(" ", "-").replace("_", "-") + "-baby-boy-girl-clothes-bodysuit-funny-cute"
    st.image(image, caption=title_full, use_container_width=True)

    if st.button("📤 Submit to Shopify + Amazon"):
        try:
            uploaded_file.seek(0)
            st.info("Uploading image and creating Shopify product...")
            cdn_url = upload_and_create_shopify_product(uploaded_file, handle, title_full)
    
            st.info("Generating Amazon JSON feed...")
            token = get_amazon_access_token()
            json_feed = generate_amazon_json_feed(file_stem, cdn_url)
    
            st.info("Submitting to Amazon...")
            feed_id = submit_amazon_json_feed(json_feed, token)
            st.success(f"✅ Amazon Feed Submitted! Feed ID: {feed_id}")
    
            st.info("Checking Amazon feed status...")
            feed_status = check_amazon_feed_status(feed_id, token)
            st.code(json.dumps(feed_status, indent=2))
    
            if feed_status.get("processingStatus") == "DONE":
                st.info("Downloading processing report...")
                report_text = download_amazon_processing_report(feed_status, token)
                st.code(report_text)
            else:
                st.warning("Feed not done processing yet. Please check again later.")
        except Exception as e:
            st.error(f"❌ Error: {e}")

        



def generate_amazon_json_feed(title, image_url):
    variations = [
        "Newborn White Short Sleeve", "Newborn White Long Sleeve", "Newborn Natural Short Sleeve",
        "0-3M White Short Sleeve", "0-3M White Long Sleeve", "0-3M Pink Short Sleeve", "0-3M Blue Short Sleeve",
        "3-6M White Short Sleeve", "3-6M White Long Sleeve", "3-6M Blue Short Sleeve", "3-6M Pink Short Sleeve",
        "6M Natural Short Sleeve", "6-9M White Short Sleeve", "6-9M White Long Sleeve", "6-9M Pink Short Sleeve",
        "6-9M Blue Short Sleeve", "12M White Short Sleeve", "12M White Long Sleeve", "12M Natural Short Sleeve",
        "12M Pink Short Sleeve", "12M Blue Short Sleeve", "18M White Short Sleeve", "18M White Long Sleeve",
        "18M Natural Short Sleeve", "24M White Short Sleeve", "24M White Long Sleeve", "24M Natural Short Sleeve"
    ]

    BULLETS = [
        "🎨 High-Quality Ink Printing",
        "🎖️ Proudly Veteran-Owned",
        "👶 Comfort and Convenience",
        "🎁 Perfect Baby Shower Gift",
        "📏 Versatile Sizing & Colors"
    ]
    DESCRIPTION = "<p>Celebrate the arrival of your little one with a beautifully printed baby bodysuit from NOFO VIBES. Crafted for comfort and made with love!</p>"

    feed_data = []
    parent_sku = f"{title}-Parent"

    parent_product = {
        "sku": parent_sku,
        "productType": "BABY_ONE_PIECE",
        "requirements": "LISTING",
        "attributes": {
            "brand": [{"value": "NOFO VIBES"}],
            "item_name": [{"value": f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute"}],
            "product_description": [{"value": DESCRIPTION}],
            "variation_theme": [{"value": "size_name"}],
            "bullet_point": [{"value": bullet} for bullet in BULLETS],
            "main_image_url": [{"value": image_url}],
            "manufacturer": [{"value": "NOFO VIBES"}],
            "external_product_id_type": [{"value": "ASIN"}]
        }
    }
    feed_data.append(parent_product)

    for var in variations:
        size = var
        abbr = "SS" if "Short" in size else "LS"
        sku = f"{title}-{size.replace(' ', '')}-{abbr}"

        child_product = {
            "sku": sku,
            "productType": "BABY_ONE_PIECE",
            "requirements": "LISTING",
            "attributes": {
                "brand": [{"value": "NOFO VIBES"}],
                "item_name": [{"value": f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute"}],
                "product_description": [{"value": DESCRIPTION}],
                "parentage": [{"value": "child"}],
                "parent_sku": [{"value": parent_sku}],
                "variation_theme": [{"value": "size_name"}],
                "size_name": [{"value": size}],
                "bullet_point": [{"value": bullet} for bullet in BULLETS],
                "main_image_url": [{"value": image_url}],
                "standard_price": [{"value": "21.99", "currency": "USD"}],
                "quantity": [{"value": "999"}],
                "manufacturer": [{"value": "NOFO VIBES"}],
                "external_product_id_type": [{"value": "ASIN"}]
            }
        }
        feed_data.append(child_product)

    return json.dumps(feed_data, indent=2)



def submit_amazon_json_feed(json_feed, access_token):
    # Step 1: Request a document upload URL
    doc_req = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/documents",
        headers={
            "x-amz-access-token": access_token,
            "Content-Type": "application/json"
        },
        json={"contentType": "application/json"}
    )
    doc_req.raise_for_status()
    doc = doc_req.json()

    # Step 2: Upload the JSON feed to the document URL
    upload_headers = {"Content-Type": "application/json"}
    upload_res = requests.put(doc["url"], data=json_feed.encode("utf-8"), headers=upload_headers)
    upload_res.raise_for_status()

    # Step 3: Submit the feed using the uploaded document
    feed_req = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds",
        headers={
            "x-amz-access-token": access_token,
            "Content-Type": "application/json"
        },
        json={
            "feedType": "POST_PRODUCT_DATA",
            "marketplaceIds": [MARKETPLACE_ID],
            "inputFeedDocumentId": doc["feedDocumentId"]
        }
    )
    feed_req.raise_for_status()
    return feed_req.json()["feedId"]



def check_amazon_feed_status(feed_id, access_token):
    feed_status_url = f"https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds/{feed_id}"
    headers = {
        "x-amz-access-token": access_token,
        "Content-Type": "application/json"
    }
    res = requests.get(feed_status_url, headers=headers)
    res.raise_for_status()
    return res.json()



def download_amazon_processing_report(feed_status, access_token):
    if "resultFeedDocumentId" not in feed_status:
        return "Processing report not available yet."

    doc_id = feed_status["resultFeedDocumentId"]
    doc_req = requests.get(
        f"https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/documents/{doc_id}",
        headers={"x-amz-access-token": access_token}
    )
    doc_req.raise_for_status()
    doc_info = doc_req.json()

    report_res = requests.get(doc_info["url"])
    report_res.raise_for_status()
    return report_res.text
