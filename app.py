from flask import Flask, render_template, request, redirect, url_for, session
import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
import os
import time

import requests
from google import genai
from datetime import datetime, date, timedelta
# Gemini Development Mode
USE_GEMINI = True


app = Flask(__name__)

app.secret_key = "ai-smart-farming-secret-key"

# Firebase connection
cred = credentials.Certificate("firebase-service-account.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# Gemini connection
client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)

# CEDA Market API key
CEDA_API_KEY = os.environ.get("CEDA_API_KEY")
CEDA_HEADERS = {
    "accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {CEDA_API_KEY}"
}


@app.route("/")
def login():
    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login_process():

    if request.method == "GET":
        return render_template("login.html")

    email = request.form["email"].strip()
    password = request.form["password"]

    try:

        # Find user by email
        users = db.collection("users").where(
            "email", "==", email
        ).limit(1).stream()

        user = None

        for doc in users:
            user = doc.to_dict()
            break

        # User not found
        if user is None:
            return render_template(
                "login.html",
                error="Invalid email or password."
            )

        # Check password
        if not check_password_hash(
            user["password"],
            password
        ):
            return render_template(
                "login.html",
                error="Invalid email or password."
            )

        # Save login session
        session["user_email"] = user["email"]

        # Login successful
        return redirect(
            url_for("dashboard")
        )

    except Exception as e:

        print(
            "Login Error:",
            repr(e)
        )

        return render_template(
            "login.html",
            error="Unable to login. Please try again."
        )

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    name = request.form["name"].strip()
    email = request.form["email"].strip()
    mobile = request.form["mobile"].strip()
    Address= request.form["address"].strip()
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]

    if password != confirm_password:
        return render_template(
            "register.html",
            error="Passwords do not match."
        )

    try:
        # Check if email already exists
        existing_user = db.collection("users").where(
            "email", "==", email
        ).limit(1).stream()

        if any(existing_user):
            return render_template(
                "register.html",
                error="Email already registered."
            )

        # Save user in Firestore
        db.collection("users").add({
            "name": name,
            "email": email,
            "mobile": mobile,
            "Address": Address,
            "password": generate_password_hash(password),
            "account": "Active"
        })

        return render_template(
            "login.html",
            success="Registration successful. Please login."
        )
    except Exception as e:

        print("Registration Error:", repr(e))

        return render_template(
            "register.html",
            error="Unable to register. Please try again."
        )

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# ================= WEATHER =================

@app.route("/weather")
def weather():
    return render_template("weather.html")

@app.route("/fertilizer")
def fertilizer():
    return render_template("fertilizer.html")

@app.route("/irrigation")
def irrigation():
    return render_template("irrigation.html")

@app.route("/market")
def market():
    return render_template("market.html")


@app.route("/market_prices")
def market_prices():

    crop = request.args.get("crop", "").strip()
    state = request.args.get("state", "").strip()
    district = request.args.get("district", "").strip()
    language = request.args.get("language", "en")

    # ==================================================
    # 1. Validate Input
    # ==================================================

    if not crop or not state or not district:

        return {
            "error": (
                "कृपया पीक, राज्य आणि जिल्हा भरा."
                if language == "mr"
                else "Please enter crop, state and district."
            )
        }

    # ==================================================
    # 2. Get CEDA API Key
    # ==================================================

    api_key = os.environ.get("CEDA_API_KEY")

    if not api_key:

        return {
            "error": (
                "CEDA API key सापडली नाही."
                if language == "mr"
                else "CEDA API key is missing."
            )
        }

    # ==================================================
    # 3. CEDA Authentication
    # ==================================================

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:

        # ==================================================
        # 4. GET COMMODITIES
        # ==================================================

        commodities_url = (
            "https://api.ceda.ashoka.edu.in/"
            "v1/agmarknet/commodities"
        )

        commodities_response = requests.get(
            commodities_url,
            headers=headers,
            timeout=20
        )

        print(
            "COMMODITIES STATUS:",
            commodities_response.status_code
        )

        commodities_response.raise_for_status()

        commodities_data = commodities_response.json()

        commodities_list = []

        if isinstance(commodities_data, dict):

            output = commodities_data.get(
                "output",
                {}
            )

            if isinstance(output, dict):

                commodities_list = output.get(
                    "data",
                    []
                )

        elif isinstance(commodities_data, list):

            commodities_list = commodities_data

        print(
            "TOTAL COMMODITIES:",
            len(commodities_list)
        )

        # ==================================================
        # Find Commodity ID
        # ==================================================

        commodity_id = None

        for item in commodities_list:

            commodity_name = str(
                item.get(
                    "commodity_name",
                    ""
                )
            ).strip()

            if commodity_name.lower() == crop.lower():

                commodity_id = item.get(
                    "commodity_id"
                )

                break

        print(
            "SEARCHED CROP:",
            crop
        )

        print(
            "COMMODITY ID:",
            commodity_id
        )

        if commodity_id is None:

            return {
                "error": (
                    f"'{crop}' पीक सापडले नाही."
                    if language == "mr"
                    else f"'{crop}' commodity was not found."
                )
            }

        # ==================================================
        # 5. GET GEOGRAPHIES
        # ==================================================

        geography_url = (
            "https://api.ceda.ashoka.edu.in/"
            "v1/agmarknet/geographies"
        )

        geography_response = requests.get(
            geography_url,
            headers=headers,
            timeout=20
        )

        print(
            "GEOGRAPHY STATUS:",
            geography_response.status_code
        )

        geography_response.raise_for_status()

        geography_data = geography_response.json()

        geographies = []

        if isinstance(geography_data, dict):

            output = geography_data.get(
                "output",
                {}
            )

            if isinstance(output, dict):

                geographies = output.get(
                    "data",
                    []
                )

        elif isinstance(geography_data, list):

            geographies = geography_data

        print(
            "TOTAL GEOGRAPHIES:",
            len(geographies)
        )

        # ==================================================
        # Find State and District IDs
        # ==================================================

        state_id = None
        district_id = None

        for item in geographies:

            item_state = str(
                item.get(
                    "census_state_name",
                    ""
                )
            ).strip()

            item_district = str(
                item.get(
                    "census_district_name",
                    ""
                )
            ).strip()

            if item_state.lower() == state.lower():

                state_id = item.get(
                    "census_state_id"
                )

                if item_district.lower() == district.lower():

                    district_id = item.get(
                        "census_district_id"
                    )

                    break

        print(
            "SEARCHED STATE:",
            state
        )

        print(
            "SEARCHED DISTRICT:",
            district
        )

        print(
            "STATE ID:",
            state_id
        )

        print(
            "DISTRICT ID:",
            district_id
        )

        if state_id is None:

            return {
                "error": (
                    "राज्य सापडले नाही."
                    if language == "mr"
                    else "State was not found."
                )
            }

        if district_id is None:

            return {
                "error": (
                    "जिल्हा सापडला नाही."
                    if language == "mr"
                    else "District was not found."
                )
            }

        # ==================================================
        # 6. GET MARKETS
        # ==================================================

        markets_url = (
            "https://api.ceda.ashoka.edu.in/"
            "v1/agmarknet/markets"
        )

        markets_payload = {

            "commodity_id": commodity_id,

            "state_id": state_id,

            "district_id": district_id,

            "indicator": "price"
        }

        print(
            "MARKET PAYLOAD:",
            markets_payload
        )

        markets_response = requests.post(
            markets_url,
            headers=headers,
            json=markets_payload,
            timeout=30
        )

        print(
            "MARKETS STATUS:",
            markets_response.status_code
        )

        markets_response.raise_for_status()

        markets_data = markets_response.json()

        markets = []

        if isinstance(markets_data, dict):

            output = markets_data.get(
                "output",
                {}
            )

            if isinstance(output, dict):

                markets = output.get(
                    "data",
                    []
                )

        elif isinstance(markets_data, list):

            markets = markets_data

        print(
            "TOTAL MARKETS:",
            len(markets)
        )

        if not markets:

            return {
                "error": (
                    "बाजारांची माहिती उपलब्ध नाही."
                    if language == "mr"
                    else "No markets were found."
                )
            }

        # ==================================================
        # Get Market IDs and Names
        # ==================================================

        market_ids = []
        market_names = {}

        for market in markets:

            market_id = market.get(
                "market_id",
                market.get(
                    "id",
                    market.get(
                        "marketId"
                    )
                )
            )

            market_name = market.get(
                "market_name",
                market.get(
                    "name",
                    market.get(
                        "market",
                        "Market"
                    )
                )
            )

            if market_id is not None:

                market_ids.append(
                    market_id
                )

                market_names[
                    str(market_id)
                ] = str(market_name)

        print(
            "FINAL MARKET IDS:",
            market_ids
        )

        print(
            "MARKET NAMES:",
            market_names
        )

        if not market_ids:

            return {
                "error": (
                    "बाजार ID उपलब्ध नाही."
                    if language == "mr"
                    else "Market IDs were not found."
                )
            }

        # ==================================================
        # Use first 5 markets
        # ==================================================

        market_ids = market_ids[:5]

        print(
            "MARKET IDS USED:",
            market_ids
        )

        # ==================================================
        # 7. GET MARKET PRICES
        # ==================================================

        prices_url = (
            "https://api.ceda.ashoka.edu.in/"
            "v1/agmarknet/prices"
        )

        from datetime import date, timedelta

        # Today's date
        today = date.today()

        # ==================================================
        # AUTOMATIC DATE RANGE
        # Fetch last 365 days
        # so latest available data can be found
        # ==================================================

        from_date = today - timedelta(
            days=365
        )

        prices_payload = {

            "commodity_id": commodity_id,

            "state_id": state_id,

            "district_id": [
                district_id
            ],

            "market_id": market_ids,

            "from_date": from_date.strftime(
                "%Y-%m-%d"
            ),

            "to_date": today.strftime(
                "%Y-%m-%d"
            )
        }

        print("========================================")
        print("STARTING PRICE API CALL...")
        print("PRICE URL:", prices_url)
        print("FROM DATE:", from_date)
        print("TO DATE:", today)
        print("PRICE PAYLOAD:", prices_payload)
        print("========================================")

        prices_response = requests.post(
            prices_url,
            headers=headers,
            json=prices_payload,
            timeout=30
        )

        print(
            "PRICES STATUS:",
            prices_response.status_code
        )

        print(
            "PRICES RESPONSE:",
            prices_response.text[:1000]
        )

        prices_response.raise_for_status()

        prices_data = prices_response.json()

        # ==================================================
        # 8. Extract Price Records
        # ==================================================

        records = []

        if isinstance(prices_data, dict):

            output = prices_data.get(
                "output",
                {}
            )

            if isinstance(output, dict):

                records = output.get(
                    "data",
                    []
                )

        elif isinstance(prices_data, list):

            records = prices_data

        print(
            "TOTAL PRICE RECORDS:",
            len(records)
        )

        # ==================================================
        # 9. If No Data
        # ==================================================

        if not records:

            return {
                "error": (
                    "बाजार भावाचा डेटा उपलब्ध नाही."
                    if language == "mr"
                    else "No market price data is available for this crop and location."
                )
            }

        # ==================================================
        # 10. Prepare Price Records
        # ==================================================

        prices = []

        for item in records:

            market_id_value = item.get(
                "market_id",
                ""
            )

            market_name = market_names.get(
                str(market_id_value),
                f"Market {market_id_value}"
            )

            prices.append({

                "market": market_name,

                "min_price": item.get(
                    "min_price",
                    0
                ),

                "max_price": item.get(
                    "max_price",
                    0
                ),

                "modal_price": item.get(
                    "modal_price",
                    0
                ),

                "date": item.get(
                    "date",
                    ""
                )
            })

        # ==================================================
        # 11. Sort Newest First
        # ==================================================

        prices.sort(
            key=lambda x: x["date"],
            reverse=True
        )

        # Keep latest 20 records
        prices = prices[:20]

        print(
            "LATEST PRICE DATE:",
            prices[0]["date"]
        )

        print(
            "FINAL PRICES:",
            prices
        )

        # ==================================================
        # 12. Save History
        # ==================================================

        save_history(

            "Market Prices",

            f"Crop: {crop}, "
            f"State: {state}, "
            f"District: {district}",

            f"Market Price Data: {prices}"
        )

        # ==================================================
        # 13. Final Response
        # ==================================================

        return {
            "prices": prices
        }

    # ==================================================
    # ERROR HANDLING
    # ==================================================

    except requests.exceptions.Timeout as e:

        print(
            "Market API Timeout:",
            repr(e)
        )

        return {
            "error": (
                "बाजार भाव सेवा प्रतिसाद देण्यासाठी वेळ घेत आहे."
                if language == "mr"
                else "Market service is taking too long to respond."
            )
        }

    except requests.exceptions.HTTPError as e:

        print(
            "Market API HTTP Error:",
            repr(e)
        )

        return {
            "error": (
                "CEDA API मध्ये समस्या आहे."
                if language == "mr"
                else "There is a problem with the CEDA API."
            )
        }

    except requests.exceptions.RequestException as e:

        print(
            "Market API Connection Error:",
            repr(e)
        )

        return {
            "error": (
                "बाजार भाव सेवा उपलब्ध नाही."
                if language == "mr"
                else "Unable to connect to market price service."
            )
        }

    except Exception as e:

        print(
            "Market Price Error:",
            repr(e)
        )

        return {
            "error": (
                "बाजार भाव मिळवता आले नाहीत."
                if language == "mr"
                else "Unable to get market prices."
            )
        }

@app.route("/weather_data")
def weather_data():

    city = request.args.get("city", "").strip()
    language = request.args.get("language", "English")

    if not city:
        return {
            "error": "Please enter a city name."
        }, 400

    try:

        # ==========================================
        # STEP 1: Find city coordinates
        # ==========================================

        geo_url = "https://geocoding-api.open-meteo.com/v1/search"

        geo_params = {
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json"
        }

        geo_response = requests.get(
            geo_url,
            params=geo_params,
            timeout=10
        )

        geo_data = geo_response.json()

        if not geo_data.get("results"):

            return {
                "error": "City not found. Please enter a valid city name."
            }, 404

        location = geo_data["results"][0]

        latitude = location["latitude"]
        longitude = location["longitude"]

        city_name = location["name"]


        # ==========================================
        # STEP 2: Get current + daily weather
        # ==========================================

        weather_url = "https://api.open-meteo.com/v1/forecast"

        weather_params = {

            "latitude": latitude,
            "longitude": longitude,

            # Current weather
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "precipitation,"
                "weather_code,"
                "wind_speed_10m"
            ),

            # Next 7 days
            "daily": (
                "temperature_2m_max,"
                "temperature_2m_min,"
                "precipitation_sum,"
                "precipitation_probability_max,"
                "weather_code"
            ),

            "temperature_unit": "celsius",

            "wind_speed_unit": "kmh",

            "timezone": "auto"
        }


        weather_response = requests.get(
            weather_url,
            params=weather_params,
            timeout=10
        )

        weather_data = weather_response.json()


        if "current" not in weather_data:

            return {
                "error": "Weather information is not available."
            }, 500


        current = weather_data["current"]

        daily = weather_data.get("daily", {})


        # ==========================================
        # STEP 3: Weather conditions
        # ==========================================

        weather_code = current.get(
            "weather_code",
            0
        )


        english_conditions = {

            0: "Clear sky",

            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",

            45: "Fog",
            48: "Depositing rime fog",

            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",

            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",

            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",

            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",

            95: "Thunderstorm",

            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }


        marathi_conditions = {

            0: "आकाश निरभ्र",

            1: "मुख्यतः स्वच्छ",
            2: "अंशतः ढगाळ",
            3: "ढगाळ",

            45: "धुके",
            48: "धुके",

            51: "हलकी रिमझिम",
            53: "मध्यम रिमझिम",
            55: "जोरदार रिमझिम",

            61: "हलका पाऊस",
            63: "मध्यम पाऊस",
            65: "जोरदार पाऊस",

            71: "हलकी बर्फवृष्टी",
            73: "मध्यम बर्फवृष्टी",
            75: "जोरदार बर्फवृष्टी",

            80: "हलका पावसाचा शिडकावा",
            81: "मध्यम पावसाचा शिडकावा",
            82: "जोरदार पावसाचा शिडकावा",

            95: "वादळी पाऊस",

            96: "गारांसह वादळ",
            99: "जोरदार गारांसह वादळ"
        }


        if language == "Marathi":

            condition = marathi_conditions.get(
                weather_code,
                "हवामानाची माहिती उपलब्ध नाही"
            )

        else:

            condition = english_conditions.get(
                weather_code,
                "Weather information unavailable"
            )


        # ==========================================
        # STEP 4: Current rain
        # ==========================================

        precipitation = current.get(
            "precipitation",
            0
        )

        rain = precipitation > 0


        # ==========================================
        # STEP 5: Prepare 7-day forecast
        # ==========================================

        forecast = []

        dates = daily.get("time", [])

        max_temperatures = daily.get(
            "temperature_2m_max",
            []
        )

        min_temperatures = daily.get(
            "temperature_2m_min",
            []
        )

        precipitation_values = daily.get(
            "precipitation_sum",
            []
        )

        rain_probabilities = daily.get(
            "precipitation_probability_max",
            []
        )

        daily_codes = daily.get(
            "weather_code",
            []
        )


        for i in range(len(dates)):

            code = daily_codes[i] if i < len(daily_codes) else 0


            if language == "Marathi":

                daily_condition = marathi_conditions.get(
                    code,
                    "हवामान उपलब्ध नाही"
                )

            else:

                daily_condition = english_conditions.get(
                    code,
                    "Weather unavailable"
                )


            forecast.append({

                "date": dates[i],

                "max_temp": max_temperatures[i]
                if i < len(max_temperatures)
                else 0,

                "min_temp": min_temperatures[i]
                if i < len(min_temperatures)
                else 0,

                "rain": precipitation_values[i]
                if i < len(precipitation_values)
                else 0,

                "rain_probability": rain_probabilities[i]
                if i < len(rain_probabilities)
                else 0,

                "condition": daily_condition,

                "weather_code": code
            })


        # ==========================================
        # STEP 6: Farming advice
        # ==========================================

        humidity = current.get(
            "relative_humidity_2m",
            0
        )

        temperature = current.get(
            "temperature_2m",
            0
        )


        if rain:

            if language == "Marathi":

                farming_advice = (
                    "पाऊस सुरू असल्याने आज सिंचन टाळावे. "
                    "शेतात पाणी साचणार नाही याची काळजी घ्या."
                )

            else:

                farming_advice = (
                    "Rain is occurring, so avoid irrigation today. "
                    "Make sure water does not accumulate in the field."
                )


        elif rain_probabilities and rain_probabilities[0] >= 60:

            if language == "Marathi":

                farming_advice = (
                    "पावसाची शक्यता जास्त आहे. "
                    "आज सिंचन शक्यतो टाळावे आणि शेतातील निचरा तपासावा."
                )

            else:

                farming_advice = (
                    "There is a high chance of rain. "
                    "Avoid irrigation if possible and check field drainage."
                )


        elif temperature >= 35:

            if language == "Marathi":

                farming_advice = (
                    "तापमान जास्त आहे. "
                    "पिकाला आवश्यकतेनुसार पाणी द्यावे आणि "
                    "दुपारच्या तीव्र उन्हापासून पिकाचे संरक्षण करावे."
                )

            else:

                farming_advice = (
                    "Temperature is high. "
                    "Provide water according to crop needs and "
                    "protect crops from strong afternoon heat."
                )


        elif humidity >= 80:

            if language == "Marathi":

                farming_advice = (
                    "आर्द्रता जास्त आहे. "
                    "पिकांमध्ये बुरशीजन्य रोगांची लक्षणे तपासा "
                    "आणि शेतात योग्य हवा खेळती राहील याची काळजी घ्या."
                )

            else:

                farming_advice = (
                    "Humidity is high. "
                    "Check crops for fungal disease symptoms "
                    "and maintain proper air circulation."
                )


        else:

            if language == "Marathi":

                farming_advice = (
                    "हवामान सामान्य आहे. "
                    "पिकाच्या गरजेनुसार सिंचन करा आणि नियमित निरीक्षण करा."
                )

            else:

                farming_advice = (
                    "Weather conditions are normal. "
                    "Irrigate according to crop needs and monitor the crop regularly."
                )


        # ==========================================
        # STEP 7: Send all data to weather.html
        # ==========================================
                # Save weather activity to history
        save_history(
            "Weather",
            city_name,
            f"Temperature: {temperature}°C, "
            f"Humidity: {humidity}%, "
            f"Condition: {condition}, "
            f"Rain: {precipitation} mm, "
            f"Advice: {farming_advice}"
        )

        return {

            "city": city_name,

            "temperature": current.get(
                "temperature_2m",
                0
            ),

            "humidity": humidity,

            "wind": current.get(
                "wind_speed_10m",
                0
            ),

            "condition": condition,

            "rain": rain,

            "precipitation": precipitation,

            "forecast": forecast,

            "farming_advice": farming_advice

        }


    except Exception as e:

        print(
            "Weather Error:",
            repr(e)
        )

        return {

            "error":
            "Unable to connect to weather service."

        }, 500

@app.route("/irrigation_advice", methods=["GET"])
def irrigation_advice():

    crop = request.args.get("crop", "").strip()
    stage = request.args.get("stage", "").strip()
    soil = request.args.get("soil", "").strip()
    city = request.args.get("city", "").strip()
    language = request.args.get("language", "English").strip()

    # -----------------------------------
    # 1. CHECK INPUTS
    # -----------------------------------

    if not crop or not stage or not soil or not city:
        return {
            "weather": "Please enter all details.",
            "when": "",
            "amount": "",
            "reason": "",
            "advice": "Please enter crop, growth stage, soil type and city."
        }

    try:

        # -----------------------------------
        # 2. GET CITY LOCATION
        # -----------------------------------

        geo_url = "https://geocoding-api.open-meteo.com/v1/search"

        geo_params = {
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json"
        }

        geo_response = requests.get(
            geo_url,
            params=geo_params,
            timeout=10
        )

        geo_data = geo_response.json()

        if "results" not in geo_data or len(geo_data["results"]) == 0:
            return {
                "weather": "City not found",
                "when": "",
                "amount": "",
                "reason": "",
                "advice": "Please enter a valid city name."
            }

        latitude = geo_data["results"][0]["latitude"]
        longitude = geo_data["results"][0]["longitude"]

        # -----------------------------------
        # 3. GET LIVE WEATHER
        # -----------------------------------

        weather_url = "https://api.open-meteo.com/v1/forecast"

        weather_params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "precipitation,"
                "weather_code,"
                "wind_speed_10m"
            ),
            "daily": (
                "precipitation_probability_max,"
                "precipitation_sum"
            ),
            "forecast_days": 1,
            "timezone": "auto"
        }

        weather_response = requests.get(
            weather_url,
            params=weather_params,
            timeout=10
        )

        weather_data = weather_response.json()

        current = weather_data["current"]
        daily = weather_data["daily"]

        temperature = current["temperature_2m"]
        humidity = current["relative_humidity_2m"]
        precipitation = current["precipitation"]
        wind = current["wind_speed_10m"]

        rain_probability = daily["precipitation_probability_max"][0]
        rain_amount = daily["precipitation_sum"][0]

        # -----------------------------------
        # 4. WEATHER CONDITION
        # -----------------------------------

        if precipitation > 0:
            condition = "Rain"

        elif rain_probability >= 60:
            condition = "Rain likely"

        elif temperature >= 35:
            condition = "Hot"

        elif humidity >= 80:
            condition = "Humid"

        else:
            condition = "Normal"

        weather_text = (
            f"{condition} | "
            f"Temperature: {temperature}°C | "
            f"Humidity: {humidity}% | "
            f"Rain chance: {rain_probability}% | "
            f"Rain: {rain_amount} mm | "
            f"Wind: {wind} km/h"
        )

        # -----------------------------------
        # 5. CREATE GEMINI PROMPT
        # -----------------------------------

        if language.lower() == "marathi":

            prompt = f"""
तुम्ही AI Agriculture Irrigation Assistant आहात.

शेतकऱ्याला दिलेल्या माहितीच्या आधारे सिंचनाचा योग्य सल्ला द्या.

पीक: {crop}
वाढीची अवस्था: {stage}
मातीचा प्रकार: {soil}
शहर: {city}

सध्याचे हवामान:
तापमान: {temperature}°C
आर्द्रता: {humidity}%
पावसाची शक्यता: {rain_probability}%
पावसाचे प्रमाण: {rain_amount} mm
वारा: {wind} km/h
हवामान स्थिती: {condition}

पीक, वाढीची अवस्था, माती आणि हवामान या सर्व माहितीचा विचार करा.

खालील headings EXACT वापरा:

When to Irrigate:
How Much Water:
Reason:
Farming Advice:

उत्तर सोप्या आणि शेतकऱ्याला समजेल अशा मराठीत द्या.
"""

        else:

            prompt = f"""
You are an AI Agriculture Irrigation Assistant.

Give practical irrigation advice to a farmer using ALL the information below.

Crop: {crop}
Growth Stage: {stage}
Soil Type: {soil}
City: {city}

Current Weather:
Temperature: {temperature}°C
Humidity: {humidity}%
Rain Probability: {rain_probability}%
Rain Amount: {rain_amount} mm
Wind: {wind} km/h
Weather Condition: {condition}

Consider the crop, growth stage, soil type and current weather together.

Use EXACTLY these headings:

When to Irrigate:
How Much Water:
Reason:
Farming Advice:

Give simple, practical and understandable advice for a farmer.

Do not give generic advice.
Base the recommendation on the provided crop,
growth stage, soil type and weather information.
"""

        # -----------------------------------
        # 6. GEMINI OR DEMO MODE
        # -----------------------------------

        if USE_GEMINI:

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            ai_text = response.text

            print("====================================")
            print("GEMINI IRRIGATION RESPONSE USED")
            print("====================================")

        else:

            ai_text = """
When to Irrigate:
Irrigation advice is available in Demo Mode.

How Much Water:
Use the normal water requirement recommended for the selected crop and soil.

Reason:
This is a development demo without calling Gemini AI.

Farming Advice:
For the final AI recommendation, turn ON Gemini AI.
"""

            print("====================================")
            print("GEMINI OFF - DEMO MODE")
            print("====================================")

        # -----------------------------------
        # 7. READ AI RESPONSE
        # -----------------------------------

        when = ""
        amount = ""
        reason = ""
        advice = ""

        if "When to Irrigate:" in ai_text:

            when = ai_text.split(
                "When to Irrigate:"
            )[1].split(
                "How Much Water:"
            )[0].strip()

        if "How Much Water:" in ai_text:

            amount = ai_text.split(
                "How Much Water:"
            )[1].split(
                "Reason:"
            )[0].strip()

        if "Reason:" in ai_text:

            reason = ai_text.split(
                "Reason:"
            )[1].split(
                "Farming Advice:"
            )[0].strip()

        if "Farming Advice:" in ai_text:

            advice = ai_text.split(
                "Farming Advice:"
            )[1].strip()

        # -----------------------------------
        # 8. SAVE HISTORY
        # -----------------------------------

        save_history(
            "Irrigation",
            f"Crop: {crop}, Stage: {stage}, "
            f"Soil: {soil}, City: {city}",
            f"Weather: {weather_text} | "
            f"When: {when} | "
            f"Amount: {amount} | "
            f"Reason: {reason} | "
            f"Advice: {advice}"
        )

        # -----------------------------------
        # 9. RETURN RESULT
        # -----------------------------------

        return {
            "weather": weather_text,
            "when": when,
            "amount": amount,
            "reason": reason,
            "advice": advice
        }

    # -----------------------------------
    # 10. ERROR
    # -----------------------------------

    except Exception as e:

        print("====================================")
        print("IRRIGATION ERROR")
        print(repr(e))
        print("====================================")

        return {
            "weather": "Unable to get irrigation advice.",
            "when": "",
            "amount": "",
            "reason": "",
            "advice": "Gemini AI could not generate the irrigation advice."
        }
@app.route("/fertilizer_recommendation", methods=["GET"])
def fertilizer_recommendation():

    crop = request.args.get("crop", "").strip()
    stage = request.args.get("stage", "").strip()
    city = request.args.get("city", "").strip()
    language = request.args.get("language", "en").strip()

    # -----------------------------------
    # 1. VALIDATION
    # -----------------------------------

    if not crop or not stage or not city:
        return {
            "weather": "",
            "fertilizer": "",
            "quantity": "",
            "reason": "",
            "advice": "Please enter crop, growth stage and city."
        }

    try:

        # -----------------------------------
        # 2. GET CITY LOCATION
        # -----------------------------------

        geo_url = "https://geocoding-api.open-meteo.com/v1/search"

        geo_params = {
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json"
        }

        geo_response = requests.get(
            geo_url,
            params=geo_params,
            timeout=10
        )

        geo_data = geo_response.json()

        if "results" not in geo_data or len(geo_data["results"]) == 0:
            return {
                "weather": "City not found",
                "fertilizer": "",
                "quantity": "",
                "reason": "",
                "advice": "Please enter a valid city."
            }

        latitude = geo_data["results"][0]["latitude"]
        longitude = geo_data["results"][0]["longitude"]

        # -----------------------------------
        # 3. GET LIVE WEATHER
        # -----------------------------------

        weather_url = "https://api.open-meteo.com/v1/forecast"

        weather_params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "precipitation,"
                "weather_code,"
                "wind_speed_10m"
            ),
            "daily": (
                "precipitation_probability_max,"
                "precipitation_sum"
            ),
            "forecast_days": 1,
            "timezone": "auto"
        }

        weather_response = requests.get(
            weather_url,
            params=weather_params,
            timeout=10
        )

        weather_data = weather_response.json()

        current = weather_data["current"]
        daily = weather_data["daily"]

        temperature = current["temperature_2m"]
        humidity = current["relative_humidity_2m"]
        precipitation = current["precipitation"]
        wind = current["wind_speed_10m"]

        rain_probability = daily["precipitation_probability_max"][0]
        rain_amount = daily["precipitation_sum"][0]

        # -----------------------------------
        # 4. WEATHER CONDITION
        # -----------------------------------

        if precipitation > 0:
            condition = "Rain"

        elif rain_probability >= 60:
            condition = "Rain likely"

        elif temperature >= 35:
            condition = "Hot"

        elif humidity >= 80:
            condition = "Humid"

        else:
            condition = "Normal"

        weather_text = (
            f"{condition} | "
            f"Temperature: {temperature}°C | "
            f"Humidity: {humidity}% | "
            f"Rain chance: {rain_probability}% | "
            f"Rain: {rain_amount} mm | "
            f"Wind: {wind} km/h"
        )

        # -----------------------------------
        # 5. DEMO RESPONSE
        # -----------------------------------

        if language.lower() == "mr":

            fertilizer = (
                "Balanced fertilizer such as NPK "
                "may be suitable during the initial stage."
            )

            quantity = (
                "Use the crop-recommended quantity and "
                "follow soil-test or local agriculture advice."
            )

            reason = (
                "The selected growth stage requires "
                "appropriate nutrients for healthy crop growth."
            )

            advice = (
                "Avoid excessive fertilizer. Apply fertilizer "
                "when soil moisture is suitable."
            )

        else:

            fertilizer = (
                "A balanced fertilizer such as NPK "
                "may be suitable during the selected growth stage."
            )

            quantity = (
                "Use the crop-recommended quantity and "
                "follow soil-test or local agriculture advice."
            )

            reason = (
                "The selected growth stage requires "
                "appropriate nutrients for healthy crop growth."
            )

            advice = (
                "Avoid excessive fertilizer. Apply fertilizer "
                "when soil moisture is suitable."
            )

        # -----------------------------------
        # 6. GEMINI AI
        # -----------------------------------

        if USE_GEMINI:

            if language.lower() == "mr":

                prompt = f"""
तुम्ही AI Agriculture Fertilizer Assistant आहात.

खालील माहिती वापरून शेतकऱ्याला खताची शिफारस द्या.

पीक: {crop}
वाढीचा टप्पा: {stage}
शहर: {city}

सध्याचे हवामान:
तापमान: {temperature}°C
आर्द्रता: {humidity}%
पावसाची शक्यता: {rain_probability}%
पाऊस: {rain_amount} mm
वारा: {wind} km/h
हवामान स्थिती: {condition}

पीक, वाढीचा टप्पा आणि हवामान यांचा विचार करा.

खालील headings EXACT वापरा:

Recommended Fertilizer:
Recommended Quantity:
Reason:
Farming Advice:

उत्तर सोप्या मराठीत द्या.

Exact chemical dosage अंदाजाने देऊ नका.
गरज असल्यास soil test आणि स्थानिक कृषी तज्ज्ञांचा सल्ला घेण्यास सांगा.
"""

            else:

                prompt = f"""
You are an AI Agriculture Fertilizer Assistant.

Give a practical fertilizer recommendation using ALL the following information.

Crop: {crop}
Growth Stage: {stage}
City: {city}

Live Weather:
Temperature: {temperature}°C
Humidity: {humidity}%
Rain Probability: {rain_probability}%
Rain: {rain_amount} mm
Wind: {wind} km/h
Weather Condition: {condition}

Consider the crop, growth stage and live weather together.

Use EXACTLY these headings:

Recommended Fertilizer:
Recommended Quantity:
Reason:
Farming Advice:

Give simple and practical advice for a farmer.

Do not invent an exact chemical dosage.
When appropriate, recommend following soil-test results
and local agricultural expert recommendations.
"""

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            ai_text = response.text

            print("====================================")
            print("GEMINI FERTILIZER RESPONSE USED")
            print("====================================")

            # -----------------------------------
            # READ GEMINI RESPONSE
            # -----------------------------------

            if "Recommended Fertilizer:" in ai_text:

                fertilizer = (
                    ai_text
                    .split("Recommended Fertilizer:")[1]
                    .split("Recommended Quantity:")[0]
                    .strip()
                )

            if "Recommended Quantity:" in ai_text:

                quantity = (
                    ai_text
                    .split("Recommended Quantity:")[1]
                    .split("Reason:")[0]
                    .strip()
                )

            if "Reason:" in ai_text:

                reason = (
                    ai_text
                    .split("Reason:")[1]
                    .split("Farming Advice:")[0]
                    .strip()
                )

            if "Farming Advice:" in ai_text:

                advice = (
                    ai_text
                    .split("Farming Advice:")[1]
                    .strip()
                )

        else:

            print("====================================")
            print("GEMINI OFF - FERTILIZER DEMO MODE")
            print("====================================")

        # -----------------------------------
        # 7. SAVE HISTORY
        # -----------------------------------

        save_history(
            "Fertilizer",
            f"Crop: {crop}, Stage: {stage}, City: {city}",
            f"Weather: {weather_text} | "
            f"Fertilizer: {fertilizer} | "
            f"Quantity: {quantity} | "
            f"Reason: {reason} | "
            f"Advice: {advice}"
        )

        # -----------------------------------
        # 8. RETURN RESULT
        # -----------------------------------

        return {
            "weather": weather_text,
            "fertilizer": fertilizer,
            "quantity": quantity,
            "reason": reason,
            "advice": advice
        }

    # -----------------------------------
    # 9. ERROR
    # -----------------------------------

    except Exception as e:

        print("====================================")
        print("FERTILIZER ERROR")
        print(repr(e))
        print("====================================")

        return {
            "weather": "Unable to get weather information.",
            "fertilizer": "",
            "quantity": "",
            "reason": "",
            "advice": "Unable to generate fertilizer recommendation."
        }

@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")


@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    user_message = data.get("message", "").strip()
    language = data.get("language", "English")

    if not user_message:
        return {
            "reply": "Please enter your question."
        }

    # Marathi prompt
    if language == "Marathi":

        prompt = f"""
You are an AI Agriculture Assistant.

Answer the farmer's question in simple Marathi using Marathi script.

The farmer may type Marathi, English, or Roman Marathi.

Give practical and easy-to-understand farming advice.

Question:
{user_message}
"""

    # English prompt
    else:

        prompt = f"""
You are an AI Agriculture Assistant.

Answer the farmer's question in simple English.

Give practical and easy-to-understand farming advice.

Question:
{user_message}
"""

    # =====================================
    # GEMINI ON / OFF
    # =====================================

    if USE_GEMINI:

        try:

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            reply = response.text

            print("GEMINI CHATBOT RESPONSE USED")

        except Exception as e:

            print("Gemini Chatbot Error:", repr(e))

            return {
                "reply": "Gemini is temporarily unavailable. Please try again later."
            }

    else:

        # Demo response - Gemini API is not called
        if language == "Marathi":

            reply = """
डेमो मोडमध्ये तुमच्या प्रश्नाचे उत्तर दिले जात आहे.

पिकाची योग्य निगा राखा, जमिनीतील ओलावा तपासा आणि पिकाच्या अवस्थेनुसार पाणी व खत द्या.

अधिक अचूक AI उत्तरासाठी Gemini AI ON करा.
"""

        else:

            reply = """
This is a Demo Mode response.

Maintain proper crop care, check soil moisture, and provide water and fertilizer according to the crop growth stage.

Turn ON Gemini AI for an actual AI-generated answer.
"""

        print("GEMINI OFF - CHATBOT DEMO MODE")

    # =====================================
    # SAVE CHATBOT HISTORY
    # =====================================

    save_history(
        "Chatbot",
        user_message,
        reply
    )

    return {
        "reply": reply
    }
 
@app.route("/disease")
def disease():
    return render_template("disease.html")


@app.route("/predict", methods=["POST"])
def predict():

    try:

        # -----------------------------------
        # 1. GET UPLOADED IMAGE
        # -----------------------------------

        image_file = request.files.get("leaf_image")
        language = request.form.get("language", "en")

        if not image_file:
            return render_template(
                "disease.html",
                error="Please upload a plant or leaf image."
            )

        # -----------------------------------
        # 2. OPEN IMAGE
        # -----------------------------------

        image = Image.open(image_file).convert("RGB")

        # -----------------------------------
        # 3. LANGUAGE INSTRUCTION
        # -----------------------------------

        if language == "mr":

            language_instruction = """
Answer the values in simple Marathi using Marathi script.

Keep the field names exactly in English:

Plant
Possible Disease
Symptoms
Cause
Treatment
Prevention
"""

        else:

            language_instruction = """
Answer the values in simple English.

Keep the field names exactly in English:

Plant
Possible Disease
Symptoms
Cause
Treatment
Prevention
"""

        # -----------------------------------
        # 4. GEMINI PROMPT
        # -----------------------------------

        prompt = f"""

You are an AI Agriculture Disease Detection Assistant.

{language_instruction}

Analyze the uploaded plant or leaf image carefully.

Identify the plant/crop if possible and identify the possible disease
based only on visible symptoms in the image.

IMPORTANT:

- Do not assume the crop is Soybean.
- The image may belong to any plant or crop.
- If you are not sure, clearly say "Uncertain".
- Do not claim 100% accuracy.
- Give practical and simple agricultural advice.

Return the answer EXACTLY in this format:

Plant: <plant or crop name>

Possible Disease: <disease name or Healthy or Uncertain>

Symptoms: <visible symptoms>

Cause: <possible cause>

Treatment: <recommended treatment>

Prevention: <prevention steps>

Do not add any extra headings before or after these fields.

"""

        # -----------------------------------
        # 5. GEMINI OR DEMO MODE
        # -----------------------------------

        if USE_GEMINI:

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=[prompt, image]
            )

            result_text = response.text

            print("====================================")
            print("GEMINI DISEASE RESPONSE USED")
            print("====================================")

        else:

            # Development / Testing Mode
            result_text = """
Plant: Demo Plant

Possible Disease: Demo Mode

Symptoms: Disease analysis is disabled during development testing.

Cause: Gemini AI is currently turned off.

Treatment: Turn on Gemini AI for actual disease analysis.

Prevention: Use healthy planting material and maintain proper crop care.
"""

            print("====================================")
            print("GEMINI OFF - DISEASE DEMO MODE")
            print("====================================")

        # -----------------------------------
        # 6. EXTRACT INFORMATION
        # -----------------------------------

        def get_value(label):

            for line in result_text.splitlines():

                if line.strip().startswith(label):

                    return line.split(":", 1)[1].strip()

            return "Information not available."

        crop = get_value("Plant")
        disease = get_value("Possible Disease")
        symptoms = get_value("Symptoms")
        cause = get_value("Cause")
        treatment = get_value("Treatment")
        prevention = get_value("Prevention")

        # -----------------------------------
        # 7. SAVE HISTORY
        # -----------------------------------

        save_history(
            "Disease Detection",
            f"Plant: {crop}",
            f"Disease: {disease} | "
            f"Symptoms: {symptoms} | "
            f"Cause: {cause} | "
            f"Treatment: {treatment} | "
            f"Prevention: {prevention}"
        )

        # -----------------------------------
        # 8. SHOW RESULT
        # -----------------------------------

        return render_template(
            "disease.html",
            crop=crop,
            result=disease,
            symptoms=symptoms,
            cause=cause,
            treatment=treatment,
            prevention=prevention
        )

    # -----------------------------------
    # 9. ERROR
    # -----------------------------------

    except Exception as e:

        print("====================================")
        print("DISEASE DETECTION ERROR")
        print(repr(e))
        print("====================================")

        return render_template(
            "disease.html",
            error="Disease detection could not be completed."
        )

@app.route("/profile")
def profile():

    email = session.get("user_email")

    if not email:
        return redirect(url_for("login"))

    try:

        users = db.collection("users").where(
            "email", "==", email
        ).limit(1).stream()

        user = None

        for doc in users:
            user = doc.to_dict()
            break

        if user is None:
            return redirect(url_for("login"))

        return render_template(
            "profile.html",
            user=user
        )

    except Exception as e:

        print("Profile Error:", repr(e))

        return render_template(
            "profile.html",
            error="Unable to load profile."
        )

@app.route("/history")
def history():

    email = session.get("user_email")

    if not email:
        return redirect(url_for("login"))

    try:

        history_data = []

        records = db.collection("history") \
                    .where("user_email", "==", email) \
                    .stream()

        for doc in records:

            data = doc.to_dict()

            history_data.append({
                "date": data.get("date", ""),
                "feature": data.get("feature", ""),
                "input": data.get("input", ""),
                "result": data.get("result", "")
            })

        # Latest history first
        history_data.reverse()

        return render_template(
            "history.html",
            history=history_data
        )

    except Exception as e:

        print("History Error:", repr(e))

        return render_template(
            "history.html",
            history=[],
            error="Unable to load history."
        )

def save_history(feature, user_input, result):
    try:
        email = session.get("user_email")

        if not email:
            return

        db.collection("history").add({
            "user_email": email,
            "date": datetime.now().strftime("%d-%m-%Y %I:%M %p"),
            "feature": feature,
            "input": user_input,
            "result": result
        })

        print("History saved successfully.")

    except Exception as e:
        print("History Save Error:", repr(e))
 
 
@app.route("/about") 
def about(): 
    return render_template("about.html") 
 
if __name__ == "__main__": 
    print("Starting AI Smart Farming Assistant...") 
    app.run(debug=True)