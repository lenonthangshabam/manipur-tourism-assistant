import hashlib
import io
import html

import pandas as pd
import requests
import streamlit as st
import speech_recognition as sr
SPEECH_RECOGNITION_AVAILABLE = True

st.set_page_config(
    page_title="Manipur Tourism Assistant",
    page_icon="🌏",
    layout="wide",
)

# -----------------------------
# Tourism knowledge base
# -----------------------------
tourism_data = [
    {
        "name": "Loktak Lake",
        "category": "Nature",
        "location": "Bishnupur, Manipur",
        "description": "Loktak Lake is the largest freshwater lake in Northeast India and is famous for its floating phumdis.",
        "keywords": ["lake", "nature", "floating islands", "phumdis", "loktak"],
    },
    {
        "name": "Kangla Fort",
        "category": "History",
        "location": "Imphal, Manipur",
        "description": "Kangla is an important historical and cultural site in the heart of Imphal.",
        "keywords": ["fort", "history", "culture", "imphal", "heritage", "kangla"],
    },
    {
        "name": "Keibul Lamjao National Park",
        "category": "Wildlife",
        "location": "Bishnupur, Manipur",
        "description": "Keibul Lamjao National Park is known as a floating national park and is associated with the Sangai deer.",
        "keywords": ["wildlife", "national park", "sangai", "nature", "animal", "keibul"],
    },
    {
        "name": "Ima Keithel",
        "category": "Market",
        "location": "Imphal, Manipur",
        "description": "Ima Keithel is a historic market in Imphal traditionally operated by women traders.",
        "keywords": ["market", "shopping", "culture", "handicrafts", "ima keithel"],
    },
    {
        "name": "Shree Govindajee Temple",
        "category": "Culture",
        "location": "Imphal, Manipur",
        "description": "A historic Vaishnavite temple and an important cultural site in Imphal.",
        "keywords": ["temple", "culture", "religion", "heritage", "govindajee"],
    },
    {
        "name": "Andro",
        "category": "Culture",
        "location": "Imphal East, Manipur",
        "description": "Andro is known for traditional culture, heritage and local crafts.",
        "keywords": ["culture", "village", "crafts", "heritage", "tradition", "andro"],
    },
    {
        "name": "Khongjom War Memorial",
        "category": "History",
        "location": "Thoubal, Manipur",
        "description": "A historical memorial associated with the Anglo-Manipur War of 1891.",
        "keywords": ["history", "war", "memorial", "heritage", "khongjom"],
    },
    {
        "name": "Singda Tourist Village",
        "category": "Nature",
        "location": "Imphal West, Manipur",
        "description": "A scenic destination known for hills, greenery and views of the surrounding landscape.",
        "keywords": ["nature", "hills", "scenery", "tourist", "singda"],
    },
    {
        "name": "Manipuri Cuisine",
        "category": "Food",
        "location": "Manipur",
        "description": "Manipuri cuisine features traditional dishes and locally used ingredients.",
        "keywords": ["food", "cuisine", "local food", "traditional food", "eat"],
    },
    {
        "name": "Pukhlein",
        "category": "Food",
        "location": "Manipur",
        "description": "A traditional sweet snack made using rice-based ingredients.",
        "keywords": ["food", "snack", "sweet", "local food", "pukhlein"],
    },
]

tourism_df = pd.DataFrame(tourism_data)

food_data = [
    {"name": "Eromba", "description": "A traditional Manipuri dish commonly prepared with vegetables, fermented fish and chilli."},
    {"name": "Singju", "description": "A traditional Manipuri salad made with vegetables, herbs and other local ingredients."},
    {"name": "Chamthong", "description": "A traditional vegetable preparation made with seasonal vegetables and herbs."},
    {"name": "Kangshoi", "description": "A traditional Manipuri vegetable preparation made with seasonal ingredients."},
    {"name": "Paknam", "description": "A traditional Manipuri preparation made using local ingredients and cooked in a wrapped form."},
]

etiquette_data = [
    ("Cultural Sites", "Dress and behave respectfully when visiting temples, historical sites and other cultural places."),
    ("Photography", "Ask permission before photographing local people, ceremonies or culturally sensitive activities."),
    ("Environment", "Avoid littering and help protect lakes, forests, wildlife areas and other natural attractions."),
    ("Local Communities", "Be polite and respectful toward local residents and their customs."),
    ("Wildlife", "Do not disturb, feed or approach wildlife in protected areas."),
]

travel_data = [
    ("Hotels & Guesthouses", "Visitors can find accommodation in and around Imphal with different price and comfort levels."),
    ("Homestays", "Homestays can provide a more local and community-oriented experience."),
    ("Local Buses", "Local and intercity buses can be used to travel between different areas of Manipur."),
    ("Taxis", "Taxis and hired vehicles can be useful for travelling between tourist destinations."),
    ("Auto Rickshaws", "Auto rickshaws can be useful for shorter journeys in urban areas."),
]

# -----------------------------
# Language handling
# -----------------------------

def detect_language(text: str) -> str:
    text = text.strip()
    if not text:
        return "English"
    if any("\uABC0" <= c <= "\uABFF" for c in text):
        return "Manipuri (Meitei)"
    if any("\u0900" <= c <= "\u097F" for c in text):
        return "Hindi"
    return "English"


def normalize_meitei_input(text: str) -> str:
    """Map a few common Meitei Mayek tourism terms to English intents.

    This is intentionally small and domain-specific. It improves recognition
    for the prototype without claiming full free-form Meitei NLP.
    """
    replacements = {
        "ꯂꯣꯀꯇꯛ": " Loktak ",
        "ꯀꯥꯡꯂꯥ": " Kangla ",
        "ꯏꯃꯥ ꯀꯩꯊꯦꯜ": " Ima Keithel ",
        "ꯁꯥꯡꯒꯥꯏ": " Sangai wildlife ",
        "ꯅꯥꯆꯔꯦ": " nature ",
        "ꯋꯥꯏꯂꯠꯂꯤꯐ": " wildlife ",
        "ꯐꯨꯗ": " food ",
        "ꯍꯤꯁꯇꯣꯔꯤ": " history ",
        "ꯀꯜꯆꯔ": " culture ",
        "ꯇꯔꯤꯐ": " tourist ",
    }
    normalized = text
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    return normalized


# Curated core Meitei strings. These are sourced/checked against public
# Manipuri phrase references and are used as reliable fallbacks for the demo.
MEITEI_CORE = {
    "hello": "ꯈꯨꯔꯨꯝꯖꯔꯤ!",
    "thanks": "ꯊꯒꯥꯆꯔꯤ!",
    "welcome": "ꯂꯣꯡꯁꯤꯟꯕꯤꯔꯛꯁꯤ",
    "help": "ꯅꯍꯛ ꯑꯩ ꯄꯨꯝꯅꯥꯃꯛ ꯄꯤꯔꯌꯨ?",
}


def google_translate_to_meitei(text: str) -> str | None:
    """Best-effort text translation to Meitei/Manipuri.

    Uses an online translation endpoint. If it is unavailable, the app falls
    back to curated tourism responses, so the UI still works.
    """
    if not text.strip():
        return text

    try:
        # Google Translate currently lists Meiteilon (Manipuri) as a supported
        # language. The endpoint below is intentionally treated as best-effort.
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": "mni",
            "dt": "t",
            "q": text,
        }
        response = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params=params,
            timeout=8,
        )
        response.raise_for_status()
        payload = response.json()
        translated = "".join(part[0] for part in payload[0] if part and part[0])
        return translated.strip() or None
    except Exception:
        return None


def meitei_fallback(query: str, english_response: str) -> str:
    """Fallback response for core tourism flows when online translation fails."""
    q = normalize_meitei_input(query).lower()

    if any(x in q for x in ["hello", "hi", "hey"]):
        return f"{MEITEI_CORE['hello']}\n\nꯃꯅꯤꯄꯨꯔ ꯇꯨꯔꯤꯖꯝ ꯑꯁꯤꯅ ꯅꯥꯍꯥꯛꯄꯨ ꯄꯥꯡꯕꯤꯌꯦꯛ꯫"

    if any(x in q for x in ["thank you", "thanks"]):
        return MEITEI_CORE["thanks"]

    if "loktak" in q:
        return (
            "📍 Loktak Lake\n"
            "📌 ꯕꯤꯁ꯭ꯅꯨꯄꯨꯔ, ꯃꯅꯤꯄꯨꯔ\n\n"
            "ꯂꯣꯀꯇꯛ ꯂꯥꯏꯛꯇꯥ ꯐꯨꯝꯗꯤꯁꯤꯡ ꯂꯩꯕꯗꯨꯅ ꯃꯁꯤ ꯀꯅꯥꯅꯥ ꯁꯤꯡꯖꯤꯟꯅꯕꯥ ꯁꯦꯟꯅꯥ ꯃꯄꯨꯡ ꯂꯩꯕꯥ ꯂꯩꯅꯥ ꯂꯥꯏꯕꯥ ꯑꯃꯅꯤ꯫"
        )

    if "kangla" in q:
        return (
            "📍 Kangla Fort\n"
            "📌 ꯏꯝꯐꯥꯜ, ꯃꯅꯤꯄꯨꯔ\n\n"
            "ꯀꯥꯡꯂꯥ ꯑꯁꯤ ꯏꯝꯐꯥꯜꯒꯤ ꯃꯔꯛꯇ ꯂꯩꯕꯥ ꯑꯃ ꯍꯤꯁꯇꯣꯔꯤꯛ ꯂꯩꯕꯥ ꯑꯃꯁꯨꯡ ꯀꯜꯆꯔꯒꯤ ꯐꯝꯃꯅꯤ꯫"
        )

    if "ima keithel" in q:
        return (
            "📍 Ima Keithel\n"
            "📌 ꯏꯝꯐꯥꯜ, ꯃꯅꯤꯄꯨꯔ\n\n"
            "ꯏꯃꯥ ꯀꯩꯊꯦꯜ ꯑꯁꯤ ꯏꯝꯐꯥꯜꯗ ꯂꯩꯕꯥ ꯍꯤꯁꯇꯣꯔꯤꯛ ꯃꯥꯔꯀꯦꯠ ꯑꯃꯅꯤ꯫"
        )

    if "nature" in q:
        return (
            "🌿 ꯃꯅꯤꯄꯨꯔꯗ ꯅꯥꯆꯔꯦ ꯂꯩꯕꯥ ꯐꯝꯁꯤꯡ:\n\n"
            "📍 Loktak Lake\n"
            "📍 Singda Tourist Village\n"
            "📍 Keibul Lamjao National Park"
        )

    if "wildlife" in q or "sangai" in q:
        return (
            "🦌 ꯋꯥꯏꯂꯠꯂꯤꯐ ꯒꯤ ꯐꯝ:\n\n"
            "📍 Keibul Lamjao National Park\n\n"
            "ꯁꯥꯡꯒꯥꯏ ꯑꯃꯁꯨꯡ ꯑꯇꯣꯞꯄ ꯑꯅꯤꯃꯜꯁꯤꯡꯕꯨ ꯅꯥꯀꯥꯄꯤ ꯑꯃꯁꯨꯡ ꯆꯥꯟꯅ ꯌꯥꯕꯥ ꯂꯣꯏꯁꯤꯟꯗꯨꯅ ꯌꯥꯡꯕꯤꯌꯨ꯫"
        )

    if "food" in q:
        return (
            "🍲 ꯃꯅꯤꯄꯨꯔꯒꯤ ꯃꯁꯤꯡ ꯁꯣꯏꯕꯥ ꯆꯥꯛ:\n\n"
            "📍 Eromba\n📍 Singju\n📍 Chamthong\n📍 Kangshoi\n📍 Paknam"
        )

    if "history" in q:
        return (
            "🏛️ ꯃꯅꯤꯄꯨꯔꯒꯤ ꯍꯤꯁꯇꯣꯔꯤꯒꯤ ꯐꯝ:\n\n"
            "📍 Kangla Fort\n📍 Khongjom War Memorial"
        )

    if "culture" in q:
        return (
            "🪷 ꯀꯜꯆꯔꯒꯤ ꯐꯝ:\n\n"
            "📍 Shree Govindajee Temple\n📍 Andro\n📍 Ima Keithel"
        )

    if is_trip_query(query):
        days = extract_days(query)
        if days == 2:
            return (
                "🗺️ ꯑꯅꯤ ꯅꯨꯃꯤꯠꯀꯤ ꯃꯅꯤꯄꯨꯔ ꯇ꯭ꯔꯤꯞ ꯄ꯭ꯂꯥꯟ:\n\n"
                "📅 Day 1 — Kangla Fort + Ima Keithel\n"
                "📅 Day 2 — Loktak Lake + Keibul Lamjao National Park"
            )
        if days == 3:
            return (
                "🗺️ ꯇ꯭ꯔꯤ ꯅꯨꯃꯤꯠꯀꯤ ꯃꯅꯤꯄꯨꯔ ꯇ꯭ꯔꯤꯞ ꯄ꯭ꯂꯥꯟ:\n\n"
                "📅 Day 1 — Kangla Fort + Ima Keithel\n"
                "📅 Day 2 — Loktak Lake + Keibul Lamjao National Park\n"
                "📅 Day 3 — Andro + Singda Tourist Village"
            )

    if is_budget_query(query):
        days = extract_days(query)
        if days:
            total = 2000 * days
            return (
                f"💰 {days} ꯅꯨꯃꯤꯠꯀꯤ ꯑꯦꯁꯇꯤꯃꯦꯠ ꯕꯖꯦꯠ\n\n"
                f"🏨 Accommodation: ₹{1000 * days}\n"
                f"🍲 Food: ₹{500 * days}\n"
                f"🚌 Transport: ₹{500 * days}\n"
                f"💵 Total: ₹{total}\n\n"
                "⚠️ ꯃꯁꯤ ꯁꯥꯝꯄꯜ ꯑꯦꯁꯇꯤꯃꯦꯠꯅꯤ; ꯂꯦꯏꯕꯥ ꯃꯤꯇꯦꯡ ꯌꯥꯑꯣ꯫"
            )

    # If we have no reliable domain-specific fallback, show the English answer
    # alongside an honest note instead of inventing Meitei text.
    return (
        "🟢 ꯃꯁꯤ ꯃꯔꯨꯑꯣꯏꯕꯥ ꯄ꯭ꯔꯣꯇꯣꯇꯥꯏꯞ ꯑꯃꯅꯤ.\n\n"
        "⚠️ ꯃꯁꯤꯒꯤ ꯃꯔꯝꯗ ꯃꯩꯇꯩꯂꯣꯟ ꯇ꯭ꯔꯥꯟꯁꯂꯦꯁꯟ ꯁꯔꯕꯤꯁ ꯂꯥꯏꯐꯇꯕ ꯂꯩꯔꯕꯗꯤ, ꯏꯉ꯭ꯂꯤꯁ ꯑꯦꯟꯁꯔ ꯑꯁꯤ ꯌꯦꯡꯕꯤꯌꯨ꯫\n\n"
        + english_response
    )

# -----------------------------
# Search + response logic
# -----------------------------

def search_places(query: str):
    q = normalize_meitei_input(query).lower().strip()
    results = []
    for place in tourism_data:
        searchable = " ".join([
            place["name"].lower(),
            place["category"].lower(),
            place["location"].lower(),
            place["description"].lower(),
            " ".join(place["keywords"]).lower(),
        ])
        score = sum(1 for word in q.split() if word and word in searchable)
        if score:
            results.append((score, place))
    results.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in results]


def category_results(category: str):
    return [p for p in tourism_data if p["category"].lower() == category.lower()]


def recommendations(query: str):
    q = normalize_meitei_input(query).lower()
    category = None
    if any(w in q for w in ["nature", "lake", "scenery", "hills", "greenery"]):
        category = "Nature"
    elif any(w in q for w in ["history", "historical", "fort", "heritage"]):
        category = "History"
    elif any(w in q for w in ["wildlife", "animal", "sangai"]):
        category = "Wildlife"
    elif any(w in q for w in ["culture", "cultural", "tradition", "traditional"]):
        category = "Culture"

    if not category:
        return None
    places = category_results(category)
    if not places:
        return None
    out = [f"🎯 Places matching your interest in {category.lower()}:", ""]
    for p in places[:4]:
        out += [f"📍 {p['name']}", f"📌 {p['location']}", p["description"], ""]
    return "\n".join(out)


def food_response(query: str):
    q = normalize_meitei_input(query).lower()
    if not any(w in q for w in ["food", "eat", "dish", "cuisine", "restaurant"]):
        return None
    for item in food_data:
        if item["name"].lower() in q:
            return f"🍲 {item['name']}\n\n{item['description']}"
    out = ["🍲 Traditional Manipuri Food", ""]
    for item in food_data:
        out += [f"📍 {item['name']}", item["description"], ""]
    return "\n".join(out)


def etiquette_response(query: str):
    q = normalize_meitei_input(query).lower()
    if not any(w in q for w in ["etiquette", "custom", "respect", "behavior", "behaviour", "rules"]):
        return None
    out = ["🪷 Local Etiquette & Cultural Tips", ""]
    for topic, advice in etiquette_data:
        out += [f"📌 {topic}", advice, ""]
    return "\n".join(out)


def travel_response(query: str):
    q = normalize_meitei_input(query).lower()
    if not any(w in q for w in ["hotel", "stay", "accommodation", "homestay", "transport", "bus", "taxi", "cab", "auto"]):
        return None
    out = ["🧳 Accommodation & Transport", ""]
    for name, desc in travel_data:
        out += [f"📍 {name}", desc, ""]
    return "\n".join(out)


def emergency_response(query: str):
    q = normalize_meitei_input(query).lower()
    if not any(w in q for w in ["emergency", "police", "ambulance", "hospital", "fire", "accident"]):
        return None
    return "🚨 For emergencies, contact the appropriate official local emergency service directly."


def directions_response(query: str):
    q = normalize_meitei_input(query).lower()
    if not any(w in q for w in ["where is", "how to reach", "how do i reach", "directions", "route", "location", "get to"]):
        return None
    for p in tourism_data:
        if p["name"].lower() in q:
            return f"🗺️ Directions to {p['name']}\n\n📍 Location: {p['location']}\n\nUse a current maps app to get the live route from your starting point."
    return "🗺️ Tell me the destination name and I can identify its location from the tourism database."


def extract_days(query: str):
    q = query.lower()
    if "1 day" in q or "one day" in q or "1-day" in q or "one-day" in q:
        return 1
    if "2 day" in q or "two day" in q or "2-day" in q or "two-day" in q:
        return 2
    if "3 day" in q or "three day" in q or "3-day" in q or "three-day" in q:
        return 3
    return None


def is_budget_query(query: str):
    q = normalize_meitei_input(query).lower()
    budget_words = [
        "budget", "cost", "costs", "price", "prices", "money",
        "expense", "expenses", "spend", "spending", "how much",
        "cheap", "affordable", "estimated cost", "travel cost"
    ]
    return any(word in q for word in budget_words)


def is_trip_query(query: str):
    q = normalize_meitei_input(query).lower()
    trip_words = [
        "trip", "itinerary", "visit", "visits", "places to visit",
        "what can i visit", "what should i visit", "where can i go",
        "what can i see", "what should i see", "sightseeing",
        "tour", "plan a trip", "travel plan", "days in manipur"
    ]
    return any(word in q for word in trip_words)


def trip_planner(query: str):
    if not is_trip_query(query):
        return None
    days = extract_days(query)
    if not days:
        return None
    itinerary = {
        1: [("Morning", "Kangla Fort"), ("Afternoon", "Ima Keithel"), ("Evening", "Loktak Lake")],
        2: [("Day 1", "Kangla Fort + Ima Keithel"), ("Day 2", "Loktak Lake + Keibul Lamjao National Park")],
        3: [("Day 1", "Kangla Fort + Ima Keithel"), ("Day 2", "Loktak Lake + Keibul Lamjao National Park"), ("Day 3", "Andro + Singda Tourist Village")],
    }
    out = [f"🗺️ {days}-Day Manipur Trip Plan", ""]
    for time, places in itinerary[days]:
        out += [f"📅 {time}", f"📍 {places}", ""]
    out.append("💡 Tip: Travel times and site conditions can vary, so check current local information before travelling.")
    return "\n".join(out)


def budget_planner(query: str):
    if not is_budget_query(query):
        return None
    days = extract_days(query)
    if not days:
        return None
    accommodation, food, transport = 1000, 500, 500
    total = (accommodation + food + transport) * days
    return (
        f"💰 Estimated {days}-Day Trip Budget\n\n"
        f"🏨 Accommodation: ₹{accommodation * days}\n"
        f"🍲 Food: ₹{food * days}\n"
        f"🚌 Local Transport: ₹{transport * days}\n"
        f"──────────────────\n"
        f"💵 Estimated Total: ₹{total}\n\n"
        f"⚠️ Sample estimate only. Actual costs vary by accommodation, transport and activities."
    )


def base_chatbot(query: str):
    q = normalize_meitei_input(query).lower().strip()

    if any(x in q for x in ["hello", "hi", "hey", "namaste"]):
        return (
            "👋 Hello! I'm your Manipur Tourism Assistant.\n\n"
            "I can help with tourist places, food, culture, directions, emergencies, trip planning and budgets."
        )
    if any(x in q for x in ["thank you", "thanks"]):
        return "😊 You're welcome! Enjoy exploring Manipur! 🌏"
    if any(x in q for x in ["bye", "goodbye", "see you"]):
        return "👋 Goodbye! Have a wonderful trip around Manipur! 🌏"

    for p in tourism_data:
        if p["name"].lower() in q:
            return (
                "🌏 Here's what I found:\n\n"
                f"📍 {p['name']}\n"
                f"Category: {p['category']}\n"
                f"Location: {p['location']}\n"
                f"{p['description']}"
            )

    if is_budget_query(q):
        result = budget_planner(q)
        if result:
            return result

    if is_trip_query(q):
        result = trip_planner(q)
        if result:
            return result

    for handler in [
        emergency_response,
        etiquette_response,
        food_response,
        travel_response,
        directions_response,
        recommendations,
    ]:
        result = handler(q)
        if result:
            return result

    results = search_places(q)
    if results:
        out = ["🌏 Here are some places you can explore:", ""]
        for p in results[:4]:
            out += [f"📍 {p['name']}", f"📌 {p['location']}", p["description"], ""]
        return "\n".join(out)

    return (
        "🤔 I couldn't find that in my current Manipur tourism knowledge base.\n\n"
        "Try asking about Loktak Lake, Kangla Fort, nature, history, wildlife, food, culture, directions, a trip plan or a budget."
    )


def answer(query: str, response_language: str = "Auto-detect"):
    detected = detect_language(query)
    language = detected if response_language == "Auto-detect" else response_language

    english_response = base_chatbot(query)

    if language == "English":
        return language, english_response

    if language == "Hindi":
        replacements = {
            "Category:": "श्रेणी:",
            "Location:": "स्थान:",
            "Nature": "प्रकृति",
            "History": "इतिहास",
            "Wildlife": "वन्यजीव",
            "Market": "बाज़ार",
            "Culture": "संस्कृति",
            "Food": "भोजन",
            "Here's what I found:": "मुझे यह जानकारी मिली:",
        }
        hindi = english_response
        for source, target in replacements.items():
            hindi = hindi.replace(source, target)
        return language, hindi

    # Manipuri / Meitei
    translated = google_translate_to_meitei(english_response)
    if translated:
        return "Manipuri (Meitei)", translated
    return "Manipuri (Meitei)", meitei_fallback(query, english_response)

# -----------------------------
# Voice transcription
# -----------------------------
def transcribe_audio(uploaded_audio, language: str):
    recognizer = sr.Recognizer()

    try:
        # Streamlit st.audio_input returns audio/wav by default.
        with sr.AudioFile(uploaded_audio) as source:
            audio = recognizer.record(source)

        speech_code = {
            "English": "en-IN",
            "Hindi": "hi-IN",
        }.get(language, "en-IN")

        text = recognizer.recognize_google(
            audio,
            language=speech_code
        )

        return text, None

    except sr.UnknownValueError:
        return None, (
            "I couldn't understand the recording. "
            "Please speak clearly and try again."
        )

    except sr.RequestError:
        return None, (
            "The online speech-recognition service is unavailable right now. "
            "Please try again later."
        )

    except Exception as exc:
        return None, f"Voice processing error: {type(exc).__name__}: {exc}"


# -----------------------------
# UI
# -----------------------------
st.markdown(
    """
    <style>
    .hero {
        padding: 1.6rem 1.7rem;
        border-radius: 20px;
        background: linear-gradient(135deg, #0b2d4d 0%, #145a7a 55%, #1d7a8c 100%);
        border: 1px solid #0a2742;
        margin-bottom: 1.2rem;
        box-shadow: 0 8px 24px rgba(8, 42, 67, 0.18);
    }
    .hero h1 {
        color: #ffffff !important;
        font-size: 2.35rem !important;
        font-weight: 800 !important;
        margin: 0 0 0.45rem 0 !important;
        letter-spacing: -0.02em;
    }
    .hero p {
        color: #eaf7ff !important;
        font-size: 1.05rem;
        line-height: 1.55;
        margin: 0 0 0.8rem 0;
    }
    .tag {
        display: inline-block;
        padding: 6px 11px;
        margin: 3px 4px 0 0;
        border-radius: 999px;
        background: rgba(255,255,255,0.14);
        color: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.32);
        font-size: 0.88rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>🌏 Manipur Tourism Assistant</h1>
      <p>Your AI travel companion for places, food, culture, directions, trip plans and budgets.</p>
      <span class="tag">📍 Manipur</span>
      <span class="tag">🌐 English + Hindi + Manipuri (Meitei)</span>
      <span class="tag">🎙️ Browser voice input</span>
      <span class="tag">🗺️ Trip planner</span>
      <span class="tag">💰 Budget planner</span>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("🧭 Explore")
    st.write("Try common tourism questions.")
    response_language = st.selectbox(
        "Response language",
        ["Auto-detect", "English", "Hindi", "Manipuri (Meitei)"],
        index=0,
    )

    prompts = [
        "Tell me about Loktak Lake",
        "I love nature. What should I visit?",
        "Show me wildlife places",
        "What food should I try?",
        "Plan a 2 day trip in Manipur",
        "What is the budget for a 3 day trip?",
        "What should I know about local etiquette?",
        "ꯂꯣꯀꯇꯛ ꯂꯥꯏꯕꯒꯤ ꯃꯔꯝꯗ ꯍꯥꯌꯕꯤꯌꯨ",
    ]
    for prompt in prompts:
        if st.button(prompt, use_container_width=True):
            st.session_state.pending_prompt = prompt

    st.divider()
    st.caption("Prototype note")
    st.caption(
        "Manipuri text mode uses an online translation layer with tourism-specific fallbacks. "
        "Voice input is currently English/Hindi only."
    )

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "👋 Welcome! Ask me about places, food, culture, directions, trip plans or budgets in Manipur.",
        }
    ]

if "pending_prompt" in st.session_state:
    prompt = st.session_state.pop("pending_prompt")
    language, reply = answer(prompt, response_language)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": f"🌐 {language}\n\n{reply}"})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

st.subheader("💬 Ask by text")
text_prompt = st.chat_input("Ask about tourism in Manipur…")
if text_prompt:
    language, reply = answer(text_prompt, response_language)
    st.session_state.messages.append({"role": "user", "content": text_prompt})
    st.session_state.messages.append({"role": "assistant", "content": f"🌐 {language}\n\n{reply}"})
    st.rerun()

st.subheader("🎙️ Ask by voice")
st.caption("Voice input currently supports English and Hindi. Text input supports Manipuri (Meitei).")
voice_language = st.selectbox(
    "Spoken language",
    ["English", "Hindi"],
    key="voice_language",
)
audio = st.audio_input("🎙️ Record your question", sample_rate=16000, key="tourism_voice")

if audio:
    audio_hash = hashlib.sha256(audio.getvalue()).hexdigest()
    if st.session_state.get("processed_voice_hash") != audio_hash:
        with st.spinner("🎧 Understanding your question…"):
            spoken_text, voice_error = transcribe_audio(audio, voice_language)
        st.session_state.processed_voice_hash = audio_hash

        if spoken_text:
            language, reply = answer(spoken_text, response_language)
            st.session_state.messages.append({"role": "user", "content": f"🎙️ {spoken_text}"})
            st.session_state.messages.append({"role": "assistant", "content": f"🌐 {language}\n\n{reply}"})
            st.success(f"Heard: {spoken_text}")
            st.rerun()
        else:
            st.error(voice_error or "I couldn't understand the recording. Please try again.")
