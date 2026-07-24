"""Test script to list available Gemini models and test generation"""
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("ERROR: GOOGLE_API_KEY not found in .env file")
    exit(1)

try:
    client = genai.Client(api_key=GOOGLE_API_KEY)
    print("✓ Successfully connected to Google Generative AI API\n")
    print("=" * 80)
    print("LISTING ALL AVAILABLE MODELS:")
    print("=" * 80)
    
    models = client.models.list()
    generation_models = []
    
    for model in models:
        print(f"\n📦 Model: {model.name}")
        if hasattr(model, 'display_name'):
            print(f"   Display Name: {model.display_name}")
        
        # All listed models should support generation in the new SDK
        generation_models.append(model.name)
        print(f"   ✅ Available for use")
    
    print("\n" + "=" * 80)
    print(f"TOTAL MODELS FOUND: {len(generation_models)}")
    print("=" * 80)
    for model_name in generation_models:
        print(f"✓ {model_name}")
    
    # Test generation with the first available model
    if generation_models:
        test_model = generation_models[0]
        print(f"\n" + "=" * 80)
        print(f"TESTING GENERATION WITH: {test_model}")
        print("=" * 80)
        
        response = client.models.generate_content(
            model=test_model,
            contents="Say 'Hello, World!' in one sentence.",
            config={
                "temperature": 0.7,
                "max_output_tokens": 50
            }
        )
        
        print(f"✓ Test successful!")
        print(f"Response: {response.text}")
        
        print(f"\n💡 RECOMMENDED: Update your .env file with:")
        print(f"   GEMINI_MODEL_NAME={test_model}")
    else:
        print("\n❌ No models available!")
            
except Exception as e:
    import traceback
    print(f"\n❌ ERROR: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
