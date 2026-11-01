"""Quick checks for MyFirstAI's learning and saved weights."""
import ai

lessons = ai.load_lessons()
brain = ai.train(lessons)
checks = [
    ("hello", "greeting"),
    ("thank you so much", "thanks"),
    ("help with python", "python"),
    ("html website", "web"),
    ("what is gravity", "science"),
    ("learn algebra", "math"),
    ("goodbye", "goodbye"),
    ("who are you", "about"),
]
for phrase, expected in checks:
    predicted, confidence, overlap = brain.predict(phrase)
    print(f"{phrase!r}: {predicted} ({confidence:.1%})")
    assert predicted == expected, f"Expected {expected}, got {predicted}"
loaded = ai.TinyNeuralNetwork.load(ai.lesson_fingerprint(lessons))
for phrase, expected in checks:
    assert loaded.predict(phrase)[0] == expected
print("\nSUCCESS: model learned the examples and saves/loads correctly.")
