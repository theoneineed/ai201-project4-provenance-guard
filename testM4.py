#testing different curl commands to check the implementation of milestone 4

from signals import signal_1_llm, signal_2_stylometrics

test_cases = {
    "1. Clearly AI": "Artificial intelligence represents a transformative paradigm shift in modern society. It is important to note that while the benefits of AI are numerous, it is equally essential to consider the ethical implications. Furthermore, stakeholders across various sectors must collaborate to ensure responsible deployment.",
    
    "2. Clearly Human": "ok so i finally tried that new ramen place downtown and honestly? underwhelming. the broth was fine but they put WAY too much sodium in it and i was thirsty for like three hours after. my friend got the spicy version and said it was better. probably won't go back unless someone drags me there",
    
    "3. Formal Human (Edge Case)": "The relationship between monetary policy and asset price inflation has been extensively studied in the literature. Central banks face a fundamental tension between their mandate for price stability and the unintended consequences of prolonged low interest rates on equity and real estate valuations.",
    
    "4. Lightly Edited AI": "I've been thinking a lot about remote work lately. There are genuine tradeoffs — flexibility and no commute on one side, isolation and blurred work-life boundaries on the other. Studies show productivity varies widely by individual and role type.",
    
    "5. Bonus: Chaotic Prompted AI": "OMG YOU GUYS. I literally cannot even right now. The way this entire system is built is just so crazy??? Like, why do we even need to do this!"
}

for name, text in test_cases.items():
    llm = signal_1_llm(text)
    stylo = signal_2_stylometrics(text)
    combined = round((0.6 * llm) + (0.4 * stylo), 2)
    
    print(f"\n--- {name} ---")
    print(f"LLM Score:   {llm}")
    print(f"Stylo Score: {stylo}")
    print(f"COMBINED:    {combined}")