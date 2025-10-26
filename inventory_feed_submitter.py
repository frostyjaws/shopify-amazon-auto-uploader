import requests
import csv
import io

def generate_inventory_feed(skus, quantity=999, latency=2):
    """
    Generate a flat file TSV inventory feed for Amazon with quantity and fulfillment latency (handling time).
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    writer.writerow(["sku", "quantity", "fulfillment_latency"])
    for sku in skus:
        writer.writerow([sku, quantity, latency])
    return output.getvalue()

def submit_inventory_feed(skus, access_token, marketplace_id, seller_id):
    """
    Submits the generated inventory feed to Amazon SP-API using POST_INVENTORY_AVAILABILITY_DATA.
    """
    feed_content = generate_inventory_feed(skus)

    # Step 1: Create the feed document
    doc_res = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/documents",
        headers={
            "x-amz-access-token": access_token,
            "Content-Type": "application/json"
        },
        json={"contentType": "text/tab-separated-values"}
    )
    doc_res.raise_for_status()
    doc = doc_res.json()

    # Step 2: Upload the TSV file content
    upload = requests.put(
        doc["url"],
        data=feed_content.encode("utf-8"),
        headers={"Content-Type": "text/tab-separated-values"}
    )
    upload.raise_for_status()

    # Step 3: Submit the feed to Amazon
    feed_res = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds",
        headers={
            "x-amz-access-token": access_token,
            "Content-Type": "application/json"
        },
        json={
            "feedType": "POST_INVENTORY_AVAILABILITY_DATA",
            "marketplaceIds": [marketplace_id],
            "inputFeedDocumentId": doc["feedDocumentId"]
        }
    )
    feed_res.raise_for_status()
    return feed_res.json()["feedId"]
