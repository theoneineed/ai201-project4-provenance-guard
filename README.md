# ai201-project4-provenance-guard
This is the repo for uploading project 4 assignment for AI201 codepath course. 

[![Walkthrough video](https://img.youtube.com/vi/BmcCF_PFaVQ/0.jpg)](https://youtu.be/BmcCF_PFaVQ)

*Provenance Guard*

Provenance Guard is a backend classification system designed for creative sharing platforms to evaluate whether submitted text is human-written or AI-generated. Instead of relying on a binary output, this system uses a multi-signal detection pipeline to calculate a calibrated confidence score, surfacing a plain-language transparency label to users while maintaining a robust audit log and appeals workflow for creators.

---

## 1. Multi-Signal Detection Pipeline
To avoid the false positives inherent in single-model detection, Provenance Guard evaluates submissions using two distinct, independent signals:

* **Signal 1: LLM-Based Semantic Analysis (Groq `llama-3.3-70b-versatile`)**
    * **What it measures:** Semantic coherence, emotional tone, and the presence of common AI tropes (e.g., highly predictable transitions, neutral safety-driven tone).
    * **What it misses:** It can be fooled by heavily prompt-engineered AI text (e.g., "Write this like a frantic Reddit user") which artificially injects human-like chaos.
* **Signal 2: Stylometric Heuristics (Pure Python)**
    * **What it measures:** Structural variance—specifically "burstiness" (sentence length variance) and Type-Token Ratio (vocabulary diversity). 
    * **What it misses:** It ignores semantic meaning entirely. Highly structured human writing (like an academic paper or technical manual) will score as AI because of its uniform sentence lengths and specific vocabulary.

---

## 2. Confidence Scoring & Uncertainty
Both signals return a float between `0.0` (Likely Human) and `1.0` (Likely AI). The system mathematically combines them to reflect genuine uncertainty. Because the LLM is slightly better at parsing semantic intent, the scoring uses a 60/40 weighted split:

$Confidence = 0.6(Signal_{LLM}) + 0.4(Signal_{Stylo})$

**Validation (Meaningful Variation):**
Testing the system confirmed that different inputs produce meaningfully different confidence scores rather than a constant output.
* **Lower-Confidence Case (Human Text):** A casual text submission about a sunset produced a combined confidence score of **`0.32`**, placing it safely in the Authentic Origin category.
* **High-Confidence Case (AI Text):** Repeated automated rate-limit testing with identical, structured strings produced a combined confidence score of **`0.74`**, pushing it up into the Uncertain/Automated boundary.

---

## 3. Transparency Labels
The API returns a plain-language transparency label based on the confidence thresholds. I specifically avoided technical jargon like "logits" or "classifier confidence" so non-technical users can understand the verdict.

| Score Range | Transparency Label |
| :--- | :--- |
| **0.00 – 0.35** | "Authentic Origin: This content reflects the natural variance and unique structural signatures of human writing." |
| **0.36 – 0.74** | "Uncertain Origin: This content exhibits a mix of human idiosyncrasies and automated patterns. Attribution cannot be definitively confirmed." |
| **0.75 – 1.00** | "Automated Origin: This content closely matches the structural predictability and semantic coherence typical of AI-generated text." |

---

## 4. Rate Limiting
To protect the `POST /submit` endpoint from bot flooding or abuse, I implemented `Flask-Limiter` with an in-memory storage URI.

* **Chosen Limits:** `5 per minute; 50 per day`
* **Reasoning:** A human writer submitting original poetry or stories to a platform realistically will not submit more than 5 distinct, high-effort pieces per minute. 50 per day easily accommodates power users while strictly cutting off automated scraper/spammer scripts.

**Evidence of Rate Limit Triggering (429 Response):**
```text
200
200
200
200
200
429
429
429
429
429
429
429
```


## 5. Audit Log & Appeals Workflow

Creators can contest a classification via the POST /appeal endpoint. When triggered, the system updates the original content's status to "under_review" and appends the creator's reasoning directly to the JSON audit log entry, giving platform moderators full context for manual review.

Sample Audit Log Output (Showing successful classification and a subsequent appeal):

```json
{
"entries": [
    {
    "appeal_reasoning": "I wrote this myself from personal experience. I am a non-native English speaker and my writing style may appear more formal than typical.",
    "attribution": "likely_human",
    "confidence": 0.32,
    "content_id": "9c1f1a34-9532-4997-b5c6-c28c193d2cc7",
    "creator_id": "test-user-1",
    "signal_1_llm": 0.2,
    "signal_2_stylo": 0.5,
    "status": "under_review",
    "timestamp": "2026-07-01T00:31:33.038497+00:00"
    }
]
}

```

## 6. Spec Reflection & Known Limitations

Spec Reflection:

* How it helped: Defining the exact math thresholds in planning.md prior to coding made implementing the conditional logic in app.py seamless. I knew exactly what label to return without guessing on the fly.

* How it diverged: During implementation, I realized my stylometric signal was failing on short texts (2-3 sentences) because calculating variance requires a larger sample size. I had to diverge from the spec by adding fallback conditional logic (if len(sentences) < 2: return 0.5) to prevent math errors and artificial 0.0 scores.

Known Limitations:
The system is highly vulnerable to misclassifying short-form technical writing or academic abstracts. Because academic writing explicitly discourages "burstiness" (sentence length variance) and utilizes a uniform, highly formal vocabulary, the Stylometric heuristic will score it close to 1.0. Depending on the LLM's assessment, this could easily drag a legitimate human essay into the "Uncertain" or "Automated" categories.


## 7. AI Usage

I utilized AI tools (Gemini) to act as a coding assistant and sounding board during implementation.

    Flask Architecture & Groq Setup: I provided my spec and asked the AI to generate a Flask skeleton and a Python function hitting the Groq API. Revision: I overrode the AI's initial Groq prompt, refining the instruction to force response_format={"type": "json_object"} so I could extract a reliable float for the math functions instead of a raw text response.

    Stylometric Math Translation: I asked the AI to write the pure Python function for sentence variance based on my spec. Revision: The AI initially just returned the raw variance number. I heavily revised the logic to mathematically normalize the variance and Type-Token Ratio into a clean 0.0 to 1.0 scale so it could be properly combined with the LLM output.