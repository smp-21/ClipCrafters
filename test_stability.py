import os
import asyncio
import aiohttp
from dotenv import load_dotenv

async def test_stability():
    load_dotenv()
    api_key = os.getenv("STABILITY_API_KEY")
    if not api_key or api_key == "your_stability_api_key_here":
        print("Error: STABILITY_API_KEY is not set or is still a placeholder.")
        return

    url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"
    headers = {
        "authorization": f"Bearer {api_key}",
        "accept": "image/*"
    }
    
    data = {
        "prompt": "A futuristic city with flying cars, cinematic educational style, high detail",
        "output_format": "jpeg",
        "model": "sd3-large-turbo"
    }

    print(f"Testing Stability.ai API with prompt: {data['prompt']}")
    
    form = aiohttp.FormData()
    for key, value in data.items():
        form.add_field(key, value)

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url, data=form) as response:
                if response.status == 200:
                    image_data = await response.read()
                    output_path = "test_stability_output.jpg"
                    with open(output_path, "wb") as f:
                        f.write(image_data)
                    print(f"Success! Image saved to {output_path}")
                else:
                    error_text = await response.text()
                    print(f"Failed! Status: {response.status}, Error: {error_text}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(test_stability())
