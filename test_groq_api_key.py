"""
Test script to verify your Groq API key and available models
Run this before using the main app to troubleshoot any issues
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()


def test_groq_api():
    """Test Groq API key and list available models"""

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("❌ ERROR: GROQ_API_KEY not found in .env file")
        print("📝 Create a .env file with: GROQ_API_KEY=your_api_key_here")
        print("🔗 Get API key from: https://console.groq.com/")
        return False

    print(f"🔑 Testing API key: {api_key[:8]}...")

    # Test 1: List available models
    print("\n📋 Testing model list...")
    try:
        url = "https://api.groq.com/openai/v1/models"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            models = response.json()
            print("✅ API key works! Available models:")
            for model in models.get('data', []):
                print(f"   • {model['id']}")
        else:
            print(f"❌ API key test failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

    # Test 2: Try a simple chat completion
    print("\n🤖 Testing chat completion...")
    try:
        chat_url = "https://api.groq.com/openai/v1/chat/completions"

        # Try the recommended model first
        test_models = [
            'llama-3.3-70b-versatile',
            'llama-3.1-8b-instant',
            'llama3-70b-8192',
            'gemma2-9b-it'
        ]

        for model in test_models:
            print(f"   Testing model: {model}")

            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Say 'Hello World'"}],
                "temperature": 0.1,
                "max_tokens": 50
            }

            response = requests.post(
                chat_url, headers=headers, json=payload, timeout=15)

            if response.status_code == 200:
                result = response.json()
                message = result['choices'][0]['message']['content']
                print(f"   ✅ {model}: {message.strip()}")
                print(
                    f"\n🎉 SUCCESS! Use MODEL_NAME = '{model}' in your config.py")
                return True
            else:
                print(
                    f"   ❌ {model}: {response.status_code} - {response.text[:100]}")

        print("❌ All models failed. Check your API key or try again later.")
        return False

    except Exception as e:
        print(f"❌ Error testing chat: {e}")
        return False


if __name__ == "__main__":
    print("🔧 Groq API Test Script")
    print("=" * 50)

    success = test_groq_api()

    if success:
        print("\n✅ All tests passed! Your Groq API setup is working.")
        print("🚀 You can now run: streamlit run main.py")
    else:
        print("\n❌ Tests failed. Please check your setup:")
        print("1. Get API key from: https://console.groq.com/")
        print("2. Add to .env file: GROQ_API_KEY=your_key_here")
        print("3. Run this test again: python test_groq_api.py")
