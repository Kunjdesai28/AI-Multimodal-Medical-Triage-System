import os
import json
import base64
import httpx

def test_vision():
    key = ""
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    key = line.strip().split("=", 1)[1]
                    break

    if not key:
        print("GEMINI_API_KEY not found in .env")
        return

    # Find sample image
    sample_img = None
    xray_base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "datasets", "xray_dataset"))
    for root, _, files in os.walk(xray_base):
        for file in files:
            if file.endswith((".png", ".jpg")):
                sample_img = os.path.join(root, file)
                break
        if sample_img:
            break

    if not sample_img:
        print("No image found in datasets/xray_dataset")
        return

    print(f"Testing Gemini Medical Vision on: {sample_img}")
    # Compress and resize for fast web transmission (<100KB)
    from PIL import Image
    import io
    pil_img = Image.open(sample_img).convert("RGB")
    pil_img.thumbnail((512, 512))
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=85)
    b64_data = base64.b64encode(buf.getvalue()).decode("utf-8")
    print(f"Compressed payload size: {len(b64_data) / 1024:.1f} KB")

    prompt = (
        "You are an expert emergency medicine diagnostic triage AI system.\n"
        "Analyze this medical image (which could be a Chest X-ray, Head CT, Bone X-ray, Ultrasound, or Clinical Trauma Photo).\n"
        "Return ONLY a valid JSON object matching this schema:\n"
        "{\n"
        '  "modality": "Detected imaging modality and anatomic body part",\n'
        '  "anatomical_region": "Anatomical region",\n'
        '  "is_abnormal": true or false,\n'
        '  "primary_findings": ["string list of detected radiological abnormalities"],\n'
        '  "emergency_severity": "CRITICAL" | "HIGH" | "MODERATE" | "LOW",\n'
        '  "abnormality_score": float between 0.0 and 1.0,\n'
        '  "clinical_rationale": "Clear, concise medical rationale of the observed visual signs",\n'
        '  "triage_recommendations": "Immediate emergency recommendation"\n'
        "}"
    )

    candidate_models = [
        "gemini-2.5-flash-image",
        "gemini-3.1-flash-image",
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-flash-latest",
        "gemini-2.5-pro"
    ]

    for model_name in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": b64_data
                        }
                    }
                ]
            }],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1
            }
        }

        try:
            print(f"Trying model: {model_name}...")
            resp = httpx.post(url, json=payload, timeout=25.0)
            if resp.status_code == 200:
                result = resp.json()
                raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(raw_text)
                print(f"SUCCESS with {model_name}!")
                print("STRUCTURED MEDICAL TRIAGE REPORT:")
                print(json.dumps(parsed, indent=2))
                return
            else:
                print(f"  {model_name} status {resp.status_code}: {resp.text[:120]}")
        except Exception as e:
            print(f"  {model_name} error: {e}")

if __name__ == "__main__":
    test_vision()
