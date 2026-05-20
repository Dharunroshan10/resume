import json
import os
import re
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler


GEMINI_MODELS = [
    model.strip()
    for model in os.environ.get(
        "GEMINI_MODELS",
        "gemini-2.5-flash,gemini-2.0-flash,gemini-1.5-flash-latest,gemini-1.5-flash",
    ).split(",")
    if model.strip()
]


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            resume_text = str(payload.get("resumeText", "")).strip()
            role = str(payload.get("role", "")).strip()

            if not resume_text:
                self._json_response({"error": "Resume text is required."}, 400)
                return

            api_key = os.environ.get("GEMINI_API_KEY", "").strip()
            if not api_key:
                self._json_response({"error": "GEMINI_API_KEY is not configured in Vercel."}, 500)
                return

            result = analyze_with_gemini(api_key, resume_text, role)
            self._json_response(result)
        except Exception as exc:
            self._json_response({"error": str(exc)}, 500)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def _json_response(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def analyze_with_gemini(api_key, resume_text, role):
    prompt = f"""
You are an expert resume reviewer and ATS optimizer.

Analyze this resume for the target role: {role}.

Return ONLY valid JSON with this exact schema:
{{
  "score": 0,
  "reason": "short reason",
  "strengths": ["3 to 5 items"],
  "weaknesses": ["exactly 5 direct mistakes"],
  "missing": ["ATS keywords missing"],
  "tips": ["3 role-based improvement tips"],
  "summary": "better professional summary",
  "improved": "one clean improved resume draft as plain text",
  "matchedJobSkills": ["best skills found or recommended for job search"]
}}

Rules:
- Score must be 0 to 100.
- Keep advice specific and practical for job seekers.
- Do not invent exact company names, degrees, phone numbers, or dates.
- For improved resume text, use placeholders where the candidate must fill missing details.
- matchedJobSkills should contain 4 to 7 concise job-search keywords.

Resume:
{resume_text[:12000]}
""".strip()

    request_body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.35,
            "responseMimeType": "application/json",
        },
    }

    data = None
    errors = []
    for model in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        request = urllib.request.Request(
            url,
            data=json.dumps(request_body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                data = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            errors.append(f"{model}: {details}")

    if data is None:
        raise RuntimeError(f"Gemini request failed for all configured models: {' | '.join(errors)}")

    text = data["candidates"][0]["content"]["parts"][0]["text"]
    parsed = parse_json_object(text)
    return normalize_result(parsed, role)


def parse_json_object(text):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    match = re.search(r"\{.*\}", cleaned, re.S)
    if not match:
        raise ValueError("Gemini did not return JSON.")
    return json.loads(match.group(0))


def normalize_result(data, role):
    def as_list(key, limit):
        value = data.get(key, [])
        if isinstance(value, str):
            value = [value]
        value = [str(item).strip() for item in value if str(item).strip()]
        return value[:limit]

    score = int(data.get("score", 0))
    score = max(0, min(100, score))
    matched_skills = as_list("matchedJobSkills", 7)
    if not matched_skills:
        matched_skills = [role, "resume", "hiring"]

    return {
        "score": score,
        "reason": str(data.get("reason", "AI resume analysis completed.")).strip(),
        "strengths": as_list("strengths", 5),
        "weaknesses": as_list("weaknesses", 5),
        "missing": as_list("missing", 10),
        "tips": as_list("tips", 5),
        "summary": str(data.get("summary", "")).strip(),
        "improved": str(data.get("improved", "")).strip(),
        "matchedJobSkills": matched_skills,
        "source": "gemini",
    }
