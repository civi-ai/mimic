import os
from dotenv import load_dotenv
load_dotenv()
from mimic.core import MimicCore

def main():
    print("╔════════════════════════════════════════╗")
    print("║     MIMIC — morphic agent framework    ║")
    print("║     civiai/mimic                       ║")
    print("║     built in Kuala Lumpur              ║")
    print("╚════════════════════════════════════════╝")
    
    mimic = MimicCore()
    
    print("\n" + "="*50)
    print("DEMO 1 — Simple task (expect: PRIME mode)")
    print("="*50)
    
    simple_task = "What is machine learning? Explain in 2 sentences."
    result1 = mimic.run(simple_task)
    print(f"\nOutput:\n{result1}")
    
    print("\n" + "="*50)
    print("DEMO 2 — Complex task (expect: FRAGMENT mode)")
    print("="*50)
    
    complex_task = "Research the top 3 AI agent frameworks, compare their strengths and weaknesses, and recommend one for a Malaysian healthcare startup."
    result2 = mimic.run(complex_task)
    print(f"\nOutput:\n{result2}")
    
    print("\n" + "="*50)
    print("MIMIC run complete.")
    print("Check wagon_logs/ for full memory of both runs.")
    print("="*50)

if __name__ == "__main__":
    main()