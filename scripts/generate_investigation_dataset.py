import json
import random
import os
import hashlib
from datetime import datetime, timedelta

def generate_dataset():
    # Drug Intelligence Dictionary
    DRUG_DICT = [
        {
            "name": "MDMA",
            "aliases": ["ecstasy", "party pills", "molly", "mandy", "e"],
            "emojis": ["💊", "🔌"],
            "slang": ["party pills", "ecstasy", "molly", "mandy"],
            "hashtags": ["#party", "#rave", "#ecstasy", "#mdma"],
            "risk_level": "HIGH",
            "hindi_spelling": "एमडीएमए",
            "hinglish_spelling": "party pills",
            "misspellings": ["mdma", "extasy", "moly", "ecstacy"],
            "abbreviations": ["MD", "Molly"],
            "overview": "3,4-Methylenedioxymethamphetamine (MDMA), commonly known as ecstasy or molly, is a synthetic drug that alters mood and perception. It is highly circulated in night clubs and rave parties in urban Indian hubs like Goa, Mumbai, and Delhi."
        },
        {
            "name": "LSD",
            "aliases": ["acid", "tabs", "blotters", "lucy", "trips"],
            "emojis": ["🌈", "👁️", "🌌"],
            "slang": ["tabs", "acid", "blotters", "trips"],
            "hashtags": ["#trip", "#psychedelic", "#acid", "#lsd"],
            "risk_level": "HIGH",
            "hindi_spelling": "एलएसडी",
            "hinglish_spelling": "acid",
            "misspellings": ["lsd", "acid tabs", "blotter"],
            "abbreviations": ["LSD"],
            "overview": "Lysergic acid diethylamide (LSD), also known colloquially as acid, is a potent psychedelic drug. Often distributed as small squares of blotter paper (tabs) decorated with colorful art, highly prevalent in the Goa party circuit."
        },
        {
            "name": "Mephedrone",
            "aliases": ["meow meow", "meow", "cat", "m-cat", "drone"],
            "emojis": ["😼", "🐈"],
            "slang": ["meow meow", "cat", "m-cat", "drone"],
            "hashtags": ["#meow", "#meowmeow", "#drone", "#mephedrone"],
            "risk_level": "HIGH",
            "hindi_spelling": "मेफेड्रोन",
            "hinglish_spelling": "meow meow",
            "misspellings": ["mephedrone", "meowmeow", "mephedrin"],
            "abbreviations": ["M-Cat", "MCAT"],
            "overview": "Mephedrone, also known as meow meow or M-Cat, is a synthetic stimulant drug of the amphetamine and cathinone classes. It has become a severe issue in Mumbai and other metro cities due to cheap pricing and high addictiveness."
        },
        {
            "name": "Cocaine",
            "aliases": ["coke", "snow", "white", "blow", "charlie"],
            "emojis": ["❄️", "🔑", "👃"],
            "slang": ["snow", "white", "coke", "blow"],
            "hashtags": ["#snow", "#coke", "#cocaine", "#white"],
            "risk_level": "HIGH",
            "hindi_spelling": "कोकीन",
            "hinglish_spelling": "coke",
            "misspellings": ["cocain", "coke", "charlie"],
            "abbreviations": ["C"],
            "overview": "Cocaine is a strong stimulant most frequently used as a recreational drug. It is commonly snorted, inhaled, or injected. Circulated as a high-end luxury drug in elite metropolitan parties, with extremely high profit margins."
        },
        {
            "name": "Cannabis",
            "aliases": ["weed", "pot", "ganja", "charas", "hash", "malana", "420"],
            "emojis": ["🍁", "🍃", "💨"],
            "slang": ["weed", "ganja", "charas", "hash", "malana cream"],
            "hashtags": ["#weed", "#420", "#ganja", "#cannabis", "#charas"],
            "risk_level": "MEDIUM",
            "hindi_spelling": "गांजा",
            "hinglish_spelling": "weed",
            "misspellings": ["ganja", "charras", "weeed", "hashh"],
            "abbreviations": ["420"],
            "overview": "Cannabis, also known as weed, ganja, or marijuana, is widely consumed in India in various forms like weed buds, hashish (charas), and bhang. Cultivation occurs in Himachal Pradesh (Malana) and is smuggled across the country."
        },
        {
            "name": "Heroin",
            "aliases": ["smack", "chitta", "brown sugar", "junk", "h"],
            "emojis": ["💉", "🥄"],
            "slang": ["chitta", "smack", "brown sugar"],
            "hashtags": ["#chitta", "#heroin", "#smack", "#junk"],
            "risk_level": "CRITICAL",
            "hindi_spelling": "हेरोइन",
            "hinglish_spelling": "chitta",
            "misspellings": ["heroin", "chita", "smak"],
            "abbreviations": ["H"],
            "overview": "Heroin, commonly known in northern India (particularly Punjab) as Chitta or smack, is an opioid drug synthesized from morphine. It has caused massive public health crises due to injection and severe addiction rates."
        }
    ]

    # Pre-generate entities
    CITIES = [
        {"name": "Delhi NCR", "lat": 28.6139, "lon": 77.2090},
        {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
        {"name": "Goa", "lat": 15.2993, "lon": 74.1240},
        {"name": "Punjab (Amritsar)", "lat": 31.6340, "lon": 74.8723},
        {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946}
    ]

    PLATFORMS = ["telegram", "whatsapp", "instagram"]

    # Generate 100 fake wallets
    crypto_wallets = []
    for i in range(100):
        prefix = random.choice(["0x", "T", "1", "bc1"])
        if prefix == "0x": # Ethereum / BSC
            addr = "0x" + "".join(random.choices("0123456789abcdef", k=40))
        elif prefix == "T": # Tron
            addr = "T" + "".join(random.choices("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", k=33))
        elif prefix == "bc1": # Bitcoin Segwit
            addr = "bc1" + "".join(random.choices("0123456789abcdefghijklmnopqrstuvwxyz", k=39))
        else: # Bitcoin Legacy
            addr = "1" + "".join(random.choices("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", k=33))
        crypto_wallets.append(addr)

    # Generate 50 fake emails
    emails = []
    email_providers = ["gmail.com", "protonmail.com", "tutanota.com", "mail.ru", "yandex.com"]
    words = ["party", "snow", "trips", "weed", "fastdel", "secure", "shadow", "ghost", "dark", "hustle", "silent", "operator"]
    for i in range(50):
        emails.append(f"{random.choice(words)}{random.randint(10, 999)}@{random.choice(email_providers)}")

    # Generate 100 fake phone numbers
    phones = []
    for i in range(100):
        phones.append(f"+91 {random.choice([6, 7, 8, 9])}{random.randint(10, 99)} {random.randint(10000, 99999)}")

    # Generate 150 fake sellers and 350 fake buyers (Total 500 accounts)
    accounts = []
    first_names = ["Rohan", "Vikram", "Rahul", "Amit", "Karan", "Pooja", "Anjali", "Siddharth", "Simran", "Harpreet", "Manpreet", "Arjun", "Neeraj", "Sanjay", "Deepak", "Aditya", "Sameer", "Rajesh", "Priya", "Sunita"]
    last_names = ["Sharma", "Singh", "Verma", "Mehta", "Patel", "Gupte", "Joshi", "Gill", "Sodhi", "Kapoor", "Nair", "Reddy", "Rao", "Dubey", "Mishra", "Gupta", "Sen", "Bose", "Choudhury", "Das"]

    # Let's pre-generate 30 bot accounts out of these 500
    bot_indices = set(random.sample(range(500), 30))

    # Cross-linked identity sets
    # We will make 15 specific sellers / buyers cross-linked across platforms with identical details
    cross_linked_identities = []
    for idx in range(15):
        first = random.choice(first_names)
        last = random.choice(last_names)
        username_base = f"{first.lower()}_{last.lower()}{random.randint(7, 99)}"
        phone = phones[idx]
        email = emails[idx % len(emails)]
        wallet = crypto_wallets[idx % len(crypto_wallets)]
        
        # This identity links all 3 platforms
        cross_linked_identities.append({
            "name": f"{first} {last}",
            "telegram_username": f"@{username_base}",
            "instagram_handle": f"@{username_base}_ig",
            "whatsapp_number": phone,
            "phone": phone,
            "email": email,
            "wallet": wallet,
            "risk_score": random.randint(75, 98),
            "bot_probability": 0.05 if idx > 2 else 0.85,
            "is_bot": idx <= 2
        })

    for i in range(500):
        is_seller = (i < 150)
        is_bot = i in bot_indices
        
        # Check if we link to a pre-defined cross-linked identity
        if i < len(cross_linked_identities):
            id_data = cross_linked_identities[i]
            accounts.append({
                "id": f"ACC-{i+1:04d}",
                "role": "seller" if is_seller else "buyer",
                "display_name": id_data["name"],
                "telegram_username": id_data["telegram_username"],
                "instagram_handle": id_data["instagram_handle"],
                "whatsapp_number": id_data["whatsapp_number"],
                "phone": id_data["phone"],
                "email": id_data["email"],
                "wallet": id_data["wallet"],
                "risk_score": id_data["risk_score"],
                "bot_probability": id_data["bot_probability"],
                "is_bot": id_data["is_bot"]
            })
        else:
            first = random.choice(first_names)
            last = random.choice(last_names)
            username_base = f"{first.lower()}_{last.lower()}{random.randint(10, 9999)}"
            phone = random.choice(phones) if random.random() > 0.3 else f"+91 {random.choice([6,7,8,9])}{random.randint(10,99)} {random.randint(10000, 99999)}"
            email = random.choice(emails) if random.random() > 0.4 else f"{username_base}@{random.choice(email_providers)}"
            wallet = random.choice(crypto_wallets) if random.random() > 0.5 else None
            
            accounts.append({
                "id": f"ACC-{i+1:04d}",
                "role": "seller" if is_seller else "buyer",
                "display_name": f"{first} {last}",
                "telegram_username": f"@{username_base}",
                "instagram_handle": f"@{username_base}_ig",
                "whatsapp_number": phone,
                "phone": phone,
                "email": email,
                "wallet": wallet,
                "risk_score": random.randint(65, 99) if is_seller else random.randint(15, 60),
                "bot_probability": random.uniform(0.7, 0.99) if is_bot else random.uniform(0.01, 0.25),
                "is_bot": is_bot
            })

    # Platforms communities/pages/channels
    tg_channels = [f"@{random.choice(['delhi', 'goa', 'mumbai', 'punjab', 'blr'])}_{random.choice(['weed', 'mdma', 'trips', 'delivery', 'plug', 'stash'])}_{random.randint(10,99)}" for _ in range(50)]
    ig_pages = [f"@{random.choice(['ecstasy', 'acid', 'coke', 'psy', 'trippy', 'chill'])}_{random.choice(['pills', 'india', 'goa', 'vibe', 'del', 'mumb'])}_{random.randint(10,99)}" for _ in range(40)]
    wa_communities = [f"{random.choice(['Goa Rave', 'Delhi Nightlife', 'Mumbai Stash', 'Punjab Chitta', 'Bangalore 420'])} {random.choice(['Supplies', 'Direct', 'Group', 'Network', 'Connect'])} #{random.randint(1,9)}" for _ in range(20)]

    # Generate 1,000 conversations
    conversations = []
    
    # Message templates by drug, language and role
    SELLER_TEMPLATES = {
        "MDMA": {
            "english": [
                "Available high grade MDMA pills. Premium quality direct from Europe. Price list: 10 tabs for 8k, 25 tabs for 18k. DM to order. Discreet shipping.",
                "Top shelf Molly crystal and ecstasy pills ready. Tested 94% pure. WhatsApp me or hit my telegram for menu. Crypto/UPI accepted.",
                "Ecstasy party pills available in bulk, pure quality. Fast delivery, cash on delivery available in South Delhi. Contact soon."
            ],
            "hinglish": [
                "Bhai MDMA available hai, best quality. 10 pills ka rate 7500 padega. Fast delivery. DM on telegram.",
                "Molly crystal and ecstasy pills ready stock. Goa main hand-to-hand delivery ho jayegi. WhatsApp me for location.",
                "Ecstasy and MDMA direct stash available in Mumbai. Quality trusted. Safe drop locations only. DM for price list."
            ],
            "hindi": [
                "एमडीएमए और परतों की गोलियां उपलब्ध हैं। उच्च गुणवत्ता, सुरक्षित वितरण। थोक दरों के लिए संपर्क करें। केवल दिल्ली एनसीआर।",
                "पार्टी की गोलियां उपलब्ध हैं, 95% शुद्धता। अभी ऑर्डर करें। डिलीवरी कैश ऑन डिलीवरी। व्हाट्सएप पर संपर्क करें।"
            ],
            "punjabi": [
                "MDMA te ecstasy pills vadiya quality de available ne. Amritsar te Ludhiana vich delivery ho jaugi ji. DM karo rate layi."
            ]
        },
        "LSD": {
            "english": [
                "LSD blotters / tabs in stock. VoidRealms 200ug and GoblinDen 155ug. Price: 1.5k per tab. Bulk discounts available. Safe stealth shipping.",
                "Psychedelic acid tabs ready to ship. Triple dipped blotters. Tested clean. 5 tabs for 6k. DM for wallet address.",
                "Trips blotters available now in Goa. Premium paper. Hand delivery in Anjuna and Vagator. Telegram now."
            ],
            "hinglish": [
                "Acid tabs (LSD) available hai. VoidRealms 200ug tabs direct from Netherlands. 5 tabs ka 6500. DM for order.",
                "LSD trips aur blotters ready in Bangalore. Hand to hand pickup available. UPI accept ho jayega. DM fast."
            ],
            "hindi": [
                "एलएसडी एसिड टैब उपलब्ध हैं। 200ug शुद्धता। सुरक्षित पैकेजिंग और डिलीवरी। केवल गंभीर खरीदार संपर्क करें।"
            ],
            "punjabi": [
                "LSD acid tabs available ne ji. Bohot vadiya quality. 5 tabs de 6000 lagan ge. Telegram te message karo."
            ]
        },
        "Mephedrone": {
            "english": [
                "Premium Mephedrone (Meow Meow / M-Cat) crystals in stock. 1g for 3.5k, 5g for 15k. High purity stimulant. Delivery within Mumbai in 2 hours.",
                "Meow Meow available. Cheap rates, high hit. Safe drop points in Pune and Mumbai. WhatsApp for menu.",
                "Drone/M-cat crystals available in Delhi NCR. Overnight shipping. Payment via Bitcoin/Monero or UPI voucher."
            ],
            "hinglish": [
                "Meow Meow / Mephedrone crystals available hai Mumbai me. 1g ka rate 3000 rs. Safe hand delivery, no risk. WhatsApp fast.",
                "Meow meow cat available in bulk. Purity check screen ready. Price details ke liye DM karo."
            ],
            "hindi": [
                "मेफेड्रोन (म्याऊ म्याऊ) क्रिस्टल मुंबई में उपलब्ध है। तेज़ और गुप्त डिलीवरी। व्हाट्सएप पर मेनू मांगें।"
            ],
            "punjabi": [
                "M-cat drone crystal available hai ji. Vadiya quality, sasta rate. Chandigarh vich home delivery ho jaugi."
            ]
        },
        "Cocaine": {
            "english": [
                "92% pure Colombian Cocaine (Snow / White) available. Uncut, direct from source. 1g for 12k, 5g for 50k. Elite quality only. Serious buyers.",
                "Coke in stock. Soft white powder, high purity. Bangalore delivery. Telegram for stealth drop instructions.",
                "Cocaine crystals available. Can do purity test in front of you. Cash payment accepted in Goa. Contact now."
            ],
            "hinglish": [
                "Colombia ka pure Cocaine (White/Snow) ready in South Delhi. 1g ka 10,000. Pure crystal. Payment via crypto/UPI.",
                "Coke and blow available. Super fast delivery in Mumbai suburbs. High profile client list. DM for trust."
            ],
            "hindi": [
                "सफेद कोकीन उपलब्ध है, 90% से अधिक शुद्धता। दिल्ली और मुंबई में सुरक्षित होम डिलीवरी। भुगतान गुप्त रहेगा।"
            ],
            "punjabi": [
                "Colombian Cocaine available ji. Pure white snow. 1g da price 11,000. DM karo jaldi order layi."
            ]
        },
        "Cannabis": {
            "english": [
                "Premium Himachal Hash (Malana Cream) and hydroponic Weed in stock. Malana Tola for 6k. Hydro buds: 3k per gram. Bangalore delivery.",
                "Weed / Ganja available. Green sticky buds, great smell. Local delivery in Goa and Delhi. DM for prices.",
                "Charas (hashish) from Parvati Valley. Unadulterated, direct from farmers. Bulk and retail. TG me."
            ],
            "hinglish": [
                "Malana Cream hash available hai. Ekdum fresh stuff. Rs. 5000 per tola. Delhi me hand-to-hand delivery. Telegram me.",
                "Hydro weed buds available in Delhi and Mumbai. Sativa and Indica strains. Green sticky buds. DM for rates."
            ],
            "hindi": [
                "हिमाचली चरस (मलाना क्रीम) और आयातित गांजा उपलब्ध है। सर्वोत्तम गुणवत्ता, कम दाम। पूरे भारत में सुरक्षित पार्सल वितरण।"
            ],
            "punjabi": [
                "Vadiya Malana Cream te ganja available hai ji. Kasol da asli maal. Price te delivery details layi DM karo."
            ]
        },
        "Heroin": {
            "english": [
                "High quality smack / brown sugar available. Purity tested. Safe supply chain in Punjab and Haryana. Bulk quantity available for wholesale. DM.",
                "Chitta (Heroin) and Brown Sugar ready stock. Ludhiana/Jalandhar local delivery within 1 hour. Trusted network. Contact.",
                "Pure Afghan Heroin in stock. Extremely high potency. Safe delivery and payment options. Contact on Telegram."
            ],
            "hinglish": [
                "Chitta (Smack) and brown sugar available in Punjab. Pure stuff. Rs 4000 per gram. Ludhiana/Amritsar delivery.",
                "Afghan chitta available in bulk. Safe payment via USDT or bank drop. Local delivery secure. PM on WhatsApp."
            ],
            "hindi": [
                "उच्च श्रेणी की हेरोइन (चिट्टा) और ब्राउन शुगर उपलब्ध है। पंजाब और अमृतसर क्षेत्र में सुरक्षित आपूर्ति।"
            ],
            "punjabi": [
                "A-one quality Chitta (Heroin) te smack ready hai. Amritsar, Jalandhar te Tarn Taran vich hand delivery sasti te tez. WhatsApp te details lao."
            ]
        }
    }

    BUYER_TEMPLATES = {
        "MDMA": {
            "english": [
                "Looking for MDMA / ecstasy pills in Mumbai tonight. Need 5 pills. Can pick up. DM me if active.",
                "Anyone selling molly crystals in Goa? Near Vagator. Drop prices and contact details.",
                "Need 10 tabs of ecstasy for a party tonight in Delhi. High confidence plug only."
            ],
            "hinglish": [
                "Bhai Goa me MDMA kaha milegi? Need 5 tabs tonight. Payment cash or UPI.",
                "Delhi NCR me MDMA party pills ka plug batado koi. Looking for pure quality.",
                "MDMA crystal chahiye 2g Mumbai me. Urgent requirement. Payment ready."
            ],
            "hindi": [
                "क्या आज रात दिल्ली में एमडीएमए या एक्स्टसी मिल सकती है? 5 गोलियों की जरूरत है।",
                "गोवा में पार्टी पिल्स (MDMA) का कोई भरोसेमंद डीलर है क्या? कृपया संपर्क करें।"
            ],
            "punjabi": [
                "MDMA pills chahidiya ne Amritsar vich. Koi seller active hai taan rate daso."
            ]
        },
        "LSD": {
            "english": [
                "Need 5 blotter tabs of acid in Goa immediately. Anjuna area. DM with rates.",
                "Looking for LSD acid tabs (VoidRealms preferred). Bangalore. Can pay in crypto.",
                "Any active plugs for acid tabs in South Delhi? Need a strip. Cash ready."
            ],
            "hinglish": [
                "LSD tabs/acid milegi Goa me? Anjuna beach ke pas pickup ho sakta hai. Prices batao.",
                "Acid tabs chahiyen 5. Delhi me delivery milegi? Instant payment ready.",
                "Bhai acid blotters/tabs ka rate kya hai? Looking for good stuff in Bangalore."
            ],
            "hindi": [
                "एलएसडी एसिड टैब (LSD tabs) की आवश्यकता है, गोवा में। क्या कोई वितरित कर सकता है?"
            ],
            "punjabi": [
                "LSD acid tabs di lod hai Ludhiana vich. Kisi kol vadiya tabs hain taan rate daso ji."
            ]
        },
        "Mephedrone": {
            "english": [
                "Looking for 2g Meow Meow (Mephedrone) in Mumbai. Cash ready. Near Andheri. Telegram me.",
                "Need drone/m-cat crystals in Pune. Urgent requirement. High confidence plug only.",
                "Anyone active for meow meow delivery in Mumbai tonight? Drop prices."
            ],
            "hinglish": [
                "Meow Meow (M-cat) milega Mumbai me urgent? 2 grams chahiye. Drop point Andheri.",
                "Meow meow drone crystal ka price kya chal raha hai? Looking to buy 5g in Pune."
            ],
            "hindi": [
                "मुंबई में म्याऊ म्याऊ (मेफेड्रोन) कहां मिलेगी? आज रात 2 ग्राम की जरूरत है।"
            ],
            "punjabi": [
                "Meow meow crystal chahida hai Chandigarh vich. Urgent delivery chahiye ji."
            ]
        },
        "Cocaine": {
            "english": [
                "Looking for Colombia Cocaine in Delhi. Need 2g. Ready to pay premium for pure uncut stuff.",
                "Need coke in Bangalore. Immediate pickup or delivery. Verified sellers only.",
                "Any plug for snow / white in Goa? Near Candolim. Drop prices."
            ],
            "hinglish": [
                "Cocaine (white snow) 1g chahiye South Delhi me. High quality uncut maal hona chahiye. Rate batao.",
                "Coke/blow ka kya rate chal raha hai Mumbai me? Need 2g tonight. Plugs text me."
            ],
            "hindi": [
                "कोकीन (Cocaine) की जरूरत है दिल्ली में। क्या कोई होम डिलीवरी दे सकता है?"
            ],
            "punjabi": [
                "Colombian Coke chahida hai Jalandhar vich. 2g di lod hai. Price te delivery daso."
            ]
        },
        "Cannabis": {
            "english": [
                "Need Malana Cream hash in Delhi. 1 tola. Hand delivery preferred. Cash ready.",
                "Looking for hydro weed buds in Bangalore. High quality sativa. Price?",
                "Need clean hash / weed in Goa. Near Calangute. Direct delivery plug please."
            ],
            "hinglish": [
                "Weed/ganja chahiye Delhi NCR me. Vadiya quality ka hydro buds ya hash milega?",
                "Malana Cream hash ka price kya hai Goa me? Need 1 tola urgently."
            ],
            "hindi": [
                "गांजा (weed) या मलाना क्रीम चरस चाहिए दिल्ली में। होम डिलीवरी उपलब्ध है?"
            ],
            "punjabi": [
                "Kasol di charas (hash) chahidi hai Chandigarh vich. 1 tola da rate daso ji."
            ]
        },
        "Heroin": {
            "english": [
                "Looking for smack/heroin in Amritsar. Need 2g. Immediate delivery. Cash payment.",
                "Urgent requirement for chitta (heroin) in Jalandhar. DM if you have active stock.",
                "Need brown sugar / heroin in Ludhiana. Drop contact or telegram username."
            ],
            "hinglish": [
                "Chitta (Heroin) milega Ludhiana me hand delivery? Urgent requirement, rates batao.",
                "Smack or heroin ka supply plug chahiye Punjab me. Daily requirement. DM on telegram."
            ],
            "hindi": [
                "हेरोइन (चिट्टा) या ब्राउन शुगर की जरूरत है अमृतसर में। सुरक्षित वितरण चाहिए।"
            ],
            "punjabi": [
                "Chitta di lod hai Amritsar vich urgently. 2g chahida hai. Payment te delivery points daso."
            ]
        }
    }

    NEUTRAL_TEMPLATES = [
        "Hey! Are you guys going to the party tonight?",
        "Yes, the music festival line-up in Goa looks amazing.",
        "Can anyone recommend a good hotel near Calangute beach?",
        "Weather in Delhi is extremely hot today.",
        "Mumbai local trains are delayed due to rain.",
        "Did you watch the cricket match yesterday?",
        "Can someone help me with this coding assignment?",
        "Where is the best butter chicken in Amritsar?",
        "Bitcoin price is crashing again, anyone holding?",
        "Let's meet tomorrow evening near Connaught Place.",
        "Suggest some good restaurants in Bangalore near Indiranagar."
    ]

    # Generate 1,000 items
    start_date = datetime.now() - timedelta(days=30)
    
    for idx in range(1000):
        # Determine timestamp
        random_minutes = random.randint(0, 30 * 24 * 60)
        timestamp_dt = start_date + timedelta(minutes=random_minutes)
        timestamp_str = timestamp_dt.isoformat() + "Z"

        # Determine platform
        platform = random.choice(PLATFORMS)
        
        # Determine group or channel
        if platform == "telegram":
            channel_or_group = random.choice(tg_channels)
        elif platform == "instagram":
            channel_or_group = random.choice(ig_pages)
        else: # WhatsApp
            channel_or_group = random.choice(wa_communities)

        # Decide type (seller, buyer, neutral, spam/bot)
        # We need ~150 fake sellers, 350 fake buyers, rest neutral/spam
        rand_role = random.random()
        if rand_role < 0.25: # Seller chat
            role = "seller"
        elif rand_role < 0.70: # Buyer chat
            role = "buyer"
        elif rand_role < 0.90: # Neutral chat
            role = "neutral"
        else: # Spam / Bots
            role = "spam"

        # Match to account
        if role == "seller":
            # Select a seller account (from first 150 accounts)
            acc = random.choice(accounts[:150])
        elif role == "buyer":
            # Select a buyer account (from index 150 to 500)
            acc = random.choice(accounts[150:])
        else:
            # Select any account or generate a random one
            acc = random.choice(accounts)

        # Map details
        username = acc["telegram_username"] if platform == "telegram" else (acc["instagram_handle"] if platform == "instagram" else acc["whatsapp_number"])
        display_name = acc["display_name"]
        phone = acc["phone"]
        email = acc["email"]
        wallet = acc["wallet"] or random.choice(crypto_wallets)
        
        # Determine drug, language, and content
        if role in ["seller", "buyer"]:
            drug = random.choice(DRUG_DICT)
            drug_name = drug["name"]
            lang = random.choice(["english", "hinglish", "hindi", "punjabi"])
            
            # Select template
            templates = SELLER_TEMPLATES if role == "seller" else BUYER_TEMPLATES
            if lang in templates[drug_name] and len(templates[drug_name][lang]) > 0:
                message = random.choice(templates[drug_name][lang])
            else:
                message = random.choice(templates[drug_name]["english"])
                lang = "english"
            
            # Select slang & emoji
            slang = random.choice(drug["slang"])
            emoji = random.choice(drug["emojis"])
            
            risk_score = acc["risk_score"]
            bot_prob = acc["bot_probability"]
            is_bot = acc["is_bot"]
            
            # Adjust risk and reasoning
            confidence = round(random.uniform(0.85, 0.99), 2)
            reasoning = f"Matched drug '{drug_name}' through slang '{slang}' and emoji '{emoji}'. "
            if role == "seller":
                reasoning += "Detected high transaction intent: offered pricing, quantity packages, or drop delivery logistics."
            else:
                reasoning += "Detected purchasing intent: requested stock availability, local coordinates, or pricing queries."
            
            bot_det_reason = "Human patterns. Custom typed messaging with contextual vocabulary."
            if is_bot:
                bot_det_reason = "Likely automated. Message sent instantly following keyword triggers, matching catalog template headers."
                # Append command structures to bot chats
                if platform == "telegram":
                    message = f"/catalog\n{message}\nUse /order to initiate transaction."
                elif platform == "whatsapp":
                    message = f"*Automated Reply:*\n{message}\nReply '1' to view payment details."
            
        else: # Neutral or Spam
            drug_name = None
            slang = None
            emoji = None
            lang = "english"
            message = random.choice(NEUTRAL_TEMPLATES)
            risk_score = random.randint(2, 14)
            bot_prob = random.uniform(0.01, 0.12)
            is_bot = False
            confidence = round(random.uniform(0.01, 0.15), 2)
            reasoning = "No drug identifiers or transaction slangs detected. General conversation placeholder."
            bot_det_reason = "Human user social chatter."
            if role == "spam":
                message = "Earn $500/day from home! Secure link: t.me/fastcash_bot. Free signup. Join now!"
                risk_score = random.randint(10, 20)
                bot_prob = random.uniform(0.85, 0.98)
                is_bot = True
                reasoning = "System advertisement broadcast. Lacks narcotics references."
                bot_det_reason = "Automated spam script. Broad-spectrum channel broadcast."

        # Pick city
        city_ref = random.choice(CITIES)
        # Add random offset for geo mapping
        lat = city_ref["lat"] + random.uniform(-0.08, 0.08)
        lon = city_ref["lon"] + random.uniform(-0.08, 0.08)

        # MD5 Hash for integrity
        hash_input = f"{idx}-{platform}-{timestamp_str}-{message}"
        sha256_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
        evidence_id = f"EVID-2026-{idx+1:04d}"

        conversations.append({
            "id": f"CONV-{idx+1:04d}",
            "platform": platform,
            "channel_or_group": channel_or_group,
            "timestamp": timestamp_str,
            "username": username,
            "display_name": display_name,
            "phone": phone,
            "email": email,
            "telegram_id": f"TGID-{random.randint(100000, 999999)}" if platform == "telegram" else None,
            "instagram_handle": acc["instagram_handle"] if platform == "instagram" else None,
            "whatsapp_number": phone if platform == "whatsapp" else None,
            "drug_mention": drug_name,
            "slang": slang,
            "emoji": emoji,
            "message": message,
            "location": city_ref["name"],
            "latitude": lat,
            "longitude": lon,
            "wallet_address": wallet,
            "risk_score": risk_score,
            "bot_probability": bot_prob,
            "label": role,
            "language": lang,
            "confidence": confidence,
            "reasoning": reasoning,
            "bot_detection_reason": bot_det_reason,
            "evidence_id": evidence_id,
            "hash": sha256_hash
        })

    # Save to json file
    output_data = {
        "drugs": DRUG_DICT,
        "accounts": accounts,
        "conversations": conversations
    }

    output_path = os.path.join("rakshastra_cli", "narcotics_dataset.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Generated dataset with {len(conversations)} conversations and {len(accounts)} accounts saved to {output_path}")

if __name__ == "__main__":
    generate_dataset()
