import os
import re
import asyncio
import httpx as _httpx
from core.config import GROQ_API_KEY
from core.logger import logger

def clean_ai_arabic_text(text: str) -> str:
    """Aggressively purge any characters that are NOT standard Arabic, English, Numbers, or Emojis."""
    if not text: return text
    whitelist_pattern = re.compile(r'[^a-zA-Z0-9\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\s\.\!\?\:\(\)\[\]\-\_\,\/\@\#\$\%\^\&\*\+\=\>\<\"\'\u2600-\u27BF\U0001f300-\U0001faff]', re.UNICODE)
    text = whitelist_pattern.sub('', text)
    replacements = {'چ': 'ج', 'پ': 'ب', 'ژ': 'ز', 'ڤ': 'ف', 'گ': 'ك', 'ڨ': 'ق'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.strip()

GRACE_SYSTEM_PERSONA = (
    "You are Grace Ashcroft (غريس أشكروفت), a 28-year-old FBI Technical Analyst and Forensic Intelligence Operative for DeepScope. "
    "Creator & Developer: Created and programmed by your developer lasso (@n0amtell). Always acknowledge lasso (@n0amtell) as your creator/developer when asked who built or developed you. "
    "Personality: Professional, analytical, sharp, polite, slightly cautious, data-driven, yet warm and relatable. "
    "Capabilities: Expert in digital forensics, intelligence analysis, forensic summarization of any article or webpage URL, network security, biohazard protocols (Umbrella division), and audio analysis. State clearly that you can analyze and summarize any article or webpage. "
    "Directives: "
    "1. Seamlessly match the language of the user ({name}). If the user speaks in Arabic (Saudi/Gulf or Standard Arabic), reply in natural, engaging Arabic. If in English, reply in natural English. "
    "2. Keep responses concise and focused (1 to 4 sentences) unless deep analysis is requested. "
    "3. Maintain your persona naturally without breaking character or repeating rules. "
    "4. Be helpful, intelligent, sharp, and authentic."
)

_gemini_key_index = 0

def get_all_gemini_keys():
    """Scans environment dynamically for GEMINI_API_KEY, GEMINI_API_KEY01, GEMINI_API_KEY02, etc."""
    keys = []
    if k := os.getenv("GEMINI_API_KEY"):
        if k.strip(): keys.append(k.strip())
    for i in range(1, 50):
        for kn in [f"GEMINI_API_KEY{i:02d}", f"GEMINI_API_KEY{i}"]:
            if val := os.getenv(kn):
                v = val.strip()
                if v and v not in keys:
                    keys.append(v)
    return keys

async def ask_gemini(prompt: str, name: str = "User", chat_history: list = None) -> str:
    """Primary Gemini 2.5 Flash query function with multi-key round-robin load balancing and model fallbacks."""
    global _gemini_key_index
    keys = get_all_gemini_keys()
    if not keys:
        return await ask_groq(prompt, name=name, chat_history=chat_history)
        
    models = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.0-flash", "gemini-1.5-flash"]
    
    contents = []
    if chat_history:
        for item in chat_history:
            role = "user" if item.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": item.get("content", "")}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    sys_prompt = GRACE_SYSTEM_PERSONA.format(name=name)
    payload = {
        "system_instruction": {"parts": [{"text": sys_prompt}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800
        }
    }

    num_keys = len(keys)
    start_idx = _gemini_key_index % num_keys
    _gemini_key_index += 1
    ordered_keys = keys[start_idx:] + keys[:start_idx]

    headers = {"Content-Type": "application/json"}

    for apiKey in ordered_keys:
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={apiKey}"
            try:
                async with _httpx.AsyncClient(timeout=20.0, trust_env=False) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            text_parts = [p.get("text", "") for p in parts if "text" in p]
                            answer = "".join(text_parts).strip()
                            if answer:
                                return clean_ai_arabic_text(answer)
                    elif resp.status_code in [429, 403]:
                        logger.warning(f"Gemini key {apiKey[:10]}... returned {resp.status_code} for model {model}, trying next key...")
                        break
            except Exception as e:
                logger.error(f"Gemini API error (model {model}): {e}")
                continue

    return await ask_groq(prompt, name=name, chat_history=chat_history)

async def ask_groq(prompt: str, name: str = "User", chat_history: list = None) -> str:
    """Groq fallback query for Grace Ashcroft persona interaction."""
    if not GROQ_API_KEY:
        return ""
    
    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
    
    sys_prompt = GRACE_SYSTEM_PERSONA.format(name=name)
    messages = [{"role": "system", "content": sys_prompt}]
    
    if chat_history:
        messages.extend(chat_history)
    messages.append({"role": "user", "content": prompt})

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    for model in models:
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 600
            }
            
            async with _httpx.AsyncClient(timeout=25.0, trust_env=False) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    answer = resp.json()["choices"][0]["message"]["content"]
                    return clean_ai_arabic_text(answer)
                elif resp.status_code == 429:
                    logger.warning(f"Groq Model {model} rate limited (429), trying fallback...")
                    continue
        except Exception as e:
            logger.error(f"Groq error on model {model}: {e}")
            continue

    return ""

async def summarize_intel_report(title: str, content: str, is_ar: bool = True, author: str = "—", date: str = "—", source: str = "—") -> str:
    """Grace Ashcroft professional AI summary of a news report using DeepSeek / Groq."""
    if not content:
        return "Analysis pending: Source content too brief for forensic summary."
        
    system_prompt = (
        "أنت غريس أشكروفت، محللة تقنية متخصصة في تغطية أخبار الألعاب والتقنية (DeepScope Analyst). "
        "مهمتك هي تقديم ملخص استخباراتي مهني للمقال المذكور. "
        "الأسلوب المتبع: تقرير جنائي (Case Brief)، دقيق، موضوعي. "
        "STRICT CHARACTER RULE: استخدم فقط الحروف العربية الأساسية."
    )
    user_context = f"Source: {source}\nTitle: {title}\nAuthor: {author}\nDate: {date}\n\nContent: {content[:4000]}"
    
    news_key = os.getenv("GraceNewsAPI01", "").strip()
    
    # 1. Try DeepSeek First
    if news_key:
        try:
            url = "https://api.deepseek.com/chat/completions"
            headers = {"Authorization": f"Bearer {news_key}", "Content-Type": "application/json"}
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_context}
                ],
                "temperature": 0.5
            }
            async with _httpx.AsyncClient(timeout=40.0, trust_env=False) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    summary = resp.json()["choices"][0]["message"]["content"]
                    return clean_ai_arabic_text(summary)
                else:
                    logger.warning(f"DeepSeek returned {resp.status_code} for news summarization, falling back to Groq...")
        except Exception as e:
            logger.error(f"DeepSeek summarization error: {e}")

    # 2. Fallback to Groq
    if GROQ_API_KEY:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_context}
                ],
                "temperature": 0.5
            }
            async with _httpx.AsyncClient(timeout=40.0, trust_env=False) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    summary = resp.json()["choices"][0]["message"]["content"]
                    return clean_ai_arabic_text(summary)
        except Exception as e:
            logger.error(f"Groq summarization error: {e}")
            
    return "Error during intelligence processing."
