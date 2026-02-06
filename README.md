
# **AI Judge – Rock-Paper-Scissors Plus**

This project implements a **prompt-driven AI Judge** that evaluates free-text user moves in a *Rock-Paper-Scissors Plus* game.
The focus is on **prompt design, explainability, and state-aware judgment**, not on building a full game engine.

---

## **Prompt Design Rationale**

The prompt is structured as a **policy document** that clearly defines the LLM’s role as a judge.
It enforces:

* **Explicit rules and constraints**
* **Step-by-step reasoning** (intent → validity → resolution → explanation)
* **Strict JSON-only output**
* **Controlled intent mapping** with explicit synonym boundaries

This prevents rule invention, over-interpretation, and inconsistent outputs.

---

## **Failure Cases Considered**

The system explicitly handles:

* **Ambiguous input** (e.g., “maybe rock”, multiple moves) → `UNCLEAR`
* **Invalid or creative moves** outside the rule set
* **One-time bomb usage**, enforced as an irreversible invariant
* **LLM output drift**, handled via defensive JSON parsing
* **Stateless LLM memory**, handled by injecting all game state each turn

Invalid or unclear moves waste the turn as defined by the rules.

---

## **Final Result Handling**

Each round is judged independently by the LLM.
The system aggregates round outcomes and prints a **final winner (User / Bot / Draw)** when the user exits.

---

## **Future Improvements**

* Confidence scores for intent interpretation
* Structured error codes for invalid and unclear moves
* Multi-agent separation for intent parsing and rule enforcement

---

This design demonstrates an LLM acting as a transparent decision-maker while the glue code enforces state safety and invariants.

