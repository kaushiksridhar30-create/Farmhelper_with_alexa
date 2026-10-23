import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    async with streamablehttp_client("http://localhost:8000/mcp") as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            print("Tools:", [t.name for t in (await s.list_tools()).tools])
            for name, args in [("get_crop_calendar", {"crop": "tomato"}),
                               ("get_mandi_price", {"crop": "ragi"}),
                               ("diagnose_crop_disease", {"crop": "tomato", "symptoms": "yellow leaves with brown spots"})]:
                print(name, "->", (await s.call_tool(name, args)).content[0].text)
asyncio.run(main())
