<<<<<<< HEAD
# Farm Helper MCP Server (Alexa+ track)
Voice-first farming assistant exposed as an MCP server (Streamable HTTP).

## Tools
- `diagnose_crop_disease(crop, symptoms)` - AWS Bedrock AI diagnosis (rule-based fallback)
- `get_irrigation_advice(crop, city)` - live weather via Open-Meteo
- `get_mandi_price(crop)` - market price (mock data)
- `get_crop_calendar(crop)` - sowing/harvest/water guidance

## Run
```
pip install -r requirements.txt
cp .env.example .env
python server.py          # http://localhost:8000/mcp
python test_client.py     # in a second terminal
```
## Deploy
Any host that runs Python (Render, Railway, EC2). Expose `/mnt`-free HTTPS URL ending in `/mcp`.
"# Farmhelper_with_alexa" 
=======
# Farmhelper_with_alexa
>>>>>>> 521ae8f265ee4d5a3c1115a43d7a8f809e40721b
