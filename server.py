"""Farm Helper MCP server (Streamable HTTP) for the Alexa+ track."""
import json, os
from pathlib import Path
import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from starlette.responses import HTMLResponse, JSONResponse
from starlette.concurrency import run_in_threadpool

load_dotenv()
DATA = Path(__file__).parent / "data"
CALENDAR = json.loads((DATA / "crop_calendar.json").read_text())
PRICES = json.loads((DATA / "mandi_prices.json").read_text())

mcp = FastMCP("farm-helper", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

@mcp.custom_route("/", methods=["GET"])
async def home(request):
    return HTMLResponse((Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8"))

@mcp.custom_route("/api/ask", methods=["POST"])
async def ask(request):
    """Demo endpoint: routes a spoken/typed request to the same tool functions the MCP server exposes."""
    import re
    text = (await request.json()).get("text", "")
    t = text.lower()
    crop = next((c for c in CALENDAR if c in t), None)
    m = re.search(r"\bin ([a-z ]+?)(?: today| now| tomorrow|\?|$)", t)
    city = m.group(1).strip() if m else "Bengaluru"
    if any(w in t for w in ["price", "rate", "mandi", "cost", "sell"]) and crop:
        tool, reply = "get_mandi_price", get_mandi_price(crop)
    elif any(w in t for w in ["water", "irrigat", "rain"]) and crop:
        tool, reply = "get_irrigation_advice", await get_irrigation_advice(crop, city)
    elif any(w in t for w in ["sow", "plant", "harvest", "when", "calendar", "grow"]) and crop:
        tool, reply = "get_crop_calendar", get_crop_calendar(crop)
    elif any(w in t for w in ["yellow", "spot", "curl", "wilt", "disease", "healthy", "white", "leaf", "leaves"]):
        tool, reply = "diagnose_crop_disease", diagnose_crop_disease(crop or "plant", text)
    else:
        tool, reply = None, "I can help with crop diseases, watering, market prices and sowing times. Mention a crop like tomato, rice, ragi, maize or chilli."
    return JSONResponse({"tool": tool, "reply": reply})

@mcp.custom_route("/api/image", methods=["POST"])
async def image(request):
    """Demo endpoint: leaf photo (base64 JPEG) -> diagnose_leaf_image tool."""
    body = await request.json()
    reply = await run_in_threadpool(diagnose_leaf_image, body.get("image", ""), body.get("crop", "plant"))
    return JSONResponse({"tool": "diagnose_leaf_image", "reply": reply})

RULES = {
    "yellow": "Possible nitrogen deficiency or early blight. Add compost/urea and remove affected leaves.",
    "spots": "Likely fungal leaf spot or blight. Remove infected leaves; spray copper fungicide or neem oil.",
    "curl": "Possible leaf curl virus (whitefly). Remove plants, use yellow sticky traps and neem spray.",
    "wilt": "Possible bacterial/fusarium wilt or overwatering. Improve drainage; rotate crops next season.",
    "white powder": "Powdery mildew. Spray diluted milk or sulphur-based fungicide.",
}

def _bedrock_diagnose(crop: str, symptoms: str) -> str | None:
    try:
        import boto3
        client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))
        prompt = (f"You are an agronomist helping an Indian farmer. Crop: {crop}. Symptoms: {symptoms}. "
                  "Give the most likely cause and 3 short, practical treatment steps. Under 80 words, plain language.")
        r = client.converse(
            modelId=os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"),
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 300, "temperature": 0.2},
        )
        return r["output"]["message"]["content"][0]["text"]
    except Exception:
        return None  # fall back to rules

@mcp.tool()
def diagnose_crop_disease(crop: str, symptoms: str) -> str:
    """Diagnose a crop problem from described symptoms (e.g. 'yellow leaves with brown spots') and suggest treatment."""
    ai = _bedrock_diagnose(crop, symptoms)
    if ai:
        return ai
    s = symptoms.lower()
    for key, advice in RULES.items():
        if key in s:
            return f"{crop.title()}: {advice}"
    return f"Not enough detail for {crop}. Describe leaf colour, spots, wilting or pests, and I'll narrow it down."

@mcp.tool()
def diagnose_leaf_image(image_base64: str, crop: str = "plant") -> str:
    """Analyse a photo of a crop leaf (base64 JPEG) for disease or nutrient problems and suggest treatment."""
    try:
        import base64, boto3
        raw = base64.b64decode(image_base64)
        client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))
        prompt = (f"You are an agronomist helping an Indian farmer. This is a photo of a {crop} leaf/plant. "
                  "Identify the crop if unclear, the most likely disease, pest or nutrient problem, and 3 short practical "
                  "treatment steps. If the photo is unclear or not a plant, say so. Under 90 words, plain language.")
        r = client.converse(
            modelId=os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"),
            messages=[{"role": "user", "content": [
                {"image": {"format": "jpeg", "source": {"bytes": raw}}},
                {"text": prompt}]}],
            inferenceConfig={"maxTokens": 400, "temperature": 0.2},
        )
        return r["output"]["message"]["content"][0]["text"]
    except Exception as e:
        print("Bedrock image error:", e)
        return "Image analysis needs AWS Bedrock access. Run 'aws configure', enable a Claude model in Bedrock, and set BEDROCK_MODEL_ID in .env."

@mcp.tool()
async def get_irrigation_advice(crop: str, city: str) -> str:
    """Advise whether to water a crop today, using the city's live weather forecast."""
    info = CALENDAR.get(crop.lower())
    async with httpx.AsyncClient(timeout=10) as c:
        g = (await c.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1})).json()
        if not g.get("results"):
            return f"I couldn't find {city}."
        loc = g["results"][0]
        w = (await c.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": loc["latitude"], "longitude": loc["longitude"],
            "daily": "precipitation_sum,temperature_2m_max", "forecast_days": 2, "timezone": "auto"})).json()
    rain = w["daily"]["precipitation_sum"][:2]
    temp = w["daily"]["temperature_2m_max"][0]
    base = f" Normal schedule for {crop}: {info['water']}." if info else ""
    if max(rain) >= 5:
        return f"Skip watering: about {max(rain):.0f} mm rain expected in {city} over the next 2 days.{base}"
    if temp >= 34:
        return f"Water today, preferably early morning or evening. It's hot ({temp:.0f}°C) with little rain.{base}"
    return f"Light watering is fine; little rain expected ({max(rain):.1f} mm).{base}"

@mcp.tool()
def get_mandi_price(crop: str) -> str:
    """Get the approximate market (mandi) price of a crop per quintal in INR."""
    p = PRICES.get(crop.lower())
    return f"{crop.title()} is around ₹{p} per quintal (demo data)." if p else f"No price data for {crop}."

@mcp.tool()
def get_crop_calendar(crop: str) -> str:
    """Get sowing time, harvest time, watering and soil guidance for a crop."""
    i = CALENDAR.get(crop.lower())
    if not i:
        return f"No calendar for {crop}. Known crops: {', '.join(CALENDAR)}."
    return f"{crop.title()}: sow {i['sow']}; harvest {i['harvest']}; water {i['water']}; soil {i['soil']}."

if __name__ == "__main__":
    mcp.run(transport="streamable-http")  # endpoint: http://localhost:8000/mcp