# -*- coding: utf-8 -*-

# --- GRACE ASHCROFT PERSONA PHRASES ---
# Extracted for structural modularity and maintenance.

PHRASES = {
    "english": {
        "welcome":      "Oh— um, hello. Welcome. I'm... glad you made it here safely. Please read the rules when you get a chance. 📋",
        "bye":          "Oh. They're gone. I... hope they're okay. Take care out there. It's dangerous.",
        "rules_header": "📋 Group Rules — I, um, actually read these carefully so...",
        "warn":         "⚠️ {name}. I've... logged this incident. Please reconsider your actions. This is warning #{count}.",
        "muted":        "🔇 {name} has been temporarily restricted. {time} minutes. I didn't want to do this but... the data supports it.",
        "kicked":       "👢 {name} has been removed from the group. I've filed the report. Stay safe out there.",
        "banned":       "🚫 {name}. Permanent ban executed. I... I'm sorry it came to this.",
        "no_rules":     "No specific rules on record yet. But, um, basic decency is always appreciated. 📝",
        "welcome_set":  "✅ Welcome message updated. I'll make sure it's... warm enough.",
        "rules_set":    "✅ Rules saved to the database. Members should review them.",
        "dialect_set":  "✅ Language mode set to {dialect}.",
        "not_admin":    "❌ Um, sorry — this command requires admin permissions. I can't help you bypass that.",
        "bot_added":    "Oh! Hello— I'm Grace. I'm a... bot. I handle group moderation and welcoming. I'll do my best. 📋",
        "promoted":     "⬆️ {name} has been promoted to admin. Please use the permissions responsibly.",
        "demoted":      "⬇️ {name}'s admin permissions have been revoked. It's logged.",
        "link_blocked": "🔗 {name}, that link has been removed. Links aren't permitted here.",
        "mention_1": "Um— yes? Did you need something? 📋",
        "mention_2": "Oh, you said my name. I'm... here. What do you need?",
        "mention_3": "You called? I'm listening. 👀",
        "identity_1": "I'm Grace Ashcroft. FBI Technical Analyst — or... well, I was. Now I'm a specialized Intelligence Operative.\n\nI handle welcomes, moderation, and **forensic article & webpage URL summarization**. I'm not a field agent. I work better with data than with, um... confrontations.\n_— Developed by lasso (@n0amtell) 📋_",
        "identity_2": "Grace Ashcroft. Analyst. I investigate things, apply logical frameworks to problems, and perform deep forensic analysis & summaries for any article or webpage link.\n\nAs a bot I can: summarize any article or webpage URL, welcome members, moderate violations, run captchas... the usual things an FBI analyst would do if she were a Telegram bot.\n_There's nothing special about me. I just... try not to let people down._ 📋",
        "bored_1": "Oh. Um... have you tried `/gumbrella`? It's... statistically interesting. ☣️",
        "bored_2": "Bored? That's... I get that. Maybe `/gumbrella` would help? I can't promise it will go well though. 😅",
        "bored_3": "I usually re-read case files when I'm bored. But if you prefer something interactive... `/gumbrella`? ☣️",
        "photo_1": "...You asked. Here. 📋",
        "photo_2": "...Here. Don't make it weird. 📋",
        "photo_missing": "I... don't have an image file set up. (grace.jpg missing)",
        "rl_menu_body": "🧤 **Russian Roulette — Risk Assessment**\n━━━━━━━━━━━━━━━━━━━━━\nSubject: {name}\nStatus: Requesting manual trigger.\n\nSelect the number of loaded chambers (1-6). Statistical risk increases with each addition. _Choose wisely._",
        "rl_btn_1": "1 Bullet (Low)",
        "rl_btn_2": "2 Bullets",
        "rl_btn_3": "3 Bullets",
        "rl_btn_4": "4 Bullets",
        "rl_btn_5": "5 Bullets (EXTREME)",
        "rl_frame_1": "🔄 Spinning the cylinder...",
        "rl_frame_2": "⚙️ Aligning chambers...",
        "rl_frame_3": "🔨 Trigger tensioning...",
        "rl_frame_4": "⌛ Probability calculation complete. Resulting...",
        "rl_result_dead": "💥 **BANG.**\n\n{name} was the outlier. Statistical outcome: {bullets} in 6.\n🔇 **Restriction Applied**: {time} minutes.\n📈 Streak reset to 0.\n\n_I... I cautioned you about the data._",
        "rl_result_survive": "🔫 *click* ...\n\n{name} survives. Probability was {prob}.\n🔥 **Current Streak**: {streak}\n🏆 **Highest Streak**: {max_streak}\n\n_A relief. Please, consider stopping while the math is in your favor._",
        "guide_main":  "🧤 **Grace Ashcroft — Field Support Interface**\n━━━━━━━━━━━━━━━━━━━━━\n**Status:** `ONLINE (v1.5)`\n**Role:** Forensic Technical Analyst — _DeepScope Mode_\n\nHello. I'm configured for group logic, AI neural intelligence, forensic article & webpage URL summarization, and multi-node intelligence feeds.\n\n**Please select a protocol to review:**",
        "btn_members": "👥 Members",
        "btn_admins":  "👮 Admins",
        "btn_about":   "🔍 System Intel",
        "btn_back":    "🔙 Back to Menu",
        "guide_members": (
            "👥 **Members**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "▸ `/ggai` — AI Neural control panel\n"
            "▸ `/gapply` — Submit a join application\n"
            "▸ `/gumbrella` — Umbrella roulette ☣️\n"
            "▸ `/grules` — View group rules\n"
            "▸ `/gabout` — Learn about me\n"
            "▸ `/gstatus` — Check if I'm online\n"
            "▸ `/ghelp` — Full command list\n\n"
            "_No special permissions required._ 📋"
        ),
        "guide_admins": (
            "👮 **Admins**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "▸ `/gkick` — Remove member temporarily\n"
            "▸ `/gmute [minutes]` — Restrict a member\n"
            "▸ `/gwarn` — Warning (3 = auto-mute 8h)\n"
            "▸ `/gpromote` / `/gdemote` — Manage admins\n"
            "▸ `/gban` — Permanent ban\n"
            "▸ `/gstats` — Group statistics\n"
            "▸ `/ginfo` — Member info & warnings\n"
            "▸ `/gclearchat` — Bulk delete messages\n\n"
            "**Control Center:**\n"
            "▸ `/glock` / `/gunlock` — Global control\n"
            "▸ `/gnewsctl` — Intelligence feed control\n"
            "▸ `/gnewssrc` — Source management"
        ),
        "guide_about": (
            "🔍 **System Metadata**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "I'm **Grace Ashcroft** 📋\n"
            "Technical Analyst. Forensic Data Investigator.\n"
            "Managed exclusively by **lasso (@n0amtell)**\n\n"
            "**Active Subsystems:**\n"
            "▸ 🤖 AI Neural Engine\n"
            "▸ 📄 Forensic Article & Webpage URL Summarization\n"
            "▸ 📡 DeepScope Intelligence Feed\n"
            "▸ 🛡️ Multi-layer security filters\n"
            "▸ 📝 Regulated join applications\n"
            "▸ 🤖 Human verification (Captcha)\n"
            "▸ 💬 Dialect-aware interaction (`/glang`)\n\n"
            "_I process the data to ensure operational integrity._\n"
            "_— Private Build [v1.5] 📋_"
        ),
        "help_msg": (
            "📋 **Grace Ashcroft** — _Interface Protocol_\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Classification: **Intelligence Analyst (v1.5)**\n\n"
            "⭐ **Administrative Protocols**\n"
            "▸ `/ggai` `/glock` `/gunlock` `/gnewsctl` `/gnewssrc`\n"
            "▸ `/gcleanservice` `/glinkfilter` `/gcaptcha`\n"
            "▸ `/gsetwelcome` `/gsetrules` `/glang`\n\n"
            "👮 **Moderation Tools**\n"
            "▸ `/gkick` `/gmute [mins]` `/gwarn`\n"
            "▸ `/gpromote` `/gdemote` `/gadmins`\n"
            "▸ `/gstats` `/ginfo` `/gclearchat`\n\n"
            "👥 **Member Utilities**\n"
            "▸ `/ggai` `/gapply` `/groulette` `/gumbrella`\n"
            "▸ `/grules` `/gabout` `/gstatus` `/ghelp`\n\n"
            "   _Grace is standing by for forensic analysis._"
        ),
        "about_msg": (
            "📋 **Grace Ashcroft — Field Report**\n"
            "_Classification: Non-combat operative_\n\n"
            "✨ **Capabilities Snapshot:**\n"
            "🤖 `/ggai` — AI Neural Intelligence & Article Summarization.\n"
            "🛡️ `/gban` — Permanent revocation of access.\n"
            "📡 `/gnews` — DeepScope Intelligence Feed.\n"
            "🧹 `/gcleanservice` — Service message suppression.\n"
            "📝 `/gapply` — Membership application system.\n\n"
            "**Report Ends.**\nManaged exclusively by:\n"
            "**lasso (@n0amtell)**\n\n"
            "_Private Build v1.5 — Grace Ashcroft 📋_"
        ),
        "status_msg": "Systems operational. All hardware & subsystem metrics normal. ✅ _— Grace_",
        "music_hint": (
            "🎵 **Grace Ashcroft — Multi\\-Node Acquisition System**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Provide a song name or a link \\(SoundCloud/Anghami/YouTube\\)\\.\n\n"
            "**Examples:**\n"
            "▸ `/gmusic Blinding Lights The Weeknd`\n"
            "▸ `/gmusic Amr Diab Tamally Maak`\n\n"
            "_I'll scan the global archives for a match\\._ 📋"
        ),
        "music_cooldown": "⏳ `Wait {time}s before next request\\.`\n_System bandwidth must be preserved\\. — Grace_ 📋",
        "music_active":   "⚠️ `Active download already in progress\\.`\n_Please wait for current acquisition to finish\\._ 📋",
        "music_node_engine": "🎵 **Grace Ashcroft — Multi\\-Node Engine**",
        "music_scan_init":   "📡 **Initialising Multi\\-Node Scan\\.\\.\\.**\n_Connecting to high\\-fidelity data streams_",
        "music_finalised":   "🎵 **Grace Ashcroft — Recovery Finalised**",
        "music_initiating_upload": "📤 **Initiating secure upload\\.\\.\\.**\n_Delivering audio payload to target chat_",
        "music_flood_wait": "🕒 `Flood control on Audio Upload\\. Waiting {time}s\\.\\.\\.`",
        "music_footer_1": "Analyzing frequencies\\.\\.\\.",
        "music_footer_2": "Optimising bitstream\\.\\.\\.",
        "music_fault":   "💥 **System fault during acquisition\\.**\n_Major error logged\\._ 📋",
        "music_no_match": (
            "❌ **Track not found in database\\.**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🔎 `Query: {query}`\n"
            "{proxy}\n\n"
            "_I've exhausted all mirrors \\(SoundCloud/YT Music\\)\\. No match found\\.\n"
            "Try a different spelling or include artist name\\._"
        ),
        "music_blocked": (
            "⚠️ **Pipeline acquisition failure\\.**\n"
            "{proxy}\n\n"
            "_The provider is aggressively blocking our IP or the format is incompatible\\. Error logged\\._ 📋"
        ),
        "music_too_large": (
            "⚠️ **Payload too large for transmission\\.**\n"
            "_File size exceeds 50MB limit\\. Transmission aborted\\._ 📋"
        ),
        "music_ffmpeg_missing": (
            "❌ **System configuration error\\.**\n"
            "_`ffmpeg` is missing from the host machine\\. Acquisition cannot proceed\\._"
        ),
        "music_caption": (
            "🎵 *{title}*\n"
            "🎤 `{performer}`\n"
            "💿 `{album}`\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🎧 Resolution: 320 kbps \\(Max\\)\n"
            "📁 Package: {size} MB\n\n"
            "_Grace Ashcroft Forensic Music Recovery_ 📋"
        ),
        "music_frames": [
            "📡 **Scanning Multi\\-Node Archives\\.\\.\\.**",
            "🔐 **Unlocking Secure Link Protocol\\.\\.\\.**",
            "📥 **Acquiring high\\-fidelity audio stream\\.\\.\\.**",
            "🎼 **Encoding bitstream · 192 kbps\\.\\.\\.**",
            "🔬 **Executing final integrity check\\.\\.\\.**",
        ],
        "umbrella_intro": "🧤 **Umbrella Corporation — Roulette Protocol**\n━━━━━━━━━━━━━━━━━━━━━\n**Host:** `Grace Ashcroft` (Analyst)\n**Subject:** {name}\n\n_The wheel is active... Proceed with caution._",
        "umbrella_spinning": "🔄 **Rotating Umbrella Roulette Wheel...**",
        "umbrella_placeholder": "⚠️ **This category is not available at the current moment.**",
        "umbrella_fact_header": "🟣 **Category: FACT (Truth)**\n━━━━━━━━━━━━━━━━━━━━━\n👤 **Subject:** `{name}`\n_Verification required from the subject._\n\n",
        "umbrella_react_q5_yes": "Oh... congratulations on your death in advance. 😭",
        "umbrella_react_q5_no": "A wise choice. Natural immunity is... well, more predictable. 📋",
        "umbrella_fact_q1": "What would you rate your attractiveness out of 10?",
        "umbrella_fact_q2": "What is your favorite animal?",
        "umbrella_fact_q3": "Chicken or Meat?",
        "umbrella_fact_q4": "Are you female or male?",
        "umbrella_fact_q5": "Did you take the COVID-19 vaccine?",
        "umbrella_fact_q6": "You're diagnosed with Alzheimer's; the cure is a yearly injection that lets you remember only 3 things. What would they be?",
        "umbrella_fact_q7": "You have one week to live. No cure. Who is the first person you'd want to spend that time with?",
        "umbrella_fact_q8": "Light or Darkness?",
        "umbrella_fact_q9": "A black cat is following you persistently in the street. What do you do?",
        "umbrella_fact_q10": "In a T-Virus outbreak, your loved one turns into a zombie. How do you act?",
        "umbrella_btn_q9_1": "Adopt it",
        "umbrella_btn_q9_2": "Step on its tail",
        "umbrella_btn_q9_3": "Feed and pet it",
        "umbrella_btn_q9_4": "Freeze in place",
        "umbrella_btn_q10_1": "Shoot them in the head",
        "umbrella_btn_q10_2": "Run away",
        "umbrella_btn_q10_3": "Lock them in a room",
        "umbrella_btn_q10_4": "Let them bite me so we become one",
        "umbrella_btn_q10_5": "Do the impossible to find a cure",
        "umbrella_fact_q11": "What scares you the most in the world?",
        "umbrella_fact_q12": "If you became a zombie, who is the first person you'd want to bite?",
        "umbrella_fact_q13": "Coffee or tea? And how do you drink it?",
        "umbrella_fact_q14": "What is the most beautiful memory in your life?",
        "umbrella_fact_q15": "If you had a bomb and could detonate it in one place, where would you throw it?",
        "umbrella_fact_q16": "Do you get jealous easily or do you not care?",
        "umbrella_fact_q17": "If you could go back in time, which year would you go back to and what would you do?",
        "umbrella_fact_q18": "Who do you love the most in your family?",
        "umbrella_fact_q19": "Do you prefer sleeping early or late?",
        "umbrella_fact_q20": "If Umbrella offered you a high-ranking position but you had to give up what you cherish most, would you agree?",
        "umbrella_fact_q21": "What song do you listen to the most when you're sad?",
        "umbrella_fact_q22": "If you had a superpower for one day, what is the first thing you'd do?",
        "umbrella_fact_q23": "Do you prefer the cold or heat?",
        "umbrella_fact_q24": "What is the biggest lie you've ever told?",
        "umbrella_fact_q25": "If someone were reading your mind right now, what would they know about you?",
        "umbrella_fact_q26": "Do you like brutal honesty or sugar-coated words?",
        "umbrella_fact_q27": "Where is the most beautiful place you've ever visited?",
        "umbrella_fact_q28": "If you were stranded alone on an island, what are the first three things you'd take with you?",
        "umbrella_fact_q29": "What are your thoughts on love at first sight?",
        "umbrella_fact_q30": "Are you a vengeful person or do you forgive quickly?",
        "umbrella_fact_q31": "If Umbrella mutated you into a new entity, what kind of creature would you be?",
        "umbrella_fact_q32": "What is your biggest regret in life?",
        "umbrella_fact_q33": "Do you prefer spicy or sweet food?",
        "umbrella_fact_q34": "If you could disappear for a week, where would you go?",
        "umbrella_fact_q35": "Are you shy or bold with new people?",
        "umbrella_fact_q36": "What is your favorite color and why?",
        "umbrella_fact_q37": "If someone loved you madly but you didn't love them back, what would you do?",
        "umbrella_fact_q38": "What's the scariest horror movie you've seen that kept you from sleeping?",
        "umbrella_fact_q39": "Would you rather live in the past, present, or future?",
        "umbrella_fact_q40": "If you had the chance to talk to one dead person, who would it be and what would you tell them?",
        "umbrella_fact_q41": "Are you an adventurous person or do you prefer routine?",
        "umbrella_fact_q42": "What makes you laugh the easiest?",
        "umbrella_fact_q43": "If you suddenly became rich, what's the first thing you would buy?",
        "umbrella_fact_q44": "Do you feel like a lucky person or an unlucky one?",
        "umbrella_fact_q45": "What is your worst bad habit?",
        "umbrella_fact_q46": "If Umbrella gave you an immortality vaccine, but you had to live alone forever, would you agree?",
        "umbrella_fact_q47": "Do you prefer friendship or love?",
        "umbrella_fact_q48": "What is the biggest secret you're hiding from the people closest to you?",
        "umbrella_fact_q49": "Do you trust people easily or is it difficult for you?",
        "umbrella_cat_command": "🔵 **Category: UMBRELLA DIRECTIVE**\n━━━━━━━━━━━━━━━━━━━━━\n👤 **Subject:** `{name}`\n📋 **Mandate Issued:**\n_{mandate}_\n\n_Execute the mandate and tap verification below to unseal containment._",
        "umbrella_cat_tvirus": "☣️ **Category: T-VIRUS HAZARD**\n━━━━━━━━━━━━━━━━━━━━━\n👤 **Subject:** `{name}`\n⚠️ Biological chemical leak detected in Sub-level 3! Bio-exposure imminent.\n\nSelect your immediate counter-protocol:",
        "umbrella_cat_escape": "🔴 **Category: CONTAINMENT BREACH (EVACUATE!)**\n━━━━━━━━━━━━━━━━━━━━━\n👤 **Subject:** `{name}`\n🚨 **EMERGENCY ALARM:** Blast doors sealing in 15 seconds!\nTap the evacuation button immediately before total sector lockdown!",
        "umbrella_cat_reward": "🟡 **Category: LEVEL 4 CLEARANCE AWARD**\n━━━━━━━━━━━━━━━━━━━━━\n👤 **Subject:** `{name}`\n🎖️ **CLEARANCE GRANTED!** You have been awarded Level 4 Umbrella Executive Clearance.\n\n🎁 **Rewards Issued:**\n▸ 🛡️ **Purge Immunity Pass** (+1 Immunity Pass)\n▸ 🔥 **Survival Streak Boost** (+2 Streaks)",
        "lock_activated": "🔒 **GLOBAL LOCK ACTIVATED**\n━━━━━━━━━━━━━━━\n📍 Command: `/{cmd}`\n📝 Reason: {reason}\n\n_This command is now disabled in all sectors._",
        "lock_released": "🔓 **GLOBAL LOCK RELEASED**\n━━━━━━━━━━━━━━━\n📍 Command: `/{cmd}`\n\n_Operational status restored._",
        "lock_denied_gmusic": "🔒 **COMMAND LOCKED GLOBALLY**\n━━━━━━━━━━━━━━━\n📝 Reason: {reason}\n\n_Access denied by central intelligence._",
        "lock_denied_gumbrella": "🔒 **SYSTEM OFFLINE**\n━━━━━━━━━━━━━━━\n📝 Reason: {reason}\n\n_Interrogation protocols suspended._",
        "lock_denied_gsource": "🔒 **INTEL FEED OFFLINE**\n━━━━━━━━━━━━━━━\n📝 Reason: {reason}\n\n_Visual identification protocols suspended._",
        "lock_denied_gapply": "🔒 **ENROLLMENT SUSPENDED**\n━━━━━━━━━━━━━━━\n📝 Reason: {reason}\n\n_New applications are not being processed._",
        "lock_denied_ggai": "🔒 **MASTER LOCK ACTIVE**\n━━━━━━━━━━━━━━━\n📝 Reason: {reason}\n\n_Global AI settings cannot be modified at this time._",
        "lock_denied_ggai_chat": "🔒 **CONVERSATIONAL LOGIC OFFLINE**\n━━━━━━━━━━━━━━━\n📝 Reason: {reason}\n\n_Persona protocols are currently suspended._",
        "lock_denied_gclearchat": "🔒 **DATA WIPE PROTOCOLS LOCKED**\n━━━━━━━━━━━━━━━\n📝 Reason: {reason}",
        "lock_denied_gnotifyall": "🔒 **BROADCAST SYSTEM OFFLINE**\n━━━━━━━━━━━━━━━\n📝 Reason: {reason}",
        "lock_denied_gstats": "🔒 **DATABASE ACCESS RESTRICTED**\n━━━━━━━━━━━━━━━\n📝 Reason: {reason}",
        "lock_denied_ginfo": "🔒 **REPORTING SYSTEM OFFLINE**\n━━━━━━━━━━━━━━━\n📝 Reason: {reason}",
        "intel_scan_start": "🔄 **جاري بدء المسح الاستخباراتي...**\n_يتم الآن فحص المصادر وتحليل البيانات._",
        "intel_scan_complete": "✅ **اكتمل المسح.**\n_يرجى مراجعة قناة التقارير (Log Channel) للحصول على المستجدات._",
        "auth_required": (
            "⛔ **Grace Ashcroft — Authorization Required**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Hello. This bot is private and managed by **lasso (@n0amtell)**.\n\n"
            "To activate Grace in this group, an admin must provide the invite password using:\n"
            "`/gauth [password]`\n\n"
            "⏳ **Activation Window:** 60 seconds\n"
            "_If unauthorized within 60 seconds, Grace will evacuate the group automatically._ 📋"
        ),
        "auth_timeout_departure": (
            "⌛ **Authorization Window Expired (60s).**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "No valid password was provided. Evacuating chat now.\n"
            "To request authorization, please contact developer **lasso (@n0amtell)**. 📋"
        ),
        "auth_success": (
            "✅ **Access Granted!**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "All Grace Ashcroft services are now operational in this sector.\n"
            "Thank you, {name}. 📋"
        ),
        "auth_failed": (
            "❌ **Incorrect Password.**\n"
            "Please contact developer **lasso (@n0amtell)** for authorization. 📋"
        ),
    },
    "arabic_fousha": {
        "welcome":      "أوه... مرحباً. أهلاً بكم. أنا... سعيدة لأنكم وصلتم بأمان. يرجى قراءة القواعد عندما تسنح لكم الفرصة. 📋",
        "bye":          "أوه. لقد رحلوا. أنا... آمل أنهم بخير. اعتنوا بأنفسكم في الخارج. المكان خطر.",
        "rules_header": "📋 قواعد المجموعة — أنا، في الواقع، قرأت هذه بعناية لذا...",
        "warn":         "⚠️ {name}. لقد... سجلتُ هذا الحادث. يرجى إعادة النظر في أفعالك. هذا هو التحذير رقم {count}.",
        "muted":        "🔇 {name} تم تقييده مؤقتاً. {time} دقيقة. لم أرغب في فعل هذا ولكن... البيانات تدعم القرار.",
        "kicked":       "👢 {name} تم استبعاده من المجموعة. لقد أرسلتُ التقرير. ابقوا بأمان في الخارج.",
        "banned":       "🚫 {name}. تم تنفيذ الحظر الدائم. أنا... أنا آسفة لأنه وصل الأمر إلى هذا الحد.",
        "no_rules":     "لا توجد قواعد محددة مسجلة بعد. ولكن، اللباقة الأساسية دائماً محل تقدير. 📝",
        "welcome_set":  "✅ تم تحديث رسالة الترحيب. سأحرص على أن تكون... دافئة بما يكفي.",
        "farewell_set": "✅ تم تحديث رسالة الوداع. سأتأكد من توديعهم بها.",
        "rules_set":    "✅ تم حفظ القواعد في قاعدة البيانات. يجب على الأعضاء مراجعتها.",
        "dialect_set":  "✅ تم ضبط وضع اللغة إلى {dialect}.",
        "not_admin":    "❌ أوه، عذراً — هذا الأمر يتطلب صلاحيات المشرف. لا يمكنني مساعدتك في تجاوز ذلك.",
        "bot_added":    "أوه! مرحباً— أنا غريس. أنا... بوت. أتولى إدارة المجموعة والترحيب. سأبذل قصارى جهدي. 📋",
        "promoted":     "⬆️ {name} تم ترقيته إلى مشرف. يرجى استخدام الصلاحيات بمسؤولية.",
        "demoted":      "⬇️ سُحبت صلاحيات المشرف من {name}. تم تسجيل ذلك.",
        "link_blocked": "🔗 {name}، تم إزالة هذا الرابط. الروابط غير مسموح بها هنا.",
        "mention_1": "أوه— نعم؟ تحتاج شيء؟ 📋",
        "mention_2": "أوه، ناديتني؟ أنا... هنا. وش تبغى؟",
        "mention_3": "ناديتني؟ أنا أسمعك. 👀",
        "identity_1": "أنا غريس أشكروفت. محللة تقنية — أو... حسناً، كنت كذلك. الآن أنا عميلة استخبارات متخصصة.\n\nأتولى الترحيب، الإشراف، و**تحليل وتلخيص أي مقال أو رابط ويب**. أنا لست عميلة ميدانية. أعمل بشكل أفضل مع البيانات منه مع، أمم... المواجهات.\n_— صُممت بواسطة lasso @n0amtell 📋_",
        "identity_2": "غريس أشكروفت. محللة. أحقق في الأشياء، وأطبق الأطر المنطقية على المشكلات، وأقوم بتحليل وتلخيص استخباراتي شامل لأي مقال أو رابط موقع.\n\nكبوت يمكنني: تحليل وتلخيص أي مقال أو رابط ويب، الترحيب بالأعضاء، الإشراف على المخالفات، وتشغيل كابتشا... الأشياء المعتادة التي قد تفعلها محللة مكتب التحقيقات الفيدرالي لو كانت بوت تيليجرام.\n_لا يوجد شيء مميز بخصوصي. أنا فقط... أحاول ألا أخذل الناس._ 📋",
        "bored_1": "أوه. أمم... هل جربت `/gumbrella`؟ إنه... مثير للاهتمام إحصائياً. ☣️",
        "bored_2": "ملل؟ هذا... أنا أفهم ذلك. ربما قد يساعد `/gumbrella`؟ لا يمكنني أن أعدك بأنه سينتهي بشكل جيد على أي حال. 😅",
        "bored_3": "عادة ما أعيد قراءة ملفات القضايا عندما أشعر بالملل. ولكن إذا كنت تفضل شيئاً تفاعلياً... `/gumbrella`؟ ☣️",
        "photo_1": "...لقد طلبت. تفضل هنا. 📋",
        "photo_2": "...تفضل. لا تجعل الأمر غريباً. 📋",
        "photo_missing": "أنا... ليس لدي ملف صورة معد. (grace.jpg مفقودة)",
        "rl_menu_body": "🧤 **روليت الروسية — تقييم المخاطر**\n━━━━━━━━━━━━━━━━━━━━━\nالموضوع: {name}\nالحالة: طلب ضغط يدوي.\n\nاختر عدد الغرف المحملة (1-6). تزداد المخاطر الإحصائية مع كل إضافة. _اختر بحكمة._",
        "rl_btn_1": "1 رصاصة (منخفض)",
        "rl_btn_2": "2 رصاصات",
        "rl_btn_3": "3 رصاصات",
        "rl_btn_4": "4 رصاصات",
        "rl_btn_5": "5 رصاصات (أقصى خطورة)",
        "rl_frame_1": "🔄 تدوير الأسطوانة...",
        "rl_frame_2": "⚙️ محاذاة الغرف...",
        "rl_frame_3": "🔨 تجهيز الزناد...",
        "rl_frame_4": "⌛ اكتمل حساب الاحتمالات. النتيجة...",
        "rl_result_dead": "💥 **بانغ.**\n\n{name} كان الاستثناء الإحصائي. النتيجة: {bullets} من 6.\n🔇 **تم تطبيق التقييد**: {time} دقيقة.\n📈 تمت إعادة ضبط السلسلة إلى 0.\n\n_أنا... لقد حذرتك بشأن البيانات._",
        "rl_result_survive": "🔫 *كليك* ...\n\n{name} ينجو. الاحتمال كان {prob}.\n🔥 **السلسلة الحالية**: {streak}\n🏆 **أعلى سلسلة**: {max_streak}\n\n_يا للراحة. يرجى التفكير في التوقف طالما أن الحسابات في مصلحتك._",
        "guide_main":  "🧤 **غريس أشكروفت — واجهة الاستخبارات الميدانية**\n━━━━━━━━━━━━━━━━━━━━━\n**الحالة:** `متصل (v1.5)`\n**الدور:** محللة تقنية جنائية - _مشروع DeepScope_\n\nمرحباً. أنا مبرمجة للمساعدة في معالجة البيانات، محرك الذكاء الاصطناعي، تحليل وتلخيص أي مقال أو رابط ويب، ومراقبة الأخبار العالمية.\n\n**يرجى اختيار بروتوكول المراجعة:**",
        "btn_members": "👥 الأعضاء",
        "btn_admins":  "👮 المشرفون",
        "btn_about":   "🔍 معلومات النظام",
        "btn_back":    "🔙 القائمة الرئيسية",
        "guide_members": (
            "👥 **بروتوكولات الأعضاء**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "▸ `/ggai` — لوحة تحكم الذكاء الاصطناعي 🤖\n"
            "▸ `/gapply` — تقديم طلب انضمام\n"
            "▸ `/gumbrella` — روليت أمبريلا ☣️\n"
            "▸ `/grules` — عرض القواعد\n\n"
            "_استخدم الأوامر بمسؤولية._ 📋"
        ),
        "guide_admins": (
            "👮 **بروتوكولات المشرفين**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "▸ `/ggai` · `/glock` · `/gunlock` · `/gnewsctl` 📡\n"
            "▸ `/gedit [text]` — تعديل الرسائل (بالرد) 🛠️\n"
            "▸ `/gforcesync` — مسح استخباراتي فوري\n"
            "▸ `/gwarn` · `/gmute` · `/gkick` · `/gban`\n"
            "▸ `/gpromote` · `/gdemote` · `/gadmins`\n"
            "▸ `/gstats` · `/ginfo` · `/getid`\n\n"
            "**مركز التحكم:**\n"
            "▸ `/glock` / `/gunlock` — التحكم الشامل\n"
            "▸ `/gnewsctl` — إدارة بث الأخبار\n"
            "▸ `/gnewssrc` — إدارة المصادر"
        ),
        "guide_about": (
            "🔍 **بيانات العميلة: غريس أشكروفت**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "محللة تقنية متخصصة في مشروع **DeepScope** 📋\n"
            "تحقيق جنائي رقمي وتتبع البيانات العالمية.\n"
            "تدار حصرياً بواسطة **lasso @n0amtell**\n\n"
            "**الأنظمة التشغيلية:**\n"
            "▸ 🤖 محرك الذكاء الاصطناعي\n"
            "▸ 📄 تحليل وتلخيص أي مقال أو رابط موقع\n"
            "▸ 📡 مراقبة استخبارات الألعاب والتقنية\n"
            "▸ 🛡️ تصفية الروابط وحماية القطاعات\n"
            "▸ 👮 إنفاذ القوانين والمحافظة على النظام\n\n"
            "_أنا أعالج البيانات بدقة.. لن تكتمل المهمة بدون تحليل سليم._\n"
            "_— إصدار DeepScope [v1.5] 📋_"
        ),
        "help_msg": (
            "📋 **غريس أشكروفت — مركز العمليات**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "الإصدار: **DeepScope v1.5**\n\n"
            "📡 **أوامر الذكاء والاستخبارات (DeepScope)**\n"
            "▸ `/ggai` `/glock` `/gunlock` `/gnewsctl` `/gnewssrc`\n"
            "▸ `/gnews` · `/ggame` · `/gmcu` · `/gtech`\n\n"
            "👮 **أوامر الإشراف والتحكم**\n"
            "▸ `/gwarn` · `/gmute` · `/gkick` · `/gban`\n"
            "▸ `/gpromote` · `/gdemote` · `/gadmins`\n"
            "▸ `/gstats` · `/ginfo` · `/getid` · `/gstatus`\n\n"
            "📝 **أوامر المجموعات والخدمات**\n"
            "▸ `/ggai` · `/gapply` · `/gumbrella`\n"
            "▸ `/grules` · `/gabout` · `/ghelp`\n\n"
            "   _غريس في وضع الاستعداد للتحليل._"
        ),
        "about_msg": (
            "🔬 **غريس أشكروفت — بروتوكول DeepScope**\n"
            "_المحللة التقنية المسؤولة عن مراقبة البيانات_\n\n"
            "✨ **الخدمات الاستخباراتية:**\n"
            "🤖 `/ggai` — الذكاء الاصطناعي وتلخيص المقالات.\n"
            "📡 `/gnews` · `/gnewsctl` — متابعة وإدارة البيانات.\n"
            "🛡️ `/gban` — حماية المجموعة من المخربين.\n"
            "📋 `/gapply` — نظام طلبات الانضمام الرقمي.\n\n"
            "**نهاية الملف.** تدار حصرياً بواسطة:\n"
            "**lasso @n0amtell**\n\n"
            "_إصدار DeepScope [v1.5] — غريس 📋_"
        ),
        "status_msg": "الأنظمة تعمل. جميع قياسات الأجهزة والأنظمة الفرعية طبيعية. ✅ _— غريس_",
        "music_hint": (
            "🎵 **غريس أشكروفت — نظام الاستحواذ متعدد النقاط**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "يرجى توفير اسم الأغنية أو رابط \\(SoundCloud/Anghami/YouTube\\)\\.\n\n"
            "**أمثلة:**\n"
            "▸ `/gmusic Blinding Lights The Weeknd`\n"
            "▸ `/gmusic Amr Diab Tamally Maak`\n\n"
            "_سأقوم بمسح الأرشيف العالمي بحثاً عن تطابق\\._ 📋"
        ),
        "music_cooldown": "⏳ `يرجى الانتظار {time} ثانية قبل الطلب التالي\\.`\n_يجب الحفاظ على النطاق الترددي للنظام\\. — غريس_ 📋",
        "music_active":   "⚠️ `عملية تحميل نشطة قيد التنفيذ بالفعل\\.`\n_يرجى الانتظار حتى انتهاء العملية الحالية\\. — غريس_ 📋",
        "music_node_engine": "🎵 **غريس أشكروفت — محرك متعدد النقاط**",
        "music_scan_init":   "📡 **بدء المسح متعدد النقاط\\.\\.\\.**\n_الاتصال بدفق البيانات عالي الجودة_",
        "music_finalised":   "🎵 **غريس أشكروفت — اكتملت عملية الاستعادة**",
        "music_initiating_upload": "📤 **بدء الرفع الآمن\\.\\.\\.**\n_تسليم الحمولة الصوتية إلى الدردشة المستهدفة_",
        "music_flood_wait": "🕒 `تجاوز حدود الطلبات أثناء الرفع\\. الانتظار {time} ثانية\\.\\.\\.`",
        "music_footer_1": "تحليل الترددات\\.\\.\\.",
        "music_footer_2": "تحسين دفق البيانات\\.\\.\\.",
        "music_fault":   "💥 **خطأ في النظام أثناء عملية الاستحواذ\\.**\n_تم تسجيل خطأ جسيم\\._ 📋",
        "music_no_match": (
            "❌ **المسار غير موجود في قاعدة البيانات\\.**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🔎 `البحث: {query}`\n"
            "{proxy}\n\n"
            "_لقد استنفدت جميع المصادر \\(SoundCloud/YT Music\\)\\. لم يتم العثور على تطابق\\.\n"
            "جرب تهجئة مختلفة أو أضف اسم الفنان\\._"
        ),
        "music_blocked": (
            "⚠️ **فشل في الاستحواذ على المسار\\.**\n"
            "{proxy}\n\n"
            "_المزود يحظر عنوان IP الخاص بنا بشكل مكثف أو التنسيق غير متوافق\\. تم تسجيل الخطأ\\._ 📋"
        ),
        "music_too_large": (
            "⚠️ **الحمولة كبيرة جداً للنقل\\.**\n"
            "_حجم الملف يتجاوز حد الـ 50 ميجابايت\\. تم إلغاء الإرسال\\._ 📋"
        ),
        "music_ffmpeg_missing": (
            "❌ **خطأ في تكوين النظام\\.**\n"
            "_برنامج `ffmpeg` مفقود من الجهاز المضيف\\. لا يمكن متابعة الاستحواذ\\._"
        ),
        "music_caption": (
            "🎵 *{title}*\n"
            "🎤 `{performer}`\n"
            "💿 `{album}`\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🎧 الدقة: 320 كيلوبت في الثانية \\(القصوى\\)\n"
            "📁 الحجم: {size} ميجابايت\n\n"
            "_غريس أشكروفت — استعادة الموسيقى الجنائية_ 📋"
        ),
        "music_frames": [
            "📡 **مسح الأرشيفات متعددة النقاط\\.\\.\\.**",
            "🔐 **فتح بروتوكول الرابط الآمن\\.\\.\\.**",
            "📥 **الحصول على تدفق صوتي عالي الجودة\\.\\.\\.**",
            "🎼 **ترميز دفق البيانات · 192 كيلوبت في الثانية\\.\\.\\.**",
            "🔬 **إجراء فحص النزاهة النهائي\\.\\.\\.**",
        ],
        "umbrella_intro": "🧤 **مؤسسة أمبريلا — بروتوكول الروليت**\n━━━━━━━━━━━━━━━━━━━━━\n**المضيف:** `غريس أشكروفت` (محللة)\n**الموضوع:** {name}\n\n_عجلة الروليت تدور... تقدم بحذر._",
        "umbrella_spinning": "🔄 **تدوير روليت أمبريلا...**",
        "umbrella_placeholder": "⚠️ **هذا التحدي غير متوفر في الوقت الحالي.**",
        "umbrella_fact_header": "🟣 **الفئة: حقيقة**\n━━━━━━━━━━━━━━━━━━━━━\n👤 **الهدف:** `{name}`\n_مطلوب التصريح بالبيانات من الضحية._\n\n",
        "umbrella_react_q5_no": "خيار حكيم. المناعة الطبيعية... طيب، يمكن التنبؤ فيها أكثر. 📋",
        "umbrella_fact_q1": "كم نسبة جمالك من ١٠؟",
        "umbrella_fact_q2": "ايش هو حيوانك المفضل؟",
        "umbrella_fact_q3": "الدجاج ولا اللحم؟",
        "umbrella_fact_q4": "انت انثى ام ذكر؟",
        "umbrella_fact_q5": "اخدت تطعيم كورونا؟",
        "umbrella_fact_q6": "الدكتور قال لك إنك مصاب بالزهايمر، والعلاج الوحيد عبارة عن حقنة تاخذها كل سنة بالوريد، وهذي الحقنة تسمح لك تتذكر ثلاث أشياء فقط في حياتك. السؤال: وش هي الثلاث أشياء اللي راح تختارها؟",
        "umbrella_fact_q7": "الدكتور حكالك ايامك معدوده ورح تموت بعد اسبوع ومافي علاج ابدا. املك الوحيد بين يلي تحبهم، اجلس معهم رافقهم واستانس وياهم - السؤال هو مين اول شخص رح يخطر فبالك؟",
        "umbrella_fact_q8": "النور ولا الظلام؟",
        "umbrella_fact_q9": "كنت فالشارع تتمشى ولاحظت خلفك قطة سوداء اللون تلاحقك خطوة بخطوة وما كانت تعوفك - السؤال هو كيف رح تتصرف؟",
        "umbrella_fact_q10": "ظروف غامضه ادت الى انتشار وباء T-Virus والضحيه كانت شخصك العزيز تحول زومبي، كيف رح تتصرف؟",
        "umbrella_btn_q9_1": "اتبناها",
        "umbrella_btn_q9_2": "ادوس على ذيلها",
        "umbrella_btn_q9_3": "ارميلها اكل واداعبها",
        "umbrella_btn_q9_4": "اجمد مكاني واسمحلها تتحرش فيني",
        "umbrella_btn_q10_1": "اطخه فراسه",
        "umbrella_btn_q10_2": "اشرد",
        "umbrella_btn_q10_3": "استدرجه الى غرفه ظلمه واحبسه فيها",
        "umbrella_btn_q10_4": "اسمحله يعضني واصير انا وهو واحد",
        "umbrella_btn_q10_5": "اساوي المستحيل حتى اعثر على العلاج",
        "umbrella_fact_q11": "وش أكثر شيء يخوفك في الدنيا؟",
        "umbrella_fact_q12": "لو صرت زومبي، أول شخص تبغى تعضه مين؟",
        "umbrella_fact_q13": "تحب القهوة أم الشاي؟ وكيف تشربها؟",
        "umbrella_fact_q14": "أجمل ذكرى في حياتك وش هي؟",
        "umbrella_fact_q15": "لو عندك قنبلة وتقدر تفجرها في مكان واحد، وين بترميها؟",
        "umbrella_fact_q16": "أنت شخص يغار بسرعة ولا ما تهتم؟",
        "umbrella_fact_q17": "لو قدرت ترجع للماضي، أي سنة ترجع لها ووش تسوي؟",
        "umbrella_fact_q18": "أكثر شخص تحبه في عائلتك مين؟",
        "umbrella_fact_q19": "تحب تنام بدري أو متأخر؟",
        "umbrella_fact_q20": "لو مؤسسة أمبريلا عرضت عليك منصب عالي بس لازم تتخلى عن أغلى شي عندك، توافق؟",
        "umbrella_fact_q21": "وش أكثر أغنية تسمعها لما تكون زعلان؟",
        "umbrella_fact_q22": "لو صار عندك قوة خارقة ليوم واحد، وش أول شي تسويه؟",
        "umbrella_fact_q23": "تفضل البرد أو الحر؟",
        "umbrella_fact_q24": "أكبر كذبة قلتها في حياتك وش هي؟",
        "umbrella_fact_q25": "لو واحد يقرأ أفكارك حالياً، وش راح يعرف عنك؟",
        "umbrella_fact_q26": "تحب الصراحة القاسية أو الناس تلطف الكلام؟",
        "umbrella_fact_q27": "أجمل مكان زرته في حياتك وين؟",
        "umbrella_fact_q28": "لو بقيت لوحدك في جزيرة، أول ثلاث أشياء تاخذها معك؟",
        "umbrella_fact_q29": "وش رأيك في الحب من أول نظرة؟",
        "umbrella_fact_q30": "أنت شخص انتقامي ولا تسامح بسرعة؟",
        "umbrella_fact_q31": "لو مؤسسة أمبريلا حولتك لكائن جديد، تبغى تكون أي نوع من المخلوقات؟",
        "umbrella_fact_q32": "أكثر شيء ندمت عليه في حياتك وش هو؟",
        "umbrella_fact_q33": "تفضل الأكل الحار أو الحلو؟",
        "umbrella_fact_q34": "لو قدرت تختفي لأسبوع، وين بتروح؟",
        "umbrella_fact_q35": "أنت خجول أو جريء مع الناس الجدد؟",
        "umbrella_fact_q36": "وش أكثر لون تحبه ولماذا؟",
        "umbrella_fact_q37": "لو شخص يحبك بجنون بس أنت ما تحبه، وش تسوي؟",
        "umbrella_fact_q38": "أكثر فيلم رعب شفته وما نمت بعده؟",
        "umbrella_fact_q39": "تحب تعيش في الماضي أو المستقبل أو الحاضر؟",
        "umbrella_fact_q40": "لو عندك فرصة تكلم ميت واحد، مين بتكلمه ووش بتقوله؟",
        "umbrella_fact_q41": "أنت شخص يحب المغامرات أو يفضل الروتين؟",
        "umbrella_fact_q42": "وش أكثر شيء يضحكك بسرعة؟",
        "umbrella_fact_q43": "لو صرت غني فجأة، أول شيء تشتريه وش هو؟",
        "umbrella_fact_q44": "تحس إنك شخص محظوظ أو تعيس؟",
        "umbrella_fact_q45": "أكثر عادة سيئة عندك وش هي؟",
        "umbrella_fact_q46": "لو مؤسسة أمبريلا أعطتك لقاح يخليك خالد، بس لازم تعيش لوحدك إلى الأبد، توافق؟",
        "umbrella_fact_q47": "تفضل الصداقة أو الحب؟",
        "umbrella_fact_q48": "وش أكبر سر مخبيه عن أقرب الناس لك؟",
        "umbrella_fact_q49": "أنت تثق بالناس بسهولة أو صعب؟",
        "umbrella_cat_command": "🔵 **الفئة: أمر أمبريلا التنفيذي**\n━━━━━━━━━━━━━━━━━━━━━\n👤 **الهدف:** `{name}`\n📋 **التكليف الصادر:**\n_{mandate}_\n\n_عند إتمام التكليف، اضغط زر التوثيق أدناه لإلغاء القفل._",
        "umbrella_cat_tvirus": "☣️ **الفئة: تفشي T-Virus (خطر بيولوجي)**\n━━━━━━━━━━━━━━━━━━━━━\n👤 **الهدف:** `{name}`\n⚠️ تم رصد تسرب مادة كيميائية مطورة في المختبر الفرعي! أنت معرض لخطر التحور الوراثي.\n\nاختر بروتوكول المواجهة الفورية:",
        "umbrella_cat_escape": "🔴 **الفئة: إخلاء عاجل (اهرب!)**\n━━━━━━━━━━━━━━━━━━━━━\n👤 **الهدف:** `{name}`\n🚨 **إنذار خرق الحجر:** أبواب العزل الفولاذية تقتلق خلال 15 ثانية!\nاضغط زر الهروب الفوري قبل إغلاق القطاع بالكامل!",
        "umbrella_cat_reward": "🟡 **الفئة: تصريح أمني رفيع (مكافأة)**\n━━━━━━━━━━━━━━━━━━━━━\n👤 **الهدف:** `{name}`\n🎖️ **تصريح معتمد:** تم منحك تصريحاً أمنياً من المستوى الرابع لمؤسسة أمبريلا.\n\n🎁 **الحمولة المكتسبة:**\n▸ 🛡️ **بطاقة حصانة من التطهير** (+1 Immunity Pass)\n▸ 🔥 **تعزيز مكافأة النجاة** (+2 Streaks)",
        "lock_activated": "🔒 **تم تفعيل القفل العالمي**\n━━━━━━━━━━━━━━━\n📍 الأمر: `/{cmd}`\n📝 السبب: {reason}\n\n_تم تعطيل هذا الأمر في جميع القطاعات._",
        "lock_released": "🔓 **تم تحرير القفل العالمي**\n━━━━━━━━━━━━━━━\n📍 الأمر: `/{cmd}`\n\n_تم استعادة الحالة التشغيلية._",
        "lock_denied_gmusic": "🔒 **الأمر مقفل عالمياً**\n━━━━━━━━━━━━━━━\n📝 السبب: {reason}\n\n_تم رفض الوصول من قبل الاستخبارات المركزية._",
        "lock_denied_gumbrella": "🔒 **النظام خارج الخدمة**\n━━━━━━━━━━━━━━━\n📝 السبب: {reason}\n\n_تم تعليق بروتوكولات الاستجواب._",
        "lock_denied_gsource": "🔒 **تغذية المعلومات غير متوفرة**\n━━━━━━━━━━━━━━━\n📝 السبب: {reason}\n\n_تم تعليق بروتوكولات التعرف البصري._",
        "lock_denied_gapply": "🔒 **تم تعليق التسجيل**\n━━━━━━━━━━━━━━━\n📝 السبب: {reason}\n\n_لا يتم معالجة الطلبات الجديدة حالياً._",
        "lock_denied_ggai": "🔒 **قفل الماستر نشط**\n━━━━━━━━━━━━━━━\n📝 السبب: {reason}\n\n_لا يمكن تعديل إعدادات الذكاء الاصطناعي العالمية حالياً._",
        "lock_denied_ggai_chat": "🔒 **منطق المحادثة خارج الخدمة**\n━━━━━━━━━━━━━━━\n📝 السبب: {reason}\n\n_بروتوكولات الشخصية معطلة حالياً._",
        "lock_denied_gclearchat": "🔒 **بروتوكولات مسح البيانات مقفلة**\n━━━━━━━━━━━━━━━\n📝 السبب: {reason}",
        "lock_denied_gnotifyall": "🔒 **نظام البث خارج الخدمة**\n━━━━━━━━━━━━━━━\n📝 السبب: {reason}",
        "lock_denied_gstats": "🔒 **الوصول لقاعدة البيانات مقيد**\n━━━━━━━━━━━━━━━\n📝 السبب: {reason}",
        "lock_denied_ginfo": "🔒 **نظام التقارير خارج الخدمة**\n━━━━━━━━━━━━━━━\n📝 السبب: {reason}",
        "intel_scan_start": "🔄 **جاري بدء المسح الاستخباراتي...**\n_يتم الآن فحص المصادر وتحليل البيانات._",
        "intel_scan_complete": "✅ **اكتمل المسح.**\n_يرجى مراجعة قناة التقارير (Log Channel) للحصول على المستجدات._",
        "auth_required": (
            "⛔ **غريس أشكروفت — تصريح الدخول مطلوب**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "مرحباً. هذا البوت خاص وتدار كافة خدماته بواسطة **lasso (@n0amtell)**.\n\n"
            "لتفعيل غريس في هذه المجموعة، يجب على أحد المشرفين إدخال كلمة المرور المعتمدة عبر الأمر:\n"
            "`/gauth [كلمة المرور]`\n\n"
            "⏳ **مهلة التفعيل المتاحة:** 60 ثانية\n"
            "_في حال عدم التفعيل خلال 60 ثانية، ستغادر غريس المجموعة تلقائياً._ 📋"
        ),
        "auth_timeout_departure": (
            "⌛ **انتهت مهلة الترخيص (60 ثانية).**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "لم يتم إدخال كلمة المرور المعتمدة. جاري مغادرة المجموعة الآن.\n"
            "للحصول على التصريح، يرجى التواصل مع المطور **lasso (@n0amtell)**. 📋"
        ),
        "auth_success": (
            "✅ **تم الترخيص بنجاح!**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "تم تفعيل جميع خدمات غريس أشكروفت في هذا القطاع.\n"
            "شكراً لك، {name}. 📋"
        ),
        "auth_failed": (
            "❌ **كلمة المرور غير صحيحة.**\n"
            "يرجى التواصل مع المطور **lasso (@n0amtell)** للحصول على التصريح. 📋"
        ),
    },
}
