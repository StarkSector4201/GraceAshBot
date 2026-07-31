# --- APPLY COMMAND DATA ---
# Grace Ashcroft Bot - Application System

APPLY_INTRO = """📋 **Group Application — Grace Ashcroft Bot**
━━━━━━━━━━━━━━━━━━━━━
Hello. I'm Grace Ashcroft.

To join this group, please complete a short application.
Answer honestly — the results are reviewed by the team.

I'll ask a few questions. Select your answer for each one.
_— This won't take long._"""

# Questions format: list of dicts with {"question": str, "options": list[str]}
# If no "options" key, it's an open text question (user types their answer)
APPLY_QUESTIONS = [
    {
        "question": "1️⃣ How old are you?",
        "options": ["18-24", "25-34", "35-44", "45+"]
    },
    {
        "question": "2️⃣ How did you hear about this group?",
        "options": ["Friend / Referral", "Social media", "Search", "Other"]
    },
    {
        "question": "3️⃣ Do you have a computer (laptop or desktop)?",
        "options": ["Yes", "No", "Other device"]
    },
    {
        "question": "4️⃣ What are your technical skills?",
        "options": ["Programming / IT", "Design / Editing", "Marketing", "None / Other"]
    },
    {
        "question": "5️⃣ Why do you want to join this group?",
        "options": ["Learn something new", "Earn / Collaborate", "Support the community", "Just curious"]
    },
    {
        "question": "6️⃣ How many hours per day are you active online?",
        "options": ["< 1 hour", "1-2 hours", "3-5 hours", "5+ hours"]
    },
    {
        "question": "7️⃣ Can you commit to contributing regularly?",
        "options": ["Yes, definitely", "I'll try my best", "Maybe", "No"]
    },
    {
        "question": "8️⃣ What kind of support can you offer the group?",
        "options": ["Content creation", "Ideas & feedback", "Promotion", "Financial support", "Other"]
    },
    {
        "question": "9️⃣ Are you interested in AI tools and technology?",
        "options": ["Very interested", "Somewhat", "Not really", "No"]
    },
    {
        "question": "🔟 Any final notes or comments for the team? (type your answer)",
    },
]
