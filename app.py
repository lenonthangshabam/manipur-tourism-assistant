import hashlib
import io

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
    q = query.lower()
    budget_words = [
        "budget", "cost", "costs", "price", "prices", "money",
        "expense", "expenses", "spend", "spending", "how much",
        "cheap", "affordable", "estimated cost", "travel cost"
    ]
    return any(word in q for word in budget_words)


def is_trip_query(query: str):
    q = query.lower()
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

    # Explicit budget questions go only to the budget planner.
    if is_budget_query(query):
        result = budget_planner(query)
        if result:
            return result

    # Trip/itinerary questions go only to the trip planner.
    if is_trip_query(query):
        result = trip_planner(query)
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
    """Convert a Streamlit microphone recording (WAV) into text."""
    recognizer = sr.Recognizer()
    audio_bytes = uploaded_audio.getvalue()

    try:
        # st.audio_input returns an audio/wav UploadedFile.
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(
            audio,
            language=speech_language_code(language),
        )
        return text, None

    except sr.UnknownValueError:
        return None, "I couldn't understand the recording. Please speak clearly and try again."
    except sr.RequestError as exc:
        return None, (
            "Speech recognition service is unavailable right now. "
            f"Details: {exc}"
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
st.caption("Record a question and the assistant will automatically transcribe it and answer.")

voice_language = st.selectbox(
    "Spoken language",
    ["English", "Hindi"],
    key="voice_language",
)
audio = st.audio_input("🎙️ Record your question", sample_rate=16000, key="tourism_voice")

if audio:
    audio_hash = hashlib.sha256(audio.getvalue()).hexdigest()

    # Prevent the same recording from being processed repeatedly on every Streamlit rerun.
    if st.session_state.get("processed_voice_hash") != audio_hash:
        with st.spinner("🎧 Understanding your question…"):
            spoken_text, voice_error = transcribe_audio(audio, voice_language)

        st.session_state.processed_voice_hash = audio_hash

        if spoken_text:
            language, reply = answer(spoken_text)
            st.session_state.messages.append({"role": "user", "content": f"🎙️ {spoken_text}"})
            st.session_state.messages.append({"role": "assistant", "content": f"🌐 {language}\n\n{reply}"})
            st.success(f"Heard: {spoken_text}")
            st.rerun()
        else:
            st.error(voice_error or "I couldn't understand the recording. Please try again.")
