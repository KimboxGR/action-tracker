import requests
from bs4 import BeautifulSoup
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

URL = "https://www.action.com/nl-nl/nieuw/"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def get_products():
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    products = []

    for item in soup.select("a[href*='/p/']"):
        name = item.get_text(strip=True)
        link = "https://www.action.com" + item["href"]

        if name:
            products.append({
                "name": name,
                "url": link
            })

    return list({p["url"]: p for p in products}.values())

def load_seen():
    if not os.path.exists("products_seen.json"):
        return []
    with open("products_seen.json", "r") as f:
        return json.load(f)

def save_seen(products):
    with open("products_seen.json", "w") as f:
        json.dump(products, f, indent=2)

def send_email(new_products):
    sender = os.environ["EMAIL_ADDRESS"]
    password = os.environ["EMAIL_PASSWORD"]
    receiver = os.environ["EMAIL_RECEIVER"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{len(new_products)} nieuwe Action producten 🛒"
    msg["From"] = sender
    msg["To"] = receiver

    html = "<h2>Nieuwe producten bij Action:</h2><ul>"
    for product in new_products:
        html += f"<li><a href='{product['url']}'>{product['name']}</a></li>"
    html += "</ul>"

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())

def main():
    current_products = get_products()
    seen_products = load_seen()

    seen_urls = {p["url"] for p in seen_products}
    new_products = [p for p in current_products if p["url"] not in seen_urls]

    if new_products:
        send_email(new_products)
        save_seen(current_products)
        print(f"{len(new_products)} nieuwe producten gevonden en gemaild.")
    else:
        print("Geen nieuwe producten.")

if __name__ == "__main__":
    main()
