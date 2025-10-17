import streamlit as st
import requests
import os
import json
from PIL import Image
from io import BytesIO

# === CREDENTIALS (read from Streamlit secrets) ===
SHOPIFY_TOKEN = st.secrets["SHOPIFY_TOKEN"]
SHOPIFY_STORE = st.secrets["SHOPIFY_STORE"]
IMGBB_API_KEY = st.secrets["IMGBB_API_KEY"]
LWA_CLIENT_ID = st.secrets["LWA_CLIENT_ID"]
LWA_CLIENT_SECRET = st.secrets["LWA_CLIENT_SECRET"]
REFRESH_TOKEN = st.secrets["REFRESH_TOKEN"]
MARKETPLACE_ID = st.secrets["MARKETPLACE_ID"]
SELLER_ID = st.secrets["SELLER_ID"]

# === COPY / CONTENT ===
DESCRIPTION = """
<p>Celebrate the arrival of your little one with our adorable Custom Baby onesie&reg;, the perfect baby shower gift that will be cherished for years to come. This charming piece of baby clothing is an ideal new baby gift for welcoming a newborn into the world. Whether it's for a baby announcement, a pregnancy reveal, or a special baby shower, this baby onesie&reg; is sure to delight.</p>
<p>Our Custom Baby onesie&reg; features a playful and cute design, perfect for showcasing your baby's unique personality. Made with love and care, this baby onesie&reg; is designed to keep your baby comfortable and stylish. It's an essential item in cute baby clothes, making it a standout piece for any new arrival.</p>
<p>Perfect for both baby boys and girls, this versatile baby onesie&reg; is soft, comfortable, and durable, ensuring it can withstand numerous washes. The easy-to-use snaps make changing a breeze, providing convenience for busy parents.</p>
<p>Whether you're looking for a personalized baby onesie&reg;, a funny baby onesie&reg;, or a cute baby onesie&reg;, this Custom Baby onesie&reg; has it all. It's ideal for celebrating the excitement of a new baby, featuring charming and customizable designs. This makes it a fantastic option for funny baby clothes that bring a smile to everyone's face.</p>
<p>Imagine gifting this delightful baby onesie&reg; at a baby shower or using it as a memorable baby announcement or pregnancy reveal. It's perfect for anyone searching for a unique baby gift, announcement baby onesie&reg;, or a special new baby onesie&reg;.</p>
<p>This baby onesie&reg; is not just an item of clothing; it's a keepsake that celebrates the joy and wonder of a new life.</p>
<p>From baby boy clothes to baby girl clothes, this baby onesie&reg; is perfect for any newborn. Whether it's a boho design, a Father's Day gift, or custom baby clothes, this piece is a wonderful addition to any baby's wardrobe.</p>
"""

BULLETS = [
    "High-Quality Ink Printing: Vibrant, long-lasting colors thanks to direct-to-garment printing.",
    "Proudly Veteran-Owned: Support a veteran-owned small business with every purchase.",
    "Comfort and Convenience: Soft, breathable material and easy snap closure for quick changes.",
    "Perfect Baby Shower Gift: A thoughtful and adorable present for new parents.",
    "Versatile Sizing & Colors: Multiple sizes and colors to find the perfect fit."
]

# === MASTER VARIATIONS (from your list) ===
VARIATIONS = [
    # Short Sleeve — White ($29.99)
    "Newborn White Short Sleeve",
    "0-3M White Short Sleeve",
    "3-6M White Short Sleeve",
    "6-9M White Short Sleeve",
    "12M White Short Sleeve",
    "18M White Short Sleeve",
    "24M White Short Sleeve",

    # Short Sleeve — Natural ($33.99)
    "0-3M Natural Short Sleeve",
    "3-6M Natural Short Sleeve",
    "6-9M Natural Short Sleeve",
    "12M Natural Short Sleeve",

    # Short Sleeve — Pink ($33.99)
    "0-3M Pink Short Sleeve",
    "3-6M Pink Short Sleeve",
    "6-9M Pink Short Sleeve",

    # Short Sleeve — Blue ($33.99)
    "0-3M Blue Short Sleeve",
    "3-6M Blue Short Sleeve",
    "6-9M Blue Short Sleeve",

    # Long Sleeve — White ($30.99)
    "Newborn White Long Sleeve",
    "0-3M White Long Sleeve",
    "3-6M White Long Sleeve",
    "6-9M White Long Sleeve",
    "12M White Long Sleeve",
    "18M White Long Sleeve",
    "24M White Long Sleeve",
]

# === HELPERS ===
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
    r = requests.post(shopify_url, json=payload, headers=headers, verify=False)
    r.raise_for_status()
    return r.json()["product"]["images"][0]["src"]

def generate_amazon_json_feed(title, image_url):
    import random

    # Map colors to Amazon-friendly swatch names
    def extract_color_sleeve_size(variation):
        parts = variation.split()
        size_token = next(p for p in parts if p == "Newborn" or "M" in p)
        sleeve_type = "Short Sleeve" if "Short" in variation else "Long Sleeve"
        size_with_sleeve = f"{size_token} - {sleeve_type}"
        color_token = next(p for p in parts if p.lower() in ["white", "pink", "blue", "natural"])
        color_value = {
            "white": "White",
            "natural": "Beige",       # Natural → Beige (swatch)
            "pink": "Light Pink",
            "blue": "Light Blue",
        }[color_token.lower()]
        return color_value, sleeve_type, size_with_sleeve

    # Pricing per your master list
    price_map = {
        # Short Sleeve — White = $29.99
        "Newborn White Short Sleeve": 29.99,
        "0-3M White Short Sleeve": 29.99,
        "3-6M White Short Sleeve": 29.99,
        "6-9M White Short Sleeve": 29.99,
        "12M White Short Sleeve": 29.99,
        "18M White Short Sleeve": 29.99,
        "24M White Short Sleeve": 29.99,

        # Short Sleeve — Natural = $33.99
        "0-3M Natural Short Sleeve": 33.99,
        "3-6M Natural Short Sleeve": 33.99,
        "6-9M Natural Short Sleeve": 33.99,
        "12M Natural Short Sleeve": 33.99,

        # Short Sleeve — Pink = $33.99
        "0-3M Pink Short Sleeve": 33.99,
        "3-6M Pink Short Sleeve": 33.99,
        "6-9M Pink Short Sleeve": 33.99,

        # Short Sleeve — Blue = $33.99
        "0-3M Blue Short Sleeve": 33.99,
        "3-6M Blue Short Sleeve": 33.99,
        "6-9M Blue Short Sleeve": 33.99,

        # Long Sleeve — White = $30.99
        "Newborn White Long Sleeve": 30.99,
        "0-3M White Long Sleeve": 30.99,
        "3-6M White Long Sleeve": 30.99,
        "6-9M White Long Sleeve": 30.99,
        "12M White Long Sleeve": 30.99,
        "18M White Long Sleeve": 30.99,
        "24M White Long Sleeve": 30.99,
    }

    # Required Apparel attributes (kept consistent parent/child)
    ITEM_TYPE = "infant-and-toddler-bodysuits"
    FABRIC_TYPE = "100% cotton"
    CARE = "Machine Wash"
    GENDER = "female"
    AGE_RANGE = "Infant"
    DEPARTMENT = "Baby Girls"
    IMPORT_DESIGNATION = "Made in USA"
    COUNTRY_OF_ORIGIN = "US"
    DG_REG = "not_applicable"

    # Required package info
    PKG_DIM = {"length": {"value": 3, "unit": "inches"},
               "width":  {"value": 3, "unit": "inches"},
               "height": {"value": 1, "unit": "inches"}}
    PKG_WEIGHT = {"value": 0.19, "unit": "kilograms"}

    slug = ''.join([w[0] for w in title.split() if w]).upper()[:3] + f"-{random.randint(1000,9999)}"
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
            "item_type_keyword": [{"value": ITEM_TYPE}],
            "product_description": [{"value": DESCRIPTION}],
            "bullet_point": [{"value": b} for b in BULLETS],
            "target_gender": [{"value": GENDER}],
            "age_range_description": [{"value": AGE_RANGE}],
            "department": [{"value": DEPARTMENT}],
            "fabric_type": [{"value": FABRIC_TYPE}],
            "care_instructions": [{"value": CARE}],
            "country_of_origin": [{"value": COUNTRY_OF_ORIGIN}],
            "import_designation": [{"value": IMPORT_DESIGNATION}],
            "supplier_declared_dg_hz_regulation": [{"value": DG_REG}],
            "batteries_required": [{"value": False}],
            # VARIATION THEME: must include a name + attributes
            "variation_theme": [{"name": "size_color", "attributes": ["size", "color"]}],
            "parentage_level": [{"value": "parent"}],
            "model_number": [{"value": "NBV"}],
            "model_name": [{"value": "Crew Neck Bodysuit"}],
            # GTIN exemption so we don't need external_product_id
            "supplier_declared_has_product_identifier_exemption": [{"value": True}]
        }
    }]

    # Child variations
    for i, variation in enumerate(VARIATIONS, start=2):
        color_value, sleeve_type, size_with_sleeve = extract_color_sleeve_size(variation)
        sku = f"{slug}-{i:03d}"

        attributes = {
            "item_name": [{"value": f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute"}],
            "brand": [{"value": "NOFO VIBES"}],
            "item_type_keyword": [{"value": ITEM_TYPE}],
            "product_description": [{"value": DESCRIPTION}],
            "bullet_point": [{"value": b} for b in BULLETS],
            "target_gender": [{"value": GENDER}],
            "age_range_description": [{"value": AGE_RANGE}],
            "department": [{"value": DEPARTMENT}],
            "fabric_type": [{"value": FABRIC_TYPE}],
            "care_instructions": [{"value": CARE}],
            "country_of_origin": [{"value": COUNTRY_OF_ORIGIN}],
            "import_designation": [{"value": IMPORT_DESIGNATION}],
            "supplier_declared_dg_hz_regulation": [{"value": DG_REG}],
            "batteries_required": [{"value": False}],

            # Variation linkage
            "variation_theme": [{"name": "size_color", "attributes": ["size", "color"]}],
            "parentage_level": [{"value": "child"}],
            "child_parent_sku_relationship": [{
                "child_relationship_type": "variation",
                "parent_sku": parent_sku
            }],

            # Your requested fields
            "size": [{"value": size_with_sleeve}],    # "0-3M - Short Sleeve"
            "style": [{"value": sleeve_type}],        # "Short Sleeve" / "Long Sleeve"
            "color": [{"value": color_value}],        # "White", "Beige", "Light Pink", "Light Blue"

            # Required offering + packaging
            "list_price": [{"currency": "USD", "value": price_map[variation]}],
            "purchasable_offer": [{
                "currency": "USD",
                "our_price": [{"schedule": [{"value_with_tax": price_map[variation]}]}],
                "marketplace_id": "ATVPDKIKX0DER"
            }],
            "fulfillment_availability": [{
                "quantity": 999,
                "fulfillment_channel_code": "DEFAULT",
                "marketplace_id": "ATVPDKIKX0DER"
            }],
            "item_package_dimensions": [PKG_DIM],
            "item_package_weight": [PKG_WEIGHT],
            "main_product_image_locator": [{
                "media_location": image_url,
                "marketplace_id": "ATVPDKIKX0DER"
            }],

            # Model + GTIN exemption on child, too
            "model_number": [{"value": "NBV"}],
            "model_name": [{"value": "Crew Neck Bodysuit"}],
            "supplier_declared_has_product_identifier_exemption": [{"value": True}]
        }

        messages.append({
            "messageId": i,
            "sku": sku,
            "operationType": "UPDATE",
            "productType": "LEOTARD",
            "requirements": "LISTING",
            "attributes": attributes
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
    if r.status_code != 200:
        raise RuntimeError(f"LWA token fetch failed {r.status_code}: {r.text}")
    data = r.json()
    if "access_token" not in data:
        raise RuntimeError(f"LWA token fetch returned no access_token: {data}")
    return data["access_token"]

def submit_amazon_json_feed(json_feed, access_token):
    # Create feed document
    create_res = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/documents",
        headers={"x-amz-access-token": access_token, "Content-Type": "application/json"},
        json={"contentType": "application/json"}
    )
    if create_res.status_code != 200:
        raise RuntimeError(f"Create document failed {create_res.status_code}: {create_res.text}")

    doc = create_res.json()
    upload_url = doc.get("url") or doc.get("uploadDestinationUrl")
    if not upload_url:
        raise RuntimeError(f"No upload URL in doc response: {doc}")

    # Upload JSON to presigned S3 URL
    up = requests.put(upload_url, data=json_feed.encode("utf-8"),
                      headers={"Content-Type": "application/json"})
    if up.status_code not in (200, 201):
        raise RuntimeError(f"Upload failed {up.status_code}: {up.text}")

    # Submit feed
    feed_res = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds",
        headers={"x-amz-access-token": access_token, "Content-Type": "application/json"},
        json={
            "feedType": "JSON_LISTINGS_FEED",
            "marketplaceIds": [MARKETPLACE_ID],
            "inputFeedDocumentId": doc["feedDocumentId"]
        }
    )
    if feed_res.status_code not in (200, 201):
        raise RuntimeError(f"Submit feed failed {feed_res.status_code}: {feed_res.text}")
    return feed_res.json().get("feedId")

def check_amazon_feed_status(feed_id, access_token):
    res = requests.get(
        f"https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds/{feed_id}",
        headers={"x-amz-access-token": access_token, "Content-Type": "application/json"}
    )
    if res.status_code != 200:
        raise RuntimeError(f"Check feed failed {res.status_code}: {res.text}")
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
st.title("Shopify → Amazon Auto Uploader")

uploaded_files = st.file_uploader(
    "Upload PNG Files (Hold Ctrl or Shift to select multiple)",
    type="png",
    accept_multiple_files=True
)

if uploaded_files:
    all_messages = []
    for uploaded_file in uploaded_files:
        st.markdown(f"---\n### 📦 Processing: `{uploaded_file.name}`")
        try:
            file_stem = os.path.splitext(uploaded_file.name)[0]
            title_full = file_stem.replace("-", " ").replace("_", " ").title() + " - Baby Bodysuit"
            handle = file_stem.lower().replace(" ", "-").replace("_", "-") + "-baby-bodysuit"

            # Preview
            image = Image.open(uploaded_file)
            st.image(image, caption=title_full, use_container_width=True)

            # Shopify image + product
            st.info("Uploading to ImgBB + Creating product on Shopify...")
            uploaded_file.seek(0)
            image_url = upload_and_create_shopify_product(uploaded_file, handle, title_full)
            st.success("✅ Shopify Product Created")

            # Build Amazon messages (aggregate into one feed)
            st.info("Generating Amazon Feed messages...")
            feed_json = json.loads(generate_amazon_json_feed(file_stem, image_url))
            all_messages.extend(feed_json["messages"])
        except Exception as e:
            st.error(f"❌ Error processing {uploaded_file.name}: {e}")

    # Submit combined feed once
    if all_messages:
        st.markdown("## 📡 Submitting Combined Feed to Amazon...")
        try:
            # Reassign unique message IDs
            for idx, msg in enumerate(all_messages, start=1):
                msg["messageId"] = idx

            token = get_amazon_access_token()
            full_feed = {
                "header": {
                    "sellerId": SELLER_ID,
                    "version": "2.0",
                    "issueLocale": "en_US"
                },
                "messages": all_messages
            }

            feed_id = submit_amazon_json_feed(json.dumps(full_feed), token)
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
            st.error(f"❌ Error submitting feed to Amazon: {e}")
