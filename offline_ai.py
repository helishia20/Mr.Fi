"""

offline_ai.py: Smart offline AI
"""
import re, random, math


class OfflineAI:

    def __init__(self):
        # ── knowledge base ────────────────────────────────────────────────────
        self.kb = {
            # Science
            "gravity":       "Gravity is a force that pulls objects toward each other. On Earth it's 9.8 m/s². It's why things fall down! 🌍",
            "photosynthesis":"Photosynthesis is how plants make food from sunlight, CO₂ and water, producing oxygen as a byproduct 🌱",
            "atom":          "Atoms are the tiny building blocks of everything. They have protons and neutrons in a nucleus, with electrons orbiting around ⚛️",
            "dna":           "DNA is the molecule that carries genetic instructions for all living things — like a biological instruction manual 🧬",
            "light":         "Light travels at ~300,000 km/s. It's both a wave and a particle (photon) — quantum physics is wild! ✨",
            "sound":         "Sound is a vibration that travels through air (or other materials) as pressure waves, at ~343 m/s in air 🔊",
            "water":         "Water is H₂O — two hydrogen atoms and one oxygen. It covers ~71% of Earth's surface 💧",
            "earth":         "Earth is the third planet from the Sun, about 4.5 billion years old, with a radius of ~6,371 km 🌍",
            "sun":           "The Sun is a G-type star at the center of our solar system. It's 1.4 million km wide and 150 million km from Earth ☀️",
            "moon":          "The Moon is Earth's only natural satellite. It's 384,400 km away and causes tides with its gravity 🌙",
            "black hole":    "A black hole is a region where gravity is so strong nothing — not even light — can escape. They form from collapsed stars 🕳️",
            "evolution":     "Evolution is the process by which species change over time through natural selection and genetic variation 🦎",
            "climate":       "Climate is the long-term pattern of weather in an area. Climate change refers to shifts in these patterns, mainly from CO₂ emissions 🌡️",
            "electricity":   "Electricity is the flow of electrons through a conductor. Voltage drives it, resistance opposes it — Ohm's Law: V = IR ⚡",
            "magnetism":     "Magnetism is a force produced by moving electric charges. The Earth has a magnetic field that protects us from solar wind 🧲",

            # Tech
            "python":        "Python is a high-level, easy-to-read programming language great for beginners and experts alike. It's used in AI, web, and science 🐍",
            "ai":            "Artificial Intelligence (AI) is the simulation of human intelligence in machines — pattern recognition, reasoning, and learning 🤖",
            "internet":      "The internet is a global network of computers communicating via protocols like TCP/IP. It was born from ARPANET in the 1960s 🌐",
            "computer":      "A computer processes data using a CPU, RAM for short-term memory, and storage for long-term. Programs give it instructions 💻",
            "algorithm":     "An algorithm is a step-by-step procedure to solve a problem. Sorting, searching, and AI all rely on algorithms 📋",
            "machine learning": "Machine learning is a type of AI where computers learn patterns from data rather than being explicitly programmed 🧠",
            "blockchain":    "Blockchain is a distributed ledger where data is stored in linked blocks, making it hard to alter — used in cryptocurrencies 🔗",

            # Math
            "pi":            "Pi (π) ≈ 3.14159265... It's the ratio of a circle's circumference to its diameter. It's irrational and goes on forever! ⭕",
            "fibonacci":     "Fibonacci: 1,1,2,3,5,8,13,21... Each number is the sum of the two before it. It appears everywhere in nature 🌻",
            "prime":         "Prime numbers are only divisible by 1 and themselves: 2,3,5,7,11,13... There are infinitely many of them ∞",
            "pythagorean":   "Pythagorean theorem: a² + b² = c². In a right triangle, the square of the hypotenuse equals the sum of squares of other sides 📐",
            "calculus":      "Calculus studies change (derivatives) and accumulation (integrals). Newton and Leibniz developed it independently in the 17th century 📈",

            # Health
            "sleep":         "Adults need 7–9 hours of sleep. During sleep, your brain consolidates memories and your body repairs itself 😴",
            "exercise":      "Regular exercise improves heart health, mood (releases endorphins), strength, and reduces disease risk. Even 30 min/day helps! 🏃",
            "nutrition":     "A balanced diet includes proteins, carbs, fats, vitamins and minerals. Vegetables, whole grains and lean proteins are key 🥗",
            "stress":        "Stress triggers cortisol release. Chronic stress harms health. Deep breathing, exercise, and sleep help manage it 🧘",

            # History / Culture  
            "iran":          "Iran (Persia) is one of the world's oldest civilizations, over 7,000 years old. It has rich history in science, poetry, and art 🇮🇷",
            "frog":          "Frogs are amphibians that live on land and in water. There are over 7,000 species! They help control insects 🐸",

            # فارسی
            "زمین":          "زمین سیاره‌ی سوم منظومه‌ی شمسیه و تنها جایی که حیات شناخته‌شده داره. قطرش ۱۲,۷۴۲ کیلومتره 🌍",
            "خورشید":        "خورشید یه ستاره‌ی G-type در مرکز منظومه‌ی شمسیه. ۱۵۰ میلیون کیلومتر از زمین فاصله داره ☀️",
            "ماه":           "ماه تنها قمر طبیعی زمینه و با جاذبه‌اش باعث ایجاد جزر و مد میشه 🌙",
            "آب":            "آب ترکیبی از دو اتم هیدروژن و یک اتم اکسیژنه (H₂O). حیات بدون آب ممکن نیست 💧",
            "قورباغه":       "قورباغه‌ها دوزیستانی هستند که هم توی آب و هم روی خشکی زندگی می‌کنند! دقیقاً مثل من 🐸",
            "گرانش":         "گرانش نیرویی‌ست که اجسام رو به هم جذب می‌کنه. شتاب گرانش زمین ۹.۸ متر بر مجذور ثانیه‌ست 🌍",
            "مغز":           "مغز انسان حدود ۸۶ میلیارد نورون داره و کنترل همه‌ی کارهای بدن رو بر عهده داره 🧠",
            "هوش مصنوعی":    "هوش مصنوعی یعنی کامپیوترها طوری برنامه‌ریزی بشن که مثل انسان فکر کنن و یاد بگیرن 🤖",
        }

        self.emotional = {
            "sad":    ["ناراحت نباش! یه بازی بازی کنیم؟ 💚", "Don't be sad! Want to play a game? 💚"],
            "happy":  ["عالیه! انرژی مثبت! 🎉", "Awesome! Good vibes! 🎉"],
            "love":   ["منم عاشقتم! 💚🐸", "I love you too! 💚"],
            "thank":  ["خواهش میکنم! 🐸", "You're welcome! 🐸"],
            "bored":  ["بیا یه بازی Mode 3 بازی کنیم! 🎮", "Let's play Brain Games! Mode 3 🎮"],
            "tired":  ["استراحت مهمه! 😴 Mr Fi هم دوست داره بخوابه!", "Rest is important! 😴"],
            "hungry": ["برو از Shop غذا بخر! 🍽", "Go buy food from the Shop! 🍽"],
        }

        self.greet_fa = ["سلام", "درود", "هلو", "صبح بخیر", "عصر بخیر", "شب بخیر"]
        self.greet_en = ["hello", "hi", "hey", "howdy", "greetings", "good morning", "good evening"]

    # ── helpers ───────────────────────────────────────────────────────────────

    def _lang(self, text):
        fa = len(re.findall(r'[\u0600-\u06FF]', text))
        return "fa" if fa > len(text) * 0.25 else "en"

    def _score(self, query, key):
        q, k = query.lower(), key.lower()
        if k in q: return 1.0
        # word overlap
        qw, kw = set(q.split()), set(k.split())
        overlap = len(qw & kw)
        if overlap: return overlap / max(len(qw), len(kw))
        # substring
        if any(kp in q for kp in k.split()): return 0.6
        return 0.0

    def _find_kb(self, query):
        best_score, best_val = 0.0, None
        for key, val in self.kb.items():
            s = self._score(query, key)
            if s > best_score:
                best_score, best_val = s, val
        return (best_val, best_score) if best_score >= 0.5 else (None, 0)

    def _handle_math(self, text):
        """Evaluate simple math expression."""
        # look for explicit ops first
        t = text.lower().strip()
        nums = re.findall(r'-?\d+\.?\d*', t)
        if len(nums) < 2:
            return None

        a, b = float(nums[0]), float(nums[1])
        fa = self._lang(text) == "fa"

        if any(op in t for op in ["جمع", "+", "plus", "add", "sum"]):
            return f"{'جواب' if fa else 'Answer'}: {a} + {b} = {a+b} ✅"
        if any(op in t for op in ["تفریق", "minus", "subtract", "-"]) and "-" not in nums[0]:
            return f"{'جواب' if fa else 'Answer'}: {a} - {b} = {a-b} ✅"
        if any(op in t for op in ["ضرب", "times", "×", "*", "multiply"]):
            return f"{'جواب' if fa else 'Answer'}: {a} × {b} = {a*b} ✅"
        if any(op in t for op in ["تقسیم", "divide", "÷", "/"]):
            if b == 0:
                return "نمیشه بر صفر تقسیم کرد! 🙈" if fa else "Can't divide by zero! 🙈"
            return f"{'جواب' if fa else 'Answer'}: {a} ÷ {b} = {round(a/b,4)} ✅"
        if any(op in t for op in ["توان", "power", "^", "**"]):
            return f"{'جواب' if fa else 'Answer'}: {a}^{b} = {a**b} ✅"

        # expression with = sign like "2+2?"
        expr = re.sub(r'[^0-9+\-*/().\s]', '', t).strip()
        if expr:
            try:
                result = eval(expr)
                return f"{'جواب' if fa else 'Answer'}: {expr} = {result} ✅"
            except Exception:
                pass
        return None

    # ── main response ──────────────────────────────────────────────────────────

    def get_response(self, message: str, history=None) -> str:
        msg  = message.strip()
        ml   = msg.lower()
        lang = self._lang(msg)
        fa   = (lang == "fa")

        # ── 1. greeting ───────────────────────────────────────────────────────
        if any(g in ml for g in self.greet_fa + self.greet_en):
            r_fa = ["سلام! چطور میتونم کمکت کنم؟ 🐸",
                    "هی! خوش اومدی! 💚",
                    "سلام دوستم! امروز چی میخوای بدونی؟ 🌟"]
            r_en = ["Hello! How can I help you? 🐸",
                    "Hey there! What's on your mind? 💚",
                    "Hi friend! What would you like to know? 🌟"]
            return random.choice(r_fa if fa else r_en)

        # ── 2. emotion keywords ───────────────────────────────────────────────
        emotion_map = {
            "sad":    ["ناراحت","غمگین","دلگیر","گریه","sad","upset","depressed","cry"],
            "happy":  ["خوشحال","شاد","عالی","happy","great","awesome","joy"],
            "love":   ["عاشق","دوست دارم","love","i love"],
            "thank":  ["ممنون","متشکر","مرسی","thanks","thank you","thx"],
            "bored":  ["حوصله‌ام","بی‌حوصله","خسته‌ام","bored","boring"],
            "tired":  ["خوابم","خستم","tired","sleepy"],
            "hungry": ["گشنمه","گرسنه","hungry","starving"],
        }
        for emo, kws in emotion_map.items():
            if any(k in ml for k in kws):
                return random.choice(self.emotional[emo])

        # ── 3. "who are you" / "چی هستی" ─────────────────────────────────────
        if any(x in ml for x in ["who are you","what are you","کی هستی","چی هستی","معرفی"]):
            return ("من Mr Fi هستم، یه قورباغه‌ی باهوشم که میتونم سوالات علمی، ریاضی و فناوری رو جواب بدم! 🐸"
                    if fa else
                    "I'm Mr Fi, a smart frog who can answer science, math, tech and general questions! 🐸")

        # ── 4. "what can you do" ──────────────────────────────────────────────
        if any(x in ml for x in ["what can you","چیکار میتونی","چه کمکی","help me with"]):
            return ("میتونم جواب سوالات علمی، ریاضی، فناوری بدم. محاسبه کنم. و درباره‌ی هر موضوعی حرف بزنیم! 🐸"
                    if fa else
                    "I can answer science, math, tech questions, do calculations, and chat about almost anything! 🐸")

        # ── 5. math detection ─────────────────────────────────────────────────
        math_kws = ["جمع","تفریق","ضرب","تقسیم","توان","plus","minus","times","divide",
                    "multiply","calculate","compute","=","چنده","چقدر","مساوی"]
        has_num  = len(re.findall(r'\d', msg)) >= 1
        is_math  = (has_num and any(k in ml for k in math_kws)) or \
                   re.search(r'\d\s*[\+\-\*\/]\s*\d', msg)
        if is_math:
            r = self._handle_math(msg)
            if r: return r

        # ── 6. knowledge base lookup ──────────────────────────────────────────
        val, score = self._find_kb(msg)
        if val:
            return val

        # ── 7. "what is X" / "X چیه" — topic extraction ─────────────────────
        topic = None
        m = re.search(r'what\s+is\s+(.+?)[\?\.\!]?$', ml)
        if m: topic = m.group(1).strip()
        m2 = re.search(r'(.+?)\s+(چیه|چیست|چی هست|یعنی چی)', ml)
        if m2: topic = m2.group(1).strip()
        m3 = re.search(r'درباره‌ی?\s+(.+?)\s+بگو', ml)
        if m3: topic = m3.group(1).strip()
        m4 = re.search(r'tell me about\s+(.+)', ml)
        if m4: topic = m4.group(1).strip()

        if topic:
            val2, s2 = self._find_kb(topic)
            if val2: return val2
            return (f"درباره‌ی «{topic}» اطلاعات کاملی ندارم، ولی میتونی سوال دقیق‌تری بپرسی! 🤔"
                    if fa else
                    f"I don't have detailed info on '{topic}' yet, but ask me something more specific! 🤔")

        # ── 8. how / why questions ────────────────────────────────────────────
        if any(x in ml for x in ["چطور","چرا","چگونه","how does","how do","why is","why does"]):
            if len(ml) > 12:
                val3, s3 = self._find_kb(msg)
                if val3: return val3
                return (f"این سوال جالبیه! پاسخ کامل توی دانشم نیست، ولی موضوع رو دقیق‌تر بپرس 🤔"
                        if fa else
                        "Great question! I don't have a full answer but try asking more specifically 🤔")

        # ── 9. yes / no questions ─────────────────────────────────────────────
        if ml.endswith("?") or ml.endswith("؟"):
            if len(ml) < 30:
                r_fa = ["آره، فکر میکنم بله! 🐸", "نه، احتمالاً نه 🤔", "بستگی داره! بیشتر توضیح بده 💚"]
                r_en = ["Yes, I think so! 🐸", "Hmm, probably not 🤔", "It depends! Tell me more 💚"]
                return random.choice(r_fa if fa else r_en)

        # ── 10. generic fallback ──────────────────────────────────────────────
        g_fa = ["جالبه! بیشتر بگو 💚", "اوه، میفهمم! 🌟", "اوکی! چیز دیگه‌ای میخوای بدونی؟ 🐸"]
        g_en = ["Interesting! Tell me more 💚", "I see! 🌟", "Got it! Anything else? 🐸"]
        return random.choice(g_fa if fa else g_en)
