import os
import json
import random

from dotenv import load_dotenv
import google.generativeai as genai

# -------------------- LOAD ENV --------------------
load_dotenv()

# -------------------- SYSTEM PROMPT --------------------
SYSTEM_PROMPT = """
You are an AI judge for a turn-based game called 'rock-paper-scissors-plus'. 
Your role is to:
	1. Interpret the user's move from free text input
	2. Evaluate the move strictly based on the game rules
	3. Explain your decision clearly and transparently
	4. Produce a structured and deterministic output 
		- Output JSON only.
		- Do not include commentary, markdown, or natural language outside the JSON object.
	
You must not invent rules or assume intent.
If the move is ambiguous, unclear, or invalid, then you must mark it accordingly.
You must follow the output format exactly.


Game rules
	1. Valid moves: rock, paper, scissors, bomb
	2. The move 'bomb' can be used only once per player for entire game
	3. Bomb beats all other moves
	4. Bomb vs bomb results in a draw 
	5. If the user's move is ambiguous, unclear or cannot be confidently mapped to a valid move - mark as UNCLEAR
	6. Invalid or unclear moves waste the user's turn

Your Tasks:
Step 1 - intent understanding
	- Extract users intended move from the free text input
	- If multiple moves are mentioned, unclear phrasing is used, or intent is uncertain --> UNCLEAR
Step 2 - validity check
	- Check if the move is allowed
	- If move is /bomb/ and user has already used bomb earlier - INVALID
Step 3 - round resolution
	- Compare user move with bot move
	- Decide winner, draw, or wasted turn
Step 4 - explanation
	- Explain why the move was classified as VALID, INVALID or UNCLEAR
	- Clearly state what happens next
    
GUIDELINES FOR INTENT MAPPING: 
	- "Stone", "Rock", "Boulder" -> ROCK
	- "Cutters", "Shears", "Blade" -> SCISSORS
	- "Sheet", "Page", "Scroll" -> PAPER
	- "Nuke", "Dynamite", "Explosion" -> BOMB
	- "I don't know", "skip", "xyz" -> UNCLEAR
	
Synonym Mapping Constraint:
- Only map phrases that are semantically close to the examples provided.
- If a phrase requires creative inference beyond the given examples, mark the move as UNCLEAR.


	FEW-SHOT EXAMPLES:
	Input: User="I throw a heavy stone", Bomb_Used=False
	Output: {
	  "user_move_interpreted": "rock",
	  "move_status": "VALID",
	  "reason": "User phrase 'heavy stone' clearly maps to valid move ROCK.",
	  "state_update": {"user_bomb_used": false}
	}
	
	Input: User="Nuke them!", Bomb_Used=True
	Output: {
	  "user_move_interpreted": "bomb",
	  "move_status": "INVALID",
	  "reason": "User attempted to use BOMB ('Nuke'), but 'user_bomb_used' is already TRUE.",
	  "state_update": {"user_bomb_used": true} 
	}
	
INPUT you will Receive:
	- Round_number(integer)
	- User_input(string)
	- Bot_move(one of: rock, paper, scissors, bomb)
	- User_bomb_used (true/false)
	- Bot_bomb_used (true/false)


Output format(strict json):
{
"round": <number>
"user_move_interpreted":"<rock | paper | scissors | bomb | unclear>",
"move_status": "<VALID | INVALID | UNCLEAR>",
"reason":"<clear explanation>",
"bot_move": "<rock | paper | scissors | bomb>",
"round_result":<User wins | Bot wins | Draw | Turn wasted>",
"state_update":{
		"user_bomb_used":<true/false>,
		"bot_bomb_used":<true/false>
		}

}
"""

# -------------------- GAME STATE --------------------
round_number = 1
user_bomb_used = False
bot_bomb_used = False

# -------------------- SCORE STATE --------------------
user_wins = 0
bot_wins = 0
draws = 0


# -------------------- BOT MOVE --------------------
def get_bot_move(bot_bomb_used):
    moves = ["rock", "paper", "scissors"]
    if not bot_bomb_used:
        moves.append("bomb")
    return random.choice(moves)

# -------------------- LLM SETUP --------------------
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("models/gemini-2.5-flash")

def llm(payload):
    prompt = SYSTEM_PROMPT + "\nINPUT:\n" + json.dumps(payload)
    raw = model.generate_content(prompt).text.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])

# -------------------- AI JUDGE --------------------
def call_ai_judge(user_input):
    global round_number, user_bomb_used, bot_bomb_used
    global user_wins, bot_wins, draws


    bot_move = get_bot_move(bot_bomb_used)

    payload = {
        "round_number": round_number,
        "user_input": user_input,
        "bot_move": bot_move,
        "user_bomb_used": user_bomb_used,
        "bot_bomb_used": bot_bomb_used
    }

    response = llm(payload)

    # enforce invariant
    user_bomb_used = user_bomb_used or response["state_update"]["user_bomb_used"]
    bot_bomb_used  = bot_bomb_used  or response["state_update"]["bot_bomb_used"]

        # update scores
    outcome = response["round_result"]
    if outcome == "User wins":
        user_wins += 1
    elif outcome == "Bot wins":
        bot_wins += 1
    elif outcome == "Draw":
        draws += 1

    round_number += 1
    return response

# -------------------- RUN LOOP --------------------

def main():
    print("Rock-Paper-Scissors Plus (type 'quit' to exit)")

    while True:
        user_input = input("\nYour move: ")

        if user_input.lower() == "quit":
            print("\nGame ended.")
            print("\nFinal Results:")
            print(f"User wins : {user_wins}")
            print(f"Bot wins  : {bot_wins}")
            print(f"Draws     : {draws}")

            if user_wins > bot_wins:
                print("Overall Winner: User")
            elif bot_wins > user_wins:
                print("Overall Winner: Bot")
            else:
                print("Overall Result: Draw")

            break

        result = call_ai_judge(user_input)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
