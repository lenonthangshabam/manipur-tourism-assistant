import io
import re

import pandas as pd
import streamlit as st
import speech_recognition as sr

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
        "keywords": ["lake", "nature", "floating islands", "phumdis"],
    },
    {
        "name": "Kangla Fort",
        "category": "History",
        "location": "Imphal, Manipur",
        "description": "Kangla is an important historical and cultural site in the heart of Imphal.",
        "keywords": ["fort", "history", "culture", "imphal", "heritage"],
    },
    {
        "name": "Keibul Lamjao National Park",
        "category": "Wildlife",
        "location": "Bishnupur, Manipur",
        "description": "Keibul Lamjao National Park is known as a floating national park and is associated with the Sangai deer.",
        "keywords": ["wildlife", "national park", "sangai", "nature", "animal"],
    },
    {
        "name": "Ima Keithel",
        "category": "Market",
        "location": "Imphal, Manipur",
        "description": "Ima Keithel is a historic market in Imphal traditionally operated by women traders.",
        "keywords": ["market", "shopping", "culture", "handicrafts"],
    },
    {
        "name": "Shree Govindajee Temple",
        "category": "Culture",
        "location": "Imphal, Manipur",
        "description": "A historic Vaishnavite temple and an important cultural site in Imphal.",
        "keywords": ["temple", "culture", "religion", "heritage"],
    },
    {
        "name": "Andro",
        "category": "Culture",
        "location": "Imphal East, Manipur",
        "description": "Andro is known for traditional culture, heritage and local crafts.",
        "keywords": ["culture", "village", "crafts", "heritage", "tradition"],
    },
    {
        "name": "Khongjom War Memorial",
        "category": "History",
        "location": "Thoubal, Manipur",
        "description": "A historical memorial associated with the Anglo-Manipur War of 1891.",
        "keywords": ["history", "war", "memorial", "heritage"],
    },
    {
        "name": "Singda Tourist Village",
        "category": "Nature",
        "location": "Imphal West, Manipur",
        "description": "A scenic destination known for hills, greenery and views of the surrounding landscape.",
        "keywords": ["nature", "hills", "scenery", "tourist"],
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
        "keywords": ["food", "snack", "sweet", "local food"],
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

emergency_data = [
    ("Police", "For immediate police assistance during an emergency."),
    ("Ambulance", "For urgent medical transportation and emergency assistance."),
    ("Fire & Rescue", "For fire-related emergencies and rescue assistance."),
]

# -----------------------------
# Language detection
# -----------------------------
def detect_language(text: str) -> str:
    text = text.strip()
    if not text:
        return "English"
    if any("\u0900" <= c <= "\u097F" for c in text):
        return "Hindi"
    if any("\uABC0" <= c <= "\uABFF" for c in text):
        return "Meitei"
    return "English"


def speech_language_code(language: str) -> str:
    return {"English": "en-IN", "Hindi": "hi-IN", "Meitei": "en-IN"}.get(language, "en-IN")

# -----------------------------
# Search + responses
# -----------------------------
def search_places(query: str):
    query = query.lower().strip()
    results = []
    for place in tourism_data:
        searchable = " ".join([
            place["name"].lower(),
            place["category"].lower(),
            place["location"].lower(),
            place["description"].lower(),
            " ".join(place["keywords"]).lower(),
        ])
        score = sum(1 for word in query.split() if word and word in searchable)
        if score:
            results.append((score, place))
    results.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in results]


def category_results(category: str):
    return [p for p in tourism_data if p["category"].lower() == category.lower()]


def recommendations(query: str):
    q = query.lower()
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
        out += [f"📍 {p['name']}", f"📌 {p['location']}", f"{p['description']}", ""]
    return "\n".join(out)


def food_response(query: str):
    q = query.lower()
    if not any(w in q for w in ["food", "eat", "dish", "cuisine", "restaurant", "খाना", "भोजन"]):
        return None
    for item in food_data:
        if item["name"].lower() in q:
            return f"🍲 {item['name']}\n\n{item['description']}"
    out = ["🍲 Traditional Manipuri Food", ""]
    for item in food_data:
        out += [f"📍 {item['name']}", item["description"], ""]
    return "\n".join(out)


def etiquette_response(query: str):
    q = query.lower()
    if not any(w in q for w in ["etiquette", "custom", "respect", "behavior", "behaviour", "culture", "rules"]):
        return None
    out = ["🪷 Local Etiquette & Cultural Tips", ""]
    for topic, advice in etiquette_data:
        out += [f"📌 {topic}", advice, ""]
    return "\n".join(out)


def travel_response(query: str):
    q = query.lower()
    if not any(w in q for w in ["hotel", "stay", "accommodation", "homestay", "transport", "bus", "taxi", "cab", "auto"]):
        return None
    out = ["🧳 Accommodation & Transport", ""]
    for name, desc in travel_data:
        out += [f"📍 {name}", desc, ""]
    return "\n".join(out)


def emergency_response(query: str):
    q = query.lower()
    if not any(w in q for w in ["emergency", "police", "ambulance", "hospital", "fire", "accident"]):
        return None
    out = ["🚨 Emergency Information", "", "For an immediate emergency, contact the appropriate official local emergency service directly.", ""]
    for name, desc in emergency_data:
        out += [f"📞 {name}", desc, ""]
    out.append("⚠️ This prototype does not display emergency phone numbers because live official numbers should be verified before publication.")
    return "\n".join(out)


def directions_response(query: str):
    q = query.lower()
    if not any(w in q for w in ["where is", "how to reach", "how do i reach", "directions", "route", "location", "get to"]):
        return None
    for p in tourism_data:
        if p["name"].lower() in q:
            return f"🗺️ Directions to {p['name']}\n\n📍 Location: {p['location']}\n\nUse a current maps app to get the live route from your starting point."
    return "🗺️ Tell me the destination name and I can identify its location from the tourism database."


def trip_planner(query: str):
    q = query.lower()
    if "1 day" in q or "one day" in q:
        days = 1
    elif "2 day" in q or "two day" in q:
        days = 2
    elif "3 day" in q or "three day" in q:
        days = 3
    else:
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
    q = query.lower()
    if "1 day" in q or "one day" in q:
        days = 1
    elif "2 day" in q or "two day" in q:
        days = 2
    elif "3 day" in q or "three day" in q:
        days = 3
    else:
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


def translate_labels(text: str, language: str):
    if language != "Hindi":
        return text
    replacements = {
        "Category:": "श्रेणी:",
        "Location:": "स्थान:",
        "Nature": "प्रकृति",
        "History": "इतिहास",
        "Wildlife": "वन्यजीव",
        "Market": "बाज़ार",
        "Culture": "संस्कृति",
        "Food": "भोजन",
        "Places matching your interest in nature:": "आपकी प्रकृति संबंधी रुचि से मेल खाने वाले स्थान:",
        "Places matching your interest in history:": "आपकी इतिहास संबंधी रुचि से मेल खाने वाले स्थान:",
        "Places matching your interest in wildlife:": "आपकी वन्यजीव संबंधी रुचि से मेल खाने वाले स्थान:",
        "Places matching your interest in culture:": "आपकी संस्कृति संबंधी रुचि से मेल खाने वाले स्थान:",
        "Here's what I found:": "मुझे यह जानकारी मिली:",
    }
    for a, b in replacements.items():
        text = text.replace(a, b)
    return text


def base_chatbot(query: str):
    q = query.lower().strip()
    if any(x in q for x in ["hello", "hi", "hey", "namaste", "नमस्ते"]):
        return (
            "👋 Hello! I'm your Manipur Tourism Assistant.\n\n"
            "I can help with tourist places, food, culture, directions, emergencies, trip planning and budgets."
        )
    if any(x in q for x in ["thank you", "thanks", "धन्यवाद"]):
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

    for handler in [
        emergency_response,
        etiquette_response,
        food_response,
        travel_response,
        directions_response,
        budget_planner,
        trip_planner,
        recommendations,
    ]:
        result = handler(query)
        if result:
            return result

    results = search_places(query)
    if results:
        out = ["🌏 Here are some places you can explore:", ""]
        for p in results[:4]:
            out += [f"📍 {p['name']}", f"📌 {p['location']}", p['description'], ""]
        return "\n".join(out)

    return (
        "🤔 I couldn't find that in my current Manipur tourism knowledge base.\n\n"
        "Try asking about Loktak Lake, Kangla Fort, nature, history, wildlife, food, culture, directions, a trip plan or a budget."
    )


def answer(query: str):
    language = detect_language(query)
    response = base_chatbot(query)
    response = translate_labels(response, language)
    return language, response

# -----------------------------
# Voice transcription
# -----------------------------
def transcribe_audio(uploaded_audio, language: str):
    recognizer = sr.Recognizer()
    try:
        audio_bytes = uploaded_audio.getvalue()
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio, language=speech_language_code(language))
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return ""
    except Exception:
        return ""

# -----------------------------
# UI
# -----------------------------
st.markdown(
    """
    <style>
    .hero {
        padding: 1.1rem 1.3rem;
        border-radius: 18px;
        background: linear-gradient(135deg, #eef6ff, #f6fbff);
        border: 1px solid #d8e8f7;
        margin-bottom: 1rem;
    }
    .tag {display:inline-block; padding:4px 10px; margin:3px; border-radius:999px; background:#ffffff; border:1px solid #d8e8f7; font-size:0.9rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>🌏 Manipur Tourism Assistant</h1>
      <p>Your prototype AI travel companion for places, food, culture, directions, trip plans and budgets.</p>
      <span class="tag">📍 Manipur</span>
      <span class="tag">🌐 English + Hindi + Meitei detection</span>
      <span class="tag">🎙️ Browser voice input</span>
      <span class="tag">🗺️ Trip planner</span>
      <span class="tag">💰 Budget planner</span>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("🧭 Explore")
    st.write("Use the buttons to try common questions.")
    prompts = [
        "Tell me about Loktak Lake",
        "I love nature. What should I visit?",
        "Show me wildlife places",
        "What food should I try?",
        "Plan a 2 day trip in Manipur",
        "What is the budget for a 3 day trip?",
        "What should I know about local etiquette?",
    ]
    for p in prompts:
        if st.button(p, use_container_width=True):
            st.session_state.pending_prompt = p

    st.divider()
    st.caption("Prototype note")
    st.caption("Emergency phone numbers and live prices are intentionally not hard-coded. Verify official/current information before real-world use.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "👋 Welcome! Ask me about places, food, culture, directions, trip plans or budgets in Manipur.",
        }
    ]

if "pending_prompt" in st.session_state:
    prompt = st.session_state.pop("pending_prompt")
    language, reply = answer(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": f"🌐 {language}\n\n{reply}"})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

st.subheader("💬 Ask by text")
text_prompt = st.chat_input("Ask about tourism in Manipur…")
if text_prompt:
    language, reply = answer(text_prompt)
    st.session_state.messages.append({"role": "user", "content": text_prompt})
    st.session_state.messages.append({"role": "assistant", "content": f"🌐 {language}\n\n{reply}"})
    st.rerun()

st.subheader("🎙️ Ask by voice")
audio = st.audio_input("Record your question")
if audio:
    language_hint = st.radio(
        "Voice language",
        ["English", "Hindi"],
        horizontal=True,
        key="voice_language",
    )
    if st.button("Transcribe & Ask", type="primary"):
        spoken_text = transcribe_audio(audio, language_hint)
        if spoken_text:
            language, reply = answer(spoken_text)
            st.session_state.messages.append({"role": "user", "content": f"🎙️ {spoken_text}"})
            st.session_state.messages.append({"role": "assistant", "content": f"🌐 {language}\n\n{reply}"})
            st.rerun()
        else:
            st.error("I couldn't understand that recording. Please try again in a quiet place.")
