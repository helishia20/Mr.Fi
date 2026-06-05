"""
bert_puzzle.py — Mode 2: Classic Puzzle + BERT Fill-[MASK]

  
  pip install optimum onnxruntime
    اthen torch
    in the end tensorflow

"""

import threading, random


# ── Puzzle banks ──────────────────────────────────────────────────────────────

SCIENCE_PUZZLES = [
    ("The planet closest to the Sun is [MASK].",           "mercury"),
    ("Water is made of hydrogen and [MASK].",              "oxygen"),
    ("The powerhouse of the cell is the [MASK].",          "mitochondria"),
    ("Albert [MASK] developed the theory of relativity.",  "einstein"),
    ("The speed of [MASK] is 300,000 km per second.",      "light"),
    ("The largest planet in our solar system is [MASK].",  "jupiter"),
    ("Photosynthesis converts sunlight into [MASK].",      "energy"),
    ("Isaac [MASK] discovered gravity.",                   "newton"),
    ("Sound travels faster in [MASK] than in air.",        "water"),
    ("The moon orbits the [MASK].",                        "earth"),
    ("Bats navigate using [MASK].",                        "echolocation"),
    ("DNA stands for deoxyribonucleic [MASK].",            "acid"),
    ("The boiling point of water is [MASK] degrees.",      "100"),
]

FUN_PUZZLES = [
    ("Harry [MASK] is a famous wizard.",                   "potter"),
    ("The Lion [MASK] is a Shakespeare play.",             "king"),
    ("Mickey [MASK] is a famous cartoon character.",       "mouse"),
    ("The game of [MASK] is played on a 64-square board.", "chess"),
    ("A group of lions is called a [MASK].",               "pride"),
    ("Romeo and [MASK] is written by Shakespeare.",        "juliet"),
    ("The Mona [MASK] is painted by Leonardo da Vinci.",   "lisa"),
    ("Sherlock [MASK] is a famous fictional detective.",   "holmes"),
    ("Peter [MASK] is a Marvel superhero.",                "parker"),
    ("Superman's weakness is [MASK].",                     "kryptonite"),
]

ALL_PUZZLES = SCIENCE_PUZZLES + FUN_PUZZLES


def _try_load_pipeline():

    # ──with first pip suggestion  ──────────────────────
    try:
        from optimum.pipelines import pipeline as opt_pipeline
        model = opt_pipeline("fill-mask", model="optimum/distilbert-base-uncased",
                             accelerator="ort")
        return model, "onnxruntime ✅"
    except Exception:
        pass

    # ── with second pip suggestion (torch)────────────────────────────────────────────────
    try:
        import torch  # noqa — just to check 4 install
        from transformers import pipeline
        model = pipeline("fill-mask", model="distilbert-base-uncased",
                         top_k=5, device=-1)   # device=-1 means CPU
        return model, "PyTorch ✅"
    except ImportError:
        pass
    except Exception as e:
        return None, f"torch error: {str(e)[:60]}"

    # ── suggrstion 3 tensorflow ─────────────────────────────────────────────────────
    try:
        import tensorflow  # noqa
        from transformers import pipeline
        model = pipeline("fill-mask", model="distilbert-base-uncased",
                         top_k=5, framework="tf")
        return model, "TensorFlow ✅"
    except ImportError:
        pass
    except Exception as e:
        return None, f"tf error: {str(e)[:60]}"

    # ── هیچکدوم نصب نیست ─────────────────────────────────────────────────────
    return None, (
        "No backend found!\n"
        "Install one of:\n"
        "  pip install torch transformers\n"
        "  pip install tensorflow transformers\n"
        "  pip install optimum[onnxruntime] transformers"
    )


class BertPuzzleEngine:
    def __init__(self):
        # BERT state
        self.bert_model    = None
        self.bert_ready    = False
        self.bert_loading  = False
        self.bert_backend  = ""
        self.bert_error    = ""
        self.bert_progress = "Not loaded"

        # puzzle state
        self.current_sentence = ""
        self.correct_answer   = ""
        self.user_input       = ""
        self.predictions      = []
        self.result_msg       = ""
        self.puzzle_type      = "both"
        self.score            = 0
        self.streak           = 0

        # classic game state
        self.classic_state = {}
        self._new_classic()

    # ── Classic ──────────────────────────────────────────────────────────────

    def _new_classic(self):
        kind = random.choice(["seq", "anagram"])
        if kind == "seq":
            start = random.randint(1, 9)
            step  = random.randint(2, 6)
            seq   = [start + step * i for i in range(4)]
            self.classic_state = {
                "kind": "seq", "seq": seq,
                "answer": seq[-1] + step,
                "input": "", "result": "",
            }
        else:
            word = random.choice(["frog","apple","star","heart","planet",
                                  "ocean","music","stone","flame","river"])
            chars = list(word)
            random.shuffle(chars)
            self.classic_state = {
                "kind": "anagram", "word": word,
                "scrambled": "".join(chars),
                "input": "", "result": "",
            }

    def check_classic(self) -> bool:
        cs  = self.classic_state
        ans = cs.get("input", "").strip().lower()
        if cs["kind"] == "seq":
            try:    ok = int(ans) == cs["answer"]
            except: ok = False
        else:
            ok = (ans == cs["word"])

        if ok:
            cs["result"] = "✅ Correct! +10 pts"
            self.score  += 10
            self.streak += 1
            return True
        else:
            exp = str(cs["answer"]) if cs["kind"] == "seq" else cs["word"]
            cs["result"] = f"❌ Answer: {exp}"
            self.streak  = 0
            return False

    # ── BERT loading ──────────────────────────────────────────────────────────

    def start_bert_loading(self):
        if self.bert_loading or self.bert_ready:
            return
        self.bert_loading  = True
        self.bert_error    = ""
        self.bert_progress = "Checking backends..."
        threading.Thread(target=self._load_bert, daemon=True).start()

    def _load_bert(self):
        try:
            self.bert_progress = "Loading model (first time ~250MB)..."
            model, info = _try_load_pipeline()
            if model is None:
                self.bert_error    = info
                self.bert_progress = "Failed — see error above"
            else:
                self.bert_model    = model
                self.bert_backend  = info
                self.bert_ready    = True
                self.bert_progress = f"Ready — {info}"
                self.new_bert_puzzle()
        except Exception as e:
            self.bert_error    = str(e)[:80]
            self.bert_progress = "Error"
        finally:
            self.bert_loading = False

    # ── BERT puzzle ───────────────────────────────────────────────────────────

    def new_bert_puzzle(self):
        pool = (SCIENCE_PUZZLES if self.puzzle_type == "science" else
                FUN_PUZZLES     if self.puzzle_type == "fun"     else
                ALL_PUZZLES)
        sentence, answer      = random.choice(pool)
        self.current_sentence = sentence
        self.correct_answer   = answer.lower()
        self.user_input       = ""
        self.result_msg       = ""
        self.predictions      = []
        if self.bert_ready:
            threading.Thread(target=self._run_bert, daemon=True).start()

    def _run_bert(self):
        try:
            results = self.bert_model(self.current_sentence)
            self.predictions = [
                (r["token_str"].strip(), round(r["score"] * 100, 1))
                for r in results
            ]
        except Exception:
            self.predictions = []

    def check_bert(self) -> bool:
        ans     = self.user_input.strip().lower()
        correct = self.correct_answer
        ok = (ans == correct) or (correct in ans) or (ans in correct and len(ans) >= 3)
        if ok:
            bert_ok = any(p[0].lower() == ans for p in self.predictions)
            bonus   = 5 if bert_ok else 0
            self.result_msg = (f"✅ Correct! +{10+bonus} pts"
                               + (" (BERT agreed! 🤖)" if bert_ok else ""))
            self.score  += 10 + bonus
            self.streak += 1
            return True
        else:
            top = self.predictions[0][0] if self.predictions else "?"
            self.result_msg = f"❌ Answer: '{correct}'  |  BERT top: '{top}'"
            self.streak = 0
            return False

    def get_hint(self) -> str:
        h = f"Starts with '{self.correct_answer[0].upper()}'"
        if self.predictions:
            h += "  |  BERT: " + ", ".join(p[0] for p in self.predictions[:3])
        return h
