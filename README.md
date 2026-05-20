# AI Resume Roast + Fixer

A modern, high-contrast AI-powered resume optimizer that roasts your resume and provides one-click improvements using Gemini AI.

## Features

- **AI Analysis:** Get an instant score and detailed feedback on your resume.
- **Electric Red Theme:** High-contrast design with glassmorphism and modern typography.
- **ATS Optimization:** Identifies missing keywords and suggests improvements.
- **Dynamic Visualization:** Interactive score gauge and progress bars.
- **Role-Based Tips:** Custom advice tailored to your target job role.
- **One-Click Improved Resume:** Generates an optimized version of your resume text.
- **Job Search Integration:** Quick links to job search engines based on detected skills.
- **Multi-Format Support:** Paste text or upload PDF, Image (OCR), or Text files.

## Tech Stack

- **Frontend:** Vanilla JavaScript, CSS (Modern Glassmorphism), HTML5
- **Backend:** Python (BaseHTTPRequestHandler)
- **AI Model:** Google Gemini (1.5 Flash / 2.0 Flash)
- **Libraries:**
  - `Tesseract.js` for Image OCR
  - `pdf.js` for PDF text extraction

## Deployment

This project is configured for easy deployment on **Vercel**.

1. Push to your GitHub repository.
2. Connect the repository to Vercel.
3. Add the following Environment Variables in Vercel:
   - `GEMINI_API_KEY`: Your Google AI Studio API key.
   - `GEMINI_MODELS` (Optional): Comma-separated list of Gemini models to try.

## Local Development

Run the server locally:

```bash
python server.py
```

The app will be available at `http://127.0.0.1:8010/`.
