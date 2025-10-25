import streamlit as st
import requests
import os
import json
from PIL import Image
from io import BytesIO
import random

# === CREDENTIALS ===
SHOPIFY_TOKEN = st.secrets["SHOPIFY_TOKEN"]
SHOPIFY_STORE = st.secrets["SHOPIFY_STORE"]
IMGBB_API_KEY = st.secrets["IMGBB_API_KEY"]
LWA_CLIENT_ID = st.secrets["LWA_CLIENT_ID"]
LWA_CLIENT_SECRET = st.secrets["LWA_CLIENT_SECRET"]
REFRESH_TOKEN = st.secrets["REFRESH_TOKEN"]
MARKETPLACE_ID = st.secrets["MARKETPLACE_ID"]
SELLER_ID = st.secrets["SELLER_ID"]

DESCRIPTION = """
<p>Celebrate the arrival of your little one with our adorable Custom Baby onesie&reg;, the perfect baby shower gift that will be cherished for years to come. This charming piece of baby clothing is an ideal new baby gift for welcoming a newborn into the world. Whether it's for a baby announcement, a pregnancy reveal, or a special baby shower, this baby onesie&reg; is sure to delight.</p>

<p>Our Custom Baby onesie&reg; features a playful and cute design, perfect for showcasing your baby's unique personality. Made with love and care, this baby onesie&reg; is designed to keep your baby comfortable and stylish. It's an essential item in cute baby clothes, making it a standout piece for any new arrival.</p>

<p>Perfect for both baby boys and girls, this versatile baby onesie&reg; is soft, comfortable, and durable, ensuring it can withstand numerous washes. The easy-to-use snaps make changing a breeze, providing convenience for busy parents.</p>

<p>Whether you're looking for a personalized baby onesie&reg;, a funny baby onesie&reg;, or a cute baby onesie&reg;, this Custom Baby onesie&reg; has it all. It's ideal for celebrating the excitement of a new baby, featuring charming and customizable designs. This makes it a fantastic option for funny baby clothes that bring a smile to everyone's face.</p>

<p>Imagine gifting this delightful baby onesie&reg; at a baby shower or using it as a memorable baby announcement or pregnancy reveal. It's perfect for anyone searching for a unique baby gift, announcement baby onesie&reg;, or a special new baby onesie&reg;.</p>

<p>This baby onesie&reg; is not just an item of clothing; it's a keepsake that celebrates the joy and wonder of a new life.</p>

<p>From baby boy clothes to baby girl clothes, this baby onesie&reg; is perfect for any newborn. Whether it's a boho design, a Father's Day gift, or custom baby clothes, this piece is a wonderful addition to any baby's wardrobe.</p>
"""

BULLETS =  [
    "🎨 High-Quality Ink Printing: Our Baby Bodysuit features vibrant, long-lasting colors thanks to direct-to-garment printing, ensuring that your baby's outfit looks fantastic wash after wash.",
    "🎖️ Proudly Veteran-Owned: Show your support for our heroes while dressing your little one in style with this adorable newborn romper from a veteran-owned small business.",
    "👶 Comfort and Convenience: Crafted from soft, breathable materials, this Bodysuit provides maximum comfort for your baby. Plus, the convenient snap closure makes diaper changes a breeze.",
    "🎁 Perfect Baby Shower Gift: This funny Baby Bodysuit makes for an excellent baby shower gift or a thoughtful present for any new parents. It's a sweet and meaningful addition to any baby's wardrobe.",
    "📏Versatile Sizing & Colors: Available in a range of sizes and colors, ensuring the perfect fit. Check our newborn outfit boy and girl sizing guide to find the right one for your little one."
]

# === VARIATIONS SPLIT INTO SHORT-SLEEVE PARENT AND LONG-SLEEVE PARENT ===

SHORT_SLEEVE_VARIATIONS = [
    # (size_label, color_label, price)
    ("Newborn Short Sleeve", "White", 29.99),
    ("0–3M Short Sleeve", "White", 29.99),
    ("3–6M Short Sleeve", "White", 29.99),
    ("6–9M Short Sleeve", "White", 29.99),
    ("12M Short Sleeve", "White", 29.99),
    ("18M Short Sleeve", "White", 29.99),
    ("24M Short Sleeve", "White", 29.99),

    ("0–3M Short Sleeve", "Natural", 33.99),
    ("3–6M Short Sleeve", "Natural", 33.99),
    ("6–9M Short Sleeve", "Natural", 33.99),
    ("12M Short Sleeve", "Natural", 33.99),

    ("0–3M Short Sleeve", "Pink", 33.99),
    ("3–6M Short Sleeve", "Pink", 33.99),
    ("6–9M Short Sleeve", "Pink", 33.99),

    ("0–3M Short Sleeve", "Blue", 33.99),
    ("3–6M Short Sleeve", "Blue", 33.99),
    ("6–9M Short Sleeve", "Blue", 33.99),
]

LONG_SLEEVE_VARIATIONS = [
    # White only, long sleeve
    ("Newborn Long Sleeve", "White", 30.99),
    ("0–3M Long Sleeve", "White", 30.99),
    ("3–6M Long Sleeve", "White", 30.99),
    ("6–9M Long Sleeve", "White", 30.99),
    ("12M Long Sleeve", "White", 30.99),
    ("18M Long Sleeve", "White", 30.99),
    ("24M Long Sleeve", "White", 30.99),
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
    r = requests.post(shopify_url, json=payload, headers=headers, verify=False)
    r.raise_for_status()
    shopify_product = r.json()
    shopify_image_url = shopify_product["product"]["images"][0]["src"]
    return shopify_image_url

def generate_amazon_json_feed(title, image_url):
    import json

    # keep your slug style: first letters of words + random 4 digits
    def format_slug(title):
        slug = ''.join([w[0] for w in title.split() if w]).upper()[:3]
        return f"{slug}-{random.randint(1000, 9999)}"

    # we keep the SKU style: slug-SIZECODE-COLORCODE-SLEEVE
    def format_variation_sku(slug, size_label, color_label):
        parts = size_label.split()  # e.g. ["0–3M","Short","Sleeve"] or ["12M","Long","Sleeve"]
        base_size = parts[0]        # "0–3M", "12M", "Newborn", etc.

        size_code = (
            base_size
            .replace("Newborn", "NB")
            .replace("0–3M", "03M")
            .replace("0-3M", "03M")
            .replace("3–6M", "36M")
            .replace("3-6M", "36M")
            .replace("6–9M", "69M")
            .replace("6-9M", "69M")
            .replace("6M", "06M")
            .replace("12M", "12M")
            .replace("18M", "18M")
            .replace("24M", "24M")
        )

        color_code = color_label[0].upper()
        sleeve_code = "SS" if "Short" in size_label else "LS"

        return f"{slug}-{size_code}-{color_code}-{sleeve_code}"

    def build_child_attributes(parent_sku, size_label, color_label, price_value):
        sleeve_type = "Short Sleeve" if "Short" in size_label else "Long Sleeve"

        other_product_images = {
            f"other_product_image_locator_{i+1}": [{
                "media_location": [
                    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/ca9082d9-c0ef-4dbc-a8a8-0de85b9610c0-copy.jpg?v=1744051115",
                    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/26363115-65e5-4936-b422-aca4c5535ae1-copy.jpg?v=1744051115",
                    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/a050c7dc-d0d5-4798-acdd-64b5da3cc70c-copy.jpg?v=1744051115"
                ][i % 3],
                "marketplace_id": "ATVPDKIKX0DER"
            }] for i in range(5)
        }

        return {
            "item_name": [{"value": f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute"}],
            "brand": [{"value": "NOFO VIBES"}],
            "item_type_keyword": [{"value": "infant-and-toddler-bodysuits"}],
            "product_description": [{"value": DESCRIPTION}],
            "bullet_point": [{"value": b} for b in BULLETS],
            "target_gender": [{"value": "female"}],
            "age_range_description": [{"value": "Infant"}],
            "material": [{"value": "Cotton"}],
            "department": [{"value": "Baby Girls"}],
            "variation_theme": [{"name": "SIZE/COLOR"}],
            "parentage_level": [{"value": "child"}],
            "child_parent_sku_relationship": [{
                "child_relationship_type": "variation",
                "parent_sku": parent_sku
            }],
            "size": [{"value": size_label}],
            "style": [{"value": sleeve_type}],
            "model_number": [{"value": "NBV"}],
            "model_name": [{"value": "Crew Neck Bodysuit"}],
            "import_designation": [{"value": "Made in USA"}],
            "country_of_origin": [{"value": "US"}],
            "condition_type": [{"value": "new_new"}],
            "batteries_required": [{"value": False}],
            "fabric_type": [{"value": "100% cotton"}],
            "supplier_declared_dg_hz_regulation": [{"value": "not_applicable"}],
            "supplier_declared_has_product_identifier_exemption": [{"value": True}],
            "care_instructions": [{"value": "Machine Wash"}],
            "sleeve": [{"value": sleeve_type}],
            "color": [{"value": color_label}],
            "list_price": [{"currency": "USD", "value": price_value}],
            "item_package_dimensions": [{
                "length": {"value": 3, "unit": "inches"},
                "width": {"value": 3, "unit": "inches"},
                "height": {"value": 1, "unit": "inches"}
            }],
            "item_package_weight": [{"value": 0.19, "unit": "kilograms"}],
            "main_product_image_locator": [{
                "media_location": image_url,
                "marketplace_id": "ATVPDKIKX0DER"
            }],
            **other_product_images,
            "purchasable_offer": [{
                "currency": "USD",
                "our_price": [{"schedule": [{"value_with_tax": price_value}]}],
                "marketplace_id": "ATVPDKIKX0DER"
            }],
            "fulfillment_availability": [{
                "quantity": 999,
                "fulfillment_channel_code": "DEFAULT",
                "marketplace_id": "ATVPDKIKX0DER"
            }]
        }

    slug = format_slug(title)

    short_parent_sku = f"{slug}-SHORT-PARENT"
    long_parent_sku = f"{slug}-LONG-PARENT"

    messages = []

    # Parent A: short sleeve family
    messages.append({
        "messageId": 1,
        "sku": short_parent_sku,
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
            "material": [{"value": "Cotton"}],
            "department": [{"value": "Baby Girls"}],
            "variation_theme": [{"name": "SIZE/COLOR"}],
            "parentage_level": [{"value": "parent"}],
            "model_number": [{"value": "NBV"}],
            "model_name": [{"value": title}],
            "import_designation": [{"value": "Imported"}],
            "country_of_origin": [{"value": "US"}],
            "condition_type": [{"value": "new_new"}],
            "batteries_required": [{"value": False}],
            "fabric_type": [{"value": "100% cotton"}],
            "supplier_declared_dg_hz_regulation": [{"value": "not_applicable"}],
            "supplier_declared_has_product_identifier_exemption": [{"value": True}]
        }
    })

    # Parent B: long sleeve family
    messages.append({
        "messageId": 2,
        "sku": long_parent_sku,
        "operationType": "UPDATE",
        "productType": "LEOTARD",
        "requirements": "LISTING",
        "attributes": {
            "item_name": [{"value": f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute Long Sleeve"}],
            "brand": [{"value": "NOFO VIBES"}],
            "item_type_keyword": [{"value": "infant-and-toddler-bodysuits"}],
            "product_description": [{"value": DESCRIPTION}],
            "bullet_point": [{"value": b} for b in BULLETS],
            "target_gender": [{"value": "female"}],
            "age_range_description": [{"value": "Infant"}],
            "material": [{"value": "Cotton"}],
            "department": [{"value": "Baby Girls"}],
            "variation_theme": [{"name": "SIZE/COLOR"}],
            "parentage_level": [{"value": "parent"}],
            "model_number": [{"value": "NBV"}],
            "model_name": [{"value": title + " Long Sleeve"}],
            "import_designation": [{"value": "Imported"}],
            "country_of_origin": [{"value": "US"}],
            "condition_type": [{"value": "new_new"}],
            "batteries_required": [{"value": False}],
            "fabric_type": [{"value": "100% cotton"}],
            "supplier_declared_dg_hz_regulation": [{"value": "not_applicable"}],
            "supplier_declared_has_product_identifier_exemption": [{"value": True}]
        }
    })

    # Children under short-sleeve parent
    msg_id = 3
    for (size_label, color_label, price_value) in SHORT_SLEEVE_VARIATIONS:
        sku = format_variation_sku(slug, size_label, color_label)
        attrs = build_child_attributes(short_parent_sku, size_label, color_label, price_value)

        messages.append({
            "messageId": msg_id,
            "sku": sku,
            "operationType": "UPDATE",
            "productType": "LEOTARD",
            "requirements": "LISTING",
            "attributes": attrs
        })
        msg_id += 1

    # Children under long-sleeve parent
    for (size_label, color_label, price_value) in LONG_SLEEVE_VARIATIONS:
        sku = format_variation_sku(slug, size_label, color_label)
        attrs = build_child_attributes(long_parent_sku, size_label, color_label, price_value)

        messages.append({
            "messageId": msg_id,
            "sku": sku,
            "operationType": "UPDATE",
            "productType": "LEOTARD",
            "requirements": "LISTING",
            "attributes": attrs
        })
        msg_id += 1

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

# === MULTI FILE MODE ===
uploaded_files = st.file_uploader("Upload PNG Files (Hold Ctrl or Shift to select multiple)", type="png", accept_multiple_files=True)

if uploaded_files:
    all_messages = []
    all_skus = []
    for uploaded_file in uploaded_files:
        st.markdown(f"---\n### 📦 Processing: `{uploaded_file.name}`")
        try:
            file_stem = os.path.splitext(uploaded_file.name)[0]
            title_full = file_stem.replace("-", " ").replace("_", " ").title() + " - Baby Bodysuit"
            handle = file_stem.lower().replace(" ", "-").replace("_", "-") + "-baby-bodysuit"
            image = Image.open(uploaded_file)
            st.image(image, caption=title_full, use_container_width=True)
            st.info("Uploading to ImgBB + Creating product on Shopify...")
            uploaded_file.seek(0)
            image_url = upload_and_create_shopify_product(uploaded_file, handle, title_full)
            st.success("✅ Shopify Product Created")

            st.info("Generating Amazon Feed...")
            json_feed = json.loads(generate_amazon_json_feed(file_stem, image_url))
            all_messages.extend(json_feed["messages"])
            for msg in json_feed["messages"]:
                if msg.get("sku"):
                    all_skus.append(msg["sku"])
        except Exception as e:
            st.error(f"❌ Error processing {uploaded_file.name}: {e}")

    if all_messages:
        st.markdown("## 📡 Submitting Combined Feed to Amazon...")
        try:
            # Reassign message IDs to avoid duplication
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

        except Exception as e:
            st.error(f"❌ Error submitting feed to Amazon: {e}")
    if st.button("📤 Submit to Shopify + Amazon"):
        st.info("🔹 Starting process...")
        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
        file_stem = os.path.splitext(uploaded_file.name)[0]
        title_full = file_stem.replace("-", " ").replace("_", " ").title() + " - Baby Bodysuit"
        handle = file_stem.lower().replace(" ", "-").replace("_", "-") + "-baby-bodysuit"
        st.image(image, caption=title_full, use_container_width=True)
        st.info("🔹 Image loaded, beginning Shopify upload...")
        try:
            st.info("Uploading to ImgBB + Creating product on Shopify...")
            uploaded_file.seek(0)
            image_url = upload_and_create_shopify_product(uploaded_file, handle, title_full)

            st.success("✅ Shopify Product Created")

            st.info("Generating Amazon Feed...")
            token = get_amazon_access_token()
            json_feed = generate_amazon_json_feed(file_stem, image_url)

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
