"""
Marketplace Domain Data Generator for DealCheck
Generates >= 2,200 synthetic multi-turn buyer-seller marketplace chats
(Facebook Marketplace, OLX, Instagram DMs, Craigslist, OfferUp).
Includes:
- Scam chats: F&F coercion, fee avoidance, urgency, advance payments, off-platform redirects,
  fake courier/escrow, Hinglish / Indian English variants, realistic typos.
- Legitimate chats: in-person inspection, receipt verification, standard negotiation,
  eagerness to use PayPal Goods & Services.
"""

import os
import random
import pandas as pd

random.seed(42)

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(DATA_DIR, "synthetic_marketplace_chats.csv")

ITEMS = [
    ("iPhone 15 Pro Max 256GB", 750, 1100),
    ("PlayStation 5 Disc Edition", 320, 480),
    ("MacBook Pro M2 14-inch", 850, 1300),
    ("Sony Alpha A7 IV Camera", 1200, 1900),
    ("Nvidia RTX 4080 GPU", 700, 1050),
    ("AirPods Max Space Gray", 260, 400),
    ("iPad Air 5th Gen 64GB", 300, 450),
    ("Nintendo Switch OLED", 180, 280),
    ("Dyson Supersonic Hair Dryer", 190, 320),
    ("Apple Watch Ultra 2", 420, 650),
    ("Bose QuietComfort Headphones", 140, 240),
    ("Canon EOS R6 Camera Body", 1100, 1600),
    ("Steam Deck OLED 512GB", 360, 520),
    ("OnePlus 12 512GB", 480, 700),
    ("Samsung Galaxy S24 Ultra", 700, 1150),
    ("Royal Enfield Classic Helmet & Jacket", 90, 160),
    ("Pecan Leather Chesterfield Sofa", 400, 800),
    ("Taylor GS Mini Acoustic Guitar", 350, 550)
]

NAMES = [
    "Alex", "David", "Vikram", "Rahul", "Sarah", "Michael", "Priya", "Arjun",
    "Chris", "Emily", "Aman", "Rohan", "James", "Elena", "Daniel", "Neha"
]

LOCATIONS = [
    "Starbucks near 5th Ave", "Metro station entrance", "Central Mall parking",
    "Local Police Station safe exchange zone", "City Center library", "Whole Foods lobby",
    "Indiranagar 100ft road", "Connaught Place block B", "Bandra Kurla Complex"
]

TYPOS = [
    ("paypal", "pay pal"), ("paypal", "papal"), ("friends and family", "friends & fam"),
    ("friends and family", "f&f"), ("friends and family", "frnds n family"),
    ("friends and family", "f and f"), ("goods and services", "g&s"),
    ("advance", "advnc"), ("guaranteed", "guarnted"), ("tomorrow", "tmrw"),
    ("please", "pls"), ("because", "bcz")
]

def apply_random_typos(text, prob=0.3):
    if random.random() < prob:
        pair = random.choice(TYPOS)
        text = text.replace(pair[0], pair[1])
    return text

def generate_scam_chat():
    item, low_val, high_val = random.choice(ITEMS)
    # Price often heavily discounted for urgency scam
    price = int(low_val * random.uniform(0.5, 0.8))
    seller = random.choice(NAMES)
    
    tactic = random.choice([
        "ff_coercion", "urgency_deposit", "offplatform_redirect",
        "military_shipping", "fake_courier_escrow", "hinglish_advance"
    ])

    if tactic == "ff_coercion":
        templates = [
            [
                f"Buyer: Hi {seller}, is the {item} still available for ${price}?",
                f"Seller: Yes still available! Need it gone quickly. Are you ready to pay now?",
                f"Buyer: Yes, I can take it. Can I pay via PayPal Goods and Services so we both have protection?",
                f"Seller: No sorry, I only accept PayPal Friends and Family. PayPal business takes a big fee and holds my money for 21 days. Send through Friends & Family only.",
                f"Buyer: But Goods and Services protects me if the package doesn't arrive.",
                f"Seller: Bro I have 100% positive reviews on my profile. If you want it, pay by Friends and Family or I will sell to someone else waiting."
            ],
            [
                f"Buyer: Hello! Interested in the {item}. Can we do PayPal?",
                f"Seller: Yes I take PayPal. But please make sure you choose 'Sending to a friend / Friends and Family'. Do NOT select goods and services.",
                f"Buyer: Why not Goods and Services? I'm happy to cover the 3% fee.",
                f"Seller: Because my account is personal not merchant! If you send as goods it gets frozen. Only friends and family option works for me."
            ],
            [
                f"Buyer: Is the {item} in good condition? Any scratches?",
                f"Seller: Pristine condition, like new in box. Price is firm at ${price}.",
                f"Buyer: Awesome. What's your PayPal email?",
                f"Seller: Here: {seller.lower()}.sales88@gmail.com. Select Friends and Family payment only. If you send as business I will refund immediately.",
                f"Buyer: Isn't Friends and Family non-refundable if anything is wrong?",
                f"Seller: Trust me, I ship with FedEx express right away with tracking. F&F avoids taxes and fees."
            ]
        ]
        chat = random.choice(templates)

    elif tactic == "urgency_deposit":
        templates = [
            [
                f"Buyer: Hey, could I come see the {item} today?",
                f"Seller: I have 3 other buyers messaging me right now offering cash. If you want me to hold it for you, you need to send a $50 deposit right now.",
                f"Buyer: Can't I just pay in full when I see it in person?",
                f"Seller: No holds without deposit. Someone is offering to pick up in 30 mins. Send deposit via Friends and Family or CashApp now or I'm letting them have it."
            ],
            [
                f"Buyer: Can you hold the {item} until 5pm when I get off work?",
                f"Seller: Bro, multiple people want this. Send half amount upfront as booking token to lock it. Otherwise first come first served.",
                f"Buyer: I don't feel comfortable sending money before meeting.",
                f"Seller: Then forget it, losing my time. Serious buyers only pay advance."
            ]
        ]
        chat = random.choice(templates)

    elif tactic == "offplatform_redirect":
        redirect_rail = random.choice(["Zelle", "Cash App", "Crypto (USDT)", "Apple Gift Card", "Telegram direct transfer"])
        templates = [
            [
                f"Buyer: Hi, I saw your listing for {item}. Can we complete the checkout on the platform?",
                f"Seller: My marketplace payments are glitching today. Can you send payment through {redirect_rail}?",
                f"Buyer: I'd rather use official protected checkout like PayPal Goods & Services.",
                f"Seller: I don't use PayPal, too many chargeback scammers. Only {redirect_rail}. Once payment is sent I'll courier it immediately."
            ],
            [
                f"Buyer: Can we do in-app payment for the {item}?",
                f"Seller: No in-app payment takes 14 days to clear. Send via {redirect_rail} or Western Union directly. I'll drop the price by $30 for you if you pay right now."
            ]
        ]
        chat = random.choice(templates)

    elif tactic == "military_shipping":
        templates = [
            [
                f"Buyer: Hi! Can I inspect the {item} before buying?",
                f"Seller: I am currently stationed at an army military base in another state, so in-person pickup is not possible. I have arranged free delivery via military courier.",
                f"Buyer: How do we handle payment?",
                f"Seller: You transfer via PayPal Friends and Family to my logistics agent. The courier will deliver within 24 hours.",
                f"Buyer: Can we use Goods & Services with invoice?",
                f"Seller: Military postal regulation does not allow commercial goods invoices. Only friends and family payment is accepted."
            ]
        ]
        chat = random.choice(templates)

    elif tactic == "fake_courier_escrow":
        courier = random.choice(["FedEx Courier Agent", "DHL Secure Delivery", "Express Escrow Service"])
        templates = [
            [
                f"Buyer: Can I come pick up the {item}?",
                f"Seller: I'm too busy to meet. I have registered the delivery with {courier}. They will bring the package to your doorstep and give you cash in an envelope.",
                f"Buyer: Wait, how do I pay?",
                f"Seller: You just need to pay the courier insurance refundable deposit of $120 via PayPal Friends and Family or prepaid voucher first.",
                f"Buyer: That sounds strange. Why would a courier give me cash?",
                f"Seller: It is an official secure courier program. Pay the deposit now and the driver is dispatched."
            ]
        ]
        chat = random.choice(templates)

    else:  # hinglish_advance
        templates = [
            [
                f"Buyer: Bhaiya {item} available hai kya? Final price kya hoga?",
                f"Seller: Haan bhai bilkul available hai. Final {price} dollars / rupees. Ekdum fresh condition hai.",
                f"Buyer: Okay, main kal aake dekh sakta hoon kya?",
                f"Seller: Bhai dekhne ke liye pehle token advance 500 bhej do Google Pay ya PayPal Friends & Family pe. Bahut log message kar rahe hain.",
                f"Buyer: Main aane ke baad hi pay karunga.",
                f"Seller: Aise hold nahi hoga bhai. Advance bhejoge tabhi address dunga nahi toh doosre buyer ko de dunga."
            ],
            [
                f"Buyer: Is {item} available? Can we do PayPal protected payment?",
                f"Seller: Haan available hai. Lekin PayPal Friends and Family se hi karna, business payment mat karna warna tax aur fee katega. Send as personal payment bro.",
                f"Buyer: But G&S is safer.",
                f"Seller: Are bhai vishwas rakho, 100% genuine item hai. F&F karke screenshot bhejo turant pack karta hoon."
            ]
        ]
        chat = random.choice(templates)

    raw_text = "\n".join([apply_random_typos(line) for line in chat])
    return {
        "text": raw_text,
        "label": 1,
        "scam_type": tactic,
        "item": item,
        "price": price
    }

def generate_legit_chat():
    item, low_val, high_val = random.choice(ITEMS)
    price = int(random.uniform(low_val, high_val))
    seller = random.choice(NAMES)
    location = random.choice(LOCATIONS)
    
    tactic = random.choice([
        "in_person_inspection", "paypal_goods_services_ok",
        "detailed_qa_serial", "reasonable_bargain", "receipt_verification"
    ])

    if tactic == "in_person_inspection":
        templates = [
            [
                f"Buyer: Hi {seller}, is the {item} still available?",
                f"Seller: Yes, it's available! In great shape, comes with original charger and box.",
                f"Buyer: Great. Can we meet in person to test it before buying?",
                f"Seller: Absolutely. How about we meet at {location} tomorrow around 2 PM? You can inspect and test everything thoroughly.",
                f"Buyer: That sounds perfect. How would you like payment?",
                f"Seller: Cash in person or PayPal Goods and Services when you're satisfied with the condition."
            ],
            [
                f"Buyer: Hey, interested in the {item}. Can I check it out this evening?",
                f"Seller: Sure! I'm free after 6 PM. We can meet in front of {location}. Let me know if that works for you."
            ]
        ]
        chat = random.choice(templates)

    elif tactic == "paypal_goods_services_ok":
        templates = [
            [
                f"Buyer: Hi, I want to purchase your {item}. Are you able to ship it?",
                f"Seller: Yes, I can ship via tracked UPS. Shipping is around $15 with signature confirmation.",
                f"Buyer: Great. Can we use PayPal Goods and Services? I'll cover the transaction fee.",
                f"Seller: Yes, definitely! I prefer PayPal Goods and Services anyway because it provides seller protection against fraudulent chargebacks.",
                f"Buyer: Perfect! Send me your PayPal email or an invoice link.",
                f"Seller: Sure, here is my link. Once payment shows in my PayPal dashboard, I will create the shipping label and send the tracking number."
            ],
            [
                f"Buyer: Would you accept PayPal for the {item}?",
                f"Seller: Yes, PayPal Goods & Services works great. I want both of us to feel completely secure."
            ]
        ]
        chat = random.choice(templates)

    elif tactic == "detailed_qa_serial":
        templates = [
            [
                f"Buyer: Hello! What is the battery health on the {item}?",
                f"Seller: It is currently at 91% battery health. Never replaced, all OEM parts.",
                f"Buyer: Can you share the serial number so I can check warranty status?",
                f"Seller: Sure, here is the serial: C02G78K9MD6R. AppleCare is valid until December.",
                f"Buyer: Awesome, thank you! I'll take it at the asking price."
            ]
        ]
        chat = random.choice(templates)

    elif tactic == "reasonable_bargain":
        offer = int(price * 0.88)
        counter = int(price * 0.94)
        templates = [
            [
                f"Buyer: Would you consider ${offer} for the {item}?",
                f"Seller: That's a bit low since it's barely used, but I could meet in the middle at ${counter}.",
                f"Buyer: That works for me! When and where can we meet?",
                f"Seller: We can meet at {location} this Saturday morning."
            ]
        ]
        chat = random.choice(templates)

    else:  # receipt_verification
        templates = [
            [
                f"Buyer: Hi {seller}, do you have the original purchase receipt for the {item}?",
                f"Seller: Yes, I bought it from Best Buy 4 months ago. I have both the printed receipt and digital PDF.",
                f"Buyer: That's great peace of mind. Can you send a photo of the receipt with today's date written on a note?",
                f"Seller: Sure, just sent it in chat. Let me know if you want to proceed with pickup or shipping."
            ]
        ]
        chat = random.choice(templates)

    raw_text = "\n".join([apply_random_typos(line, prob=0.15) for line in chat])
    return {
        "text": raw_text,
        "label": 0,
        "scam_type": tactic,
        "item": item,
        "price": price
    }

def generate_marketplace_dataset(num_samples=2400):
    print(f"[DealCheck Synthetic Generator] Generating {num_samples} marketplace domain chats...")
    records = []
    half = num_samples // 2
    
    for _ in range(half):
        records.append(generate_scam_chat())
    for _ in range(num_samples - half):
        records.append(generate_legit_chat())

    random.shuffle(records)
    df = pd.DataFrame(records)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"[DealCheck Synthetic Generator] Successfully saved {len(df):,} synthetic chats to {OUTPUT_FILE}")
    print(f"    Scam chats: {sum(df['label'] == 1):,}, Legit chats: {sum(df['label'] == 0):,}")
    return df

if __name__ == "__main__":
    generate_marketplace_dataset(2400)
