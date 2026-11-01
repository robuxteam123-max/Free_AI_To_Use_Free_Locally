"""MyFirstAI: a tiny, REAL neural network built using only standard Python.

No APIs, no downloaded models, no NumPy or PyTorch.
Learns to classify messages using a trainable hidden layer and backpropagation.
"""

import hashlib
import json
import math
import random
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
LESSONS_FILE = HERE / "lessons.json"
BRAIN_FILE = HERE / "brain.json"
HIDDEN_SIZE = 18  # Neurons in the hidden layer; try changing this!
EPOCHS = 250      # Number of passes over the lessons
LEARNING_RATE = 0.065
SEED = 42


def words(message):
    """Convert text into simple lowercase words."""
    return re.findall(r"[a-z0-9]+", message.lower())


def load_lessons():
    with LESSONS_FILE.open("r", encoding="utf-8") as file:
        lessons = json.load(file)
    if not isinstance(lessons, dict) or len(lessons) < 2:
        raise ValueError("lessons.json must contain at least two categories.")
    for category, content in lessons.items():
        if not content.get("examples") or not content.get("replies"):
            raise ValueError(f"Category '{category}' needs examples and replies.")
    return lessons


def lesson_fingerprint(lessons):
    text = json.dumps(lessons, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class TinyNeuralNetwork:
    def __init__(self, vocab, categories, hidden=HIDDEN_SIZE, seed=SEED):
        self.vocab = vocab
        self.categories = categories
        self.word_to_index = {word: index for index, word in enumerate(vocab)}
        self.hidden = hidden
        rng = random.Random(seed)
        # First layer: text -> hidden neurons
        self.w1 = [[rng.uniform(-0.20, 0.20) for _ in vocab]
                   for _ in range(hidden)]
        self.b1 = [0.0 for _ in range(hidden)]
        # Second layer: hidden neurons -> answer categories
        self.w2 = [[rng.uniform(-0.20, 0.20) for _ in range(hidden)]
                   for _ in categories]
        self.b2 = [0.0 for _ in categories]

    def vectorize(self, message):
        """A simple bag-of-words input: 1 if a learned word is present."""
        vec = [0.0] * len(self.vocab)
        tokens = words(message)
        for word in tokens:
            if word in self.word_to_index:
                vec[self.word_to_index[word]] = 1.0
        return vec

    def forward(self, x):
        # Hidden neurons: tanh(sum(inputs * weights) + bias)
        h = [math.tanh(sum(weight * value for weight, value in zip(row, x)) + bias)
             for row, bias in zip(self.w1, self.b1)]
        # Output neurons, converted to probabilities by softmax
        scores = [sum(weight * value for weight, value in zip(row, h)) + bias
                  for row, bias in zip(self.w2, self.b2)]
        highest = max(scores)  # Avoid overflowing exp()
        exponentials = [math.exp(score - highest) for score in scores]
        total = sum(exponentials)
        probabilities = [number / total for number in exponentials]
        return h, probabilities

    def learn_one(self, x, answer, rate):
        """Backpropagation: correct both layers using the prediction error."""
        h, probabilities = self.forward(x)
        error = probabilities[:]
        error[answer] -= 1.0  # softmax + cross-entropy gradient
        # Calculate hidden gradients BEFORE updating layer 2.
        hidden_error = [
            (1 - h[j] ** 2) * sum(error[k] * self.w2[k][j]
                                   for k in range(len(self.categories)))
            for j in range(self.hidden)
        ]
        for k in range(len(self.categories)):
            for j in range(self.hidden):
                self.w2[k][j] -= rate * error[k] * h[j]
            self.b2[k] -= rate * error[k]
        for j in range(self.hidden):
            for i, value in enumerate(x):
                if value:  # Skip zero-valued inputs
                    self.w1[j][i] -= rate * hidden_error[j] * value
            self.b1[j] -= rate * hidden_error[j]
        return -math.log(max(probabilities[answer], 1e-12))

    def predict(self, message):
        x = self.vectorize(message)
        _, probabilities = self.forward(x)
        best = max(range(len(probabilities)), key=probabilities.__getitem__)
        tokens = set(words(message))
        overlap = len(tokens & self.word_to_index.keys()) / max(len(tokens), 1)
        return self.categories[best], probabilities[best], overlap

    def save(self, fingerprint):
        data = {
            "fingerprint": fingerprint, "vocab": self.vocab,
            "categories": self.categories, "hidden": self.hidden,
            "w1": self.w1, "b1": self.b1, "w2": self.w2, "b2": self.b2
        }
        with BRAIN_FILE.open("w", encoding="utf-8") as file:
            json.dump(data, file)

    @classmethod
    def load(cls, fingerprint):
        with BRAIN_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if data["fingerprint"] != fingerprint:
            raise ValueError("Lessons changed; retraining is required.")
        brain = cls(data["vocab"], data["categories"], data["hidden"])
        for name in ("w1", "b1", "w2", "b2"):
            setattr(brain, name, data[name])
        return brain


def train(lessons):
    rng = random.Random(SEED)
    vocab = sorted(set(word for content in lessons.values()
                       for example in content["examples"] for word in words(example)))
    categories = list(lessons)
    brain = TinyNeuralNetwork(vocab, categories)
    examples = [(brain.vectorize(example), categories.index(category))
                for category, content in lessons.items()
                for example in content["examples"]]
    print(f"\nTraining {len(categories)} categories using {len(examples)} examples")
    print(f"Words: {len(vocab)} | Hidden neurons: {HIDDEN_SIZE} | Epochs: {EPOCHS}")
    for epoch in range(EPOCHS):
        rng.shuffle(examples)
        total_loss = sum(brain.learn_one(vector, answer, LEARNING_RATE)
                         for vector, answer in examples)
        if (epoch + 1) in (1, 50, 100, 150, 200, EPOCHS):
            correct = sum(brain.forward(vector)[1].index(max(brain.forward(vector)[1])) == answer
                          for vector, answer in examples)
            print(f"Epoch {epoch + 1:3d}/{EPOCHS}: loss={total_loss / len(examples):.3f}, "
                  f"training accuracy={correct}/{len(examples)}")
    brain.save(lesson_fingerprint(lessons))
    print("Learned weights saved to brain.json!\n")
    return brain


def answer(brain, lessons, message):
    category, confidence, overlap = brain.predict(message)
    # A confident prediction on completely unfamiliar words is not trustworthy.
    if confidence < 0.52 or overlap < 0.30:
        return ("I don't understand that yet. Try a message about Python, "
                "HTML, math, science, or saying hello. Type /help for commands.",
                category, confidence)
    # These responses are written by humans; the category is chosen by the NEURAL NETWORK.
    reply = random.choice(lessons[category]["replies"])
    return reply, category, confidence


def main():
    print("=" * 52)
    print(" MyFirstAI - Neural network from scratch (offline)")
    print("=" * 52)
    try:
        lessons = load_lessons()
        fingerprint = lesson_fingerprint(lessons)
        try:
            brain = TinyNeuralNetwork.load(fingerprint)
            print("Loaded your trained brain from brain.json.")
        except (FileNotFoundError, ValueError, KeyError):
            print("No matching brain found. Learning from scratch...")
            brain = train(lessons)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Could not start:", exc)
        return

    print("Chat with your AI! Type /help for commands, /quit to exit.\n")
    while True:
        try:
            message = input("YOU > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
        if not message:
            continue
        if message.lower() in ("/quit", "/exit"):
            print("Goodbye!")
            break
        if message.lower() == "/help":
            print("/help  = commands | /train = relearn lessons.json")
            print("/info  = view neuron counts | /quit = close")
            print("To teach your AI: edit lessons.json, save it, then type /train.")
            continue
        if message.lower() == "/info":
            print(f"{len(brain.vocab)} input words -> {brain.hidden} hidden neurons "
                  f"-> {len(brain.categories)} answer classes")
            continue
        if message.lower() == "/train":
            try:
                lessons = load_lessons()
                brain = train(lessons)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                print("Training failed:", exc)
            continue
        reply, category, confidence = answer(brain, lessons, message)
        print(f"AI  > {reply}")
        print(f"      [neural guess: {category}, confidence: {confidence:.0%}]\n")


if __name__ == "__main__":
    main()
