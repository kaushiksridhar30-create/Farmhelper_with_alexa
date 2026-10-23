# Farm Helper: MCP server for the Alexa+ track

Voice-first farming assistant exposed as an **MCP server** (spec 2025-11-25+, Streamable HTTP, Python). It includes a simulated Alexa+ web app that lets users ask by voice or text and hears the answer spoken back.

## MCP tools
- `diagnose_crop_disease(crop, symptoms)`: treatment advice from described symptoms (rule-based; AI-enhanced if AWS Bedrock is configured)
- `get_irrigation_advice(crop, city)`: water or skip, using live weather (Open-Meteo)
- `get_mandi_price(crop)`: market price per quintal (demo data)
- `get_crop_calendar(crop)`: sowing, harvest, water and soil guidance
- `diagnose_leaf_image(image_base64)`: optional leaf photo analysis, needs AWS Bedrock access

## Run locally
```
pip install -r requirements.txt
python server.py
```
- Simulated Alexa+ web app: http://localhost:8000/
- MCP endpoint (Streamable HTTP): http://localhost:8000/mcp
- Test the MCP tools: `python test_client.py` (in a second terminal)

Voice input works best in Chrome or Edge.

## Project layout
- `server.py`: MCP server (FastMCP) and demo API routes
- `static/index.html`: simulated Alexa+ web app
- `data/`: crop calendar and demo mandi prices
- `test_client.py`: MCP client that lists and calls the tools

## Built during the hackathon
Built from scratch during the hackathon window.

## License
MIT
