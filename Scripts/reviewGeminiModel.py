import os
import sys
import requests
import json

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

PRIMARY_MODEL = "gemini-2.5-flash"
FALLBACK_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
]


def get_api_key():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable is not set.")
        print("   Example (bash): export GEMINI_API_KEY=\"your-real-api-key-here\"")
        sys.exit(1)
    return api_key


def try_model(api_key: str, model_name: str) -> bool:
    """
    Try calling generateContent on a given model.
    Returns True if the call succeeds (HTTP 200 and no 'error' in JSON).
    """
    url = f"{BASE_URL}/{model_name}:generateContent"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": "Reply with the word: OK"}
                ]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }

    print(f"\n--- Testing model: {model_name} ---")
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
    except requests.RequestException as e:
        print(f"HTTP error while calling {model_name}: {e}")
        return False

    print(f"HTTP status: {resp.status_code}")

    # Try to decode JSON
    try:
        data = resp.json()
    except json.JSONDecodeError:
        print("Non-JSON response:\n", resp.text[:300])
        return False

    # If API returned an error object
    if "error" in data:
        err = data["error"]
        print("API error:")
        print(" code   :", err.get("code"))
        print(" status :", err.get("status"))
        print(" message:", err.get("message"))
        return False

    # Success path: show a tiny bit of the model output
    try:
        text = data["candidates"][0]["content"]["parts"][0].get("text", "")
    except (KeyError, IndexError, TypeError):
        text = ""

    print("✅ Model call succeeded.")
    if text:
        print("Sample output:", repr(text[:80]))
    return True


def list_available_models(api_key: str):
    """Optional helper: list all models visible to this API key."""
    print("\nListing models visible to your API key...")

    url = f"{BASE_URL}"
    headers = {
        "x-goog-api-key": api_key,
    }

    try:
        resp = requests.get(url, headers=headers, timeout=30)
    except requests.RequestException as e:
        print("Could not list models:", e)
        return

    print("HTTP status (list models):", resp.status_code)

    try:
        data = resp.json()
    except json.JSONDecodeError:
        print("Non-JSON response:\n", resp.text[:300])
        return

    models = data.get("models", [])
    if not models:
        print("No models returned. Check project / region / permissions.")
        return

    print("Models available (names you can use after 'models/'):")
    for m in models:
        name = m.get("name", "")
        display = m.get("displayName", "")
        # name looks like "models/gemini-1.5-flash"
        model_str = name.split("/", 1)[-1] if "/" in name else name
        print(f" - {model_str} (display: {display})")


def main():
    api_key = get_api_key()

    print(f"Checking primary model: {PRIMARY_MODEL}")
    primary_ok = try_model(api_key, PRIMARY_MODEL)

    if primary_ok:
        print(f"\n✅ Using primary model: {PRIMARY_MODEL}")
        return

    print("\nPrimary model unavailable or not working.")
    print("Trying fallback models in order...\n")

    for model in FALLBACK_MODELS:
        if try_model(api_key, model):
            print(f"\n✅ Recommended model for you: {model}")
            break
    else:
        print("\n❌ None of the candidate models worked.")
        print("   Possible reasons:")
        print("   - Invalid or disabled API key")
        print("   - Gemini API not enabled for this project")
        print("   - Region/account doesn’t have access to these models")
        list_available_models(api_key)


if __name__ == "__main__":
    main()
