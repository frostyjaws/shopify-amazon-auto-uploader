# streamlit_app.py
import streamlit as st
import requests
import os
import json
from PIL import Image
from io import BytesIO
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from pathlib import Path

# === CREDENTIALS ===
SHOPIFY_TOKEN = st.secrets["SHOPIFY_TOKEN"]
SHOPIFY_STORE = st.secrets["SHOPIFY_STORE"]
IMGBB_API_KEY = st.secrets["IMGBB_API_KEY"]
LWA_CLIENT_ID = st.secrets["LWA_CLIENT_ID"]
LWA_CLIENT_SECRET = st.secrets["LWA_CLIENT_SECRET"]
REFRESH_TOKEN = st.secrets["REFRESH_TOKEN"]
MARKETPLACE_ID = st.secrets["MARKETPLACE_ID"]
SELLER_ID = st.secrets["SELLER_ID"]
ACCESSORY_IMAGES = [
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/ca9082d9-c0ef-4dbc-a8a8-0de85b9610c0-copy.jpg?v=1744051115",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/26363115-65e5-4936-b422-aca4c5535ae1-copy.jpg?v=1744051115",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/a050c7dc-d0d5-4798-acdd-64b5da3cc70c-copy.jpg?v=1744051115",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/7159a2aa-6595-4f28-8c53-9fe803487504-copy.jpg?v=1744051115",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/700cea5a-034d-4520-99ee-218911d7e905-copy.jpg?v=1744051115"
]

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
            imgbb_url = "https://api.imgbb.com/1/upload"
            files = {
                "key": (None, IMGBB_API_KEY),
                "name": (None, handle),
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
                    "handle": handle,
                    "body_html": "<p>Custom baby bodysuit</p>",
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
            st.success("✅ Shopify Product Created")

            st.info("Generating Amazon Feed...")
            token = requests.post("https://api.amazon.com/auth/o2/token", data={
                "grant_type": "refresh_token",
                "refresh_token": REFRESH_TOKEN,
                "client_id": LWA_CLIENT_ID,
                "client_secret": LWA_CLIENT_SECRET
            }).json()["access_token"]

            json_feed = {
                "header": {
                    "sellerId": SELLER_ID,
                    "version": "2.0",
                    "issueLocale": "en_US"
                },
                "messages": [{
                    "messageId": 1,
                    "sku": f"{file_stem.upper()}-PARENT",
                    "operationType": "UPDATE",
                    "productType": "LEOTARD",
                    "requirements": "LISTING",
                    "attributes": {
                        "item_name": [{"value": title_full}],
                        "brand": [{"value": "NOFO VIBES"}],
                        "product_description": [{"value": "Custom baby bodysuit description"}],
                        "main_product_image_locator": [{
                            "media_location": shopify_image_url,
                            "marketplace_id": "ATVPDKIKX0DER"
                        }]
                    }
                }]
            }

            st.info("Submitting Feed to Amazon...")
            doc_res = requests.post(
                "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/documents",
                headers={"x-amz-access-token": token, "Content-Type": "application/json"},
                json={"contentType": "application/json"}
            )
            doc = doc_res.json()
            requests.put(doc["url"], data=json.dumps(json_feed).encode("utf-8"),
                         headers={"Content-Type": "application/json"}).raise_for_status()

            feed_res = requests.post(
                "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds",
                headers={"x-amz-access-token": token, "Content-Type": "application/json"},
                json={
                    "feedType": "JSON_LISTINGS_FEED",
                    "marketplaceIds": [MARKETPLACE_ID],
                    "inputFeedDocumentId": doc["feedDocumentId"]
                }
            )
            feed_id = feed_res.json()["feedId"]
            st.success(f"✅ Feed Submitted to Amazon — Feed ID: {feed_id}")

            # === IMAGE FEED FOR ACCESSORY PHOTOS ===
            def generate_image_feed_xml(sku, image_urls):
                envelope = Element("AmazonEnvelope")
                header = SubElement(envelope, "Header")
                SubElement(header, "DocumentVersion").text = "1.01"
                SubElement(header, "MerchantIdentifier").text = SELLER_ID
                SubElement(envelope, "MessageType").text = "ProductImage"

                for i, url in enumerate(image_urls):
                    message = SubElement(envelope, "Message")
                    SubElement(message, "MessageID").text = str(i + 1)
                    SubElement(message, "OperationType").text = "Update"
                    image = SubElement(message, "ProductImage")
                    SubElement(image, "SKU").text = f"{file_stem.upper()}-PARENT"
                    SubElement(image, "ImageType").text = f"PT{i+1}"
                    SubElement(image, "ImageLocation").text = url

                return minidom.parseString(tostring(envelope, "utf-8")).toprettyxml(indent="  ")

            image_xml = generate_image_feed_xml(f"{file_stem.upper()}-PARENT", ACCESSORY_IMAGES)
            doc_img = requests.post(
                "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/documents",
                headers={"x-amz-access-token": token, "Content-Type": "application/json"},
                json={"contentType": "text/xml; charset=UTF-8"}
            ).json()
            requests.put(doc_img["url"], data=image_xml.encode("utf-8"),
                         headers={"Content-Type": "text/xml; charset=UTF-8"}).raise_for_status()
            image_feed_res = requests.post(
                "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds",
                headers={"x-amz-access-token": token, "Content-Type": "application/json"},
                json={
                    "feedType": "POST_PRODUCT_IMAGE_DATA",
                    "marketplaceIds": [MARKETPLACE_ID],
                    "inputFeedDocumentId": doc_img["feedDocumentId"]
                }
            )
            image_feed_id = image_feed_res.json()["feedId"]
            st.success(f"📸 Accessory Images Submitted — Feed ID: {image_feed_id}")

        except Exception as e:
            st.error(f"❌ Error: {e}")
