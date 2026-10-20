"""Cave Climb: a dice race to the top of the cave.

Run:  pip install flask
      python cave_climb.py
Open: http://127.0.0.1:5000
"""
import random
from flask import Flask, render_template_string, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

STEPS = 10  # board: Start (0), steps 1-9, Finish (10)
TIE_MOVES_UP = False  # True: rolling the same number as before also moves up

# Which of the 9 grid cells show a dot for each dice value
FACES = {
    1: [5],
    2: [1, 9],
    3: [1, 5, 9],
    4: [1, 3, 7, 9],
    5: [1, 3, 5, 7, 9],
    6: [1, 3, 4, 6, 7, 9],
}


def new_game(names):
    return {
        "players": [{"name": n, "pos": 0, "prev": None} for n in names],
        "turn": 0,
        "winner": None,
        "roll": None,
        "message": "Roll the dice to start. A 6 on your first roll does not count.",
    }


def play_turn(game):
    """Apply one dice roll to the current player."""
    player = game["players"][game["turn"]]
    roll = random.randint(1, 6)
    game["roll"] = roll
    name = player["name"]

    if player["prev"] is None:
        # First roll: a 6 does not count, anything else sets the number to beat.
        if roll == 6:
            game["message"] = f"{name} rolled a 6 on the first roll. It does not count."
        else:
            player["prev"] = roll
            game["message"] = f"{name} rolled {roll}. This is the number to beat."
    else:
        prev = player["prev"]
        if roll > prev:
            player["pos"] += 1
            game["message"] = f"{name} rolled {roll}, higher than {prev}. Up one step."
        elif roll < prev:
            player["pos"] = max(0, player["pos"] - 1)
            game["message"] = f"{name} rolled {roll}, lower than {prev}. Down one step."
        elif TIE_MOVES_UP:
            player["pos"] += 1
            game["message"] = f"{name} rolled {roll}, the same as before. Up one step."
        else:
            game["message"] = f"{name} rolled {roll}, the same as before. No move."
        player["prev"] = roll

    if player["pos"] >= STEPS:
        game["winner"] = name
        game["message"] = f"{name} reached the top of the cave and wins!"
    else:
        game["turn"] = (game["turn"] + 1) % len(game["players"])



PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Cave Climb</title>
  <style>
:root {
  --white: #ffffff;
  --text: #ffffff;
  --torch: #ffb347;
  --green: #6fcf97;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

/* Dark cave rock, drawn with an SVG noise filter so no image file is needed */
body, .rung, .panel {
  background-color: #1c232b;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='260' height='260'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' seed='4'/><feColorMatrix type='saturate' values='0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.45'/></svg>");
}

body {
  font-family: "Trebuchet MS", "Segoe UI", sans-serif;
  color: var(--text);
  line-height: 1.4;
  min-height: 100vh;
}

main { max-width: 900px; margin: 0 auto; padding: 1rem 1rem 3rem; }

h1 {
  font-family: Georgia, serif;
  text-align: center;
  font-size: clamp(2rem, 6vw, 3rem);
  color: var(--torch);
  margin-bottom: 1rem;
}
h2 { font-family: Georgia, serif; margin-bottom: 0.5rem; }

.panel {
  border: 4px solid var(--white);
  padding: 1.25rem;
  max-width: 480px;
  margin: 0 auto;
}
form label { display: block; margin-top: 0.75rem; font-weight: 700; }
input {
  display: block;
  width: 100%;
  padding: 0.5rem;
  margin: 0.25rem 0 1rem;
  background: #11161b;
  color: var(--text);
  border: 2px solid var(--white);
  font-size: 1rem;
}

.button {
  padding: 0.7rem 1.5rem;
  background: var(--torch);
  color: #2a1a00;
  font-weight: 700;
  font-size: 1rem;
  border: none;
  border-radius: 999px;
  cursor: pointer;
}
.button:hover { filter: brightness(1.1); }
.button.secondary { background: transparent; color: var(--text); border: 2px solid var(--white); }
.button:focus-visible, input:focus-visible {
  outline: 3px solid var(--torch);
  outline-offset: 2px;
}

/* Board: ladder | dice area | ladder */
.board {
  display: grid;
  grid-template-columns: minmax(130px, 200px) 1fr minmax(130px, 200px);
  gap: 1rem;
  align-items: start;
}

.lane { text-align: center; }
.lane h3 { font-size: 1.1rem; }
.lane.active h3 { color: var(--torch); }
.last { font-size: 0.85rem; opacity: 0.8; margin-bottom: 0.4rem; }

/* White ladder frame with rock-textured rungs */
.ladder {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 10px;
  background: var(--white);
}
.rung {
  position: relative;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.step-no { font-size: 1.4rem; font-weight: 700; }

.token {
  position: absolute;
  right: 8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 3px solid var(--white);
}
.t0 { background: #ff6b57; }
.t1 { background: #4aa8ff; }

/* Center area where "Dice Needed" sits on the original board */
.center { text-align: center; padding-top: 3rem; }
.turn { font-size: 1.2rem; margin-bottom: 1rem; }
.winner { font-size: 1.5rem; font-weight: 700; color: var(--green); margin-bottom: 1rem; }
.message { margin: 1rem 0; min-height: 3em; }
.actions { display: flex; gap: 0.75rem; justify-content: center; flex-wrap: wrap; }
.actions form { margin: 0; }

.dice {
  width: 88px;
  height: 88px;
  margin: 0 auto;
  padding: 10px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(3, 1fr);
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 4px 0 #999;
}
.dice.empty { opacity: 0.4; }
.dot { width: 15px; height: 15px; border-radius: 50%; place-self: center; background: transparent; }
.dot.on { background: #222; }

@media (max-width: 600px) {
  .board { grid-template-columns: 1fr 1fr; }
  .lane[style*="grid-column: 3"] { grid-column: 2 !important; }
  .center { grid-column: 1 / 3 !important; grid-row: 2 !important; padding-top: 0.5rem; }
  .rung { height: 38px; }
}
  </style>
</head>
<body>
<main>
  <h1>Cave Climb</h1>

  {% if not game %}
  <section class="panel setup">
    <h2>New game</h2>
    <p>Roll higher than your last roll to climb one step. Roll lower and you slide down one step. First to the Finish wins.</p>
    <form method="post" action="{{ url_for('start') }}">
      <label>Player 1 name
        <input type="text" name="name0" placeholder="Player 1" maxlength="14">
      </label>
      <label>Player 2 name
        <input type="text" name="name1" placeholder="Player 2" maxlength="14">
      </label>
      <button class="button" type="submit">Start</button>
    </form>
  </section>

  {% else %}
  <div class="board">

    {% for p in game.players %}
    {% set pi = loop.index0 %}
    <div class="lane {% if pi == game.turn and not game.winner %}active{% endif %}" style="grid-column: {{ 1 if pi == 0 else 3 }}; grid-row: 1;">
      <h3>{{ p.name }}</h3>
      <p class="last">Last roll: {{ p.prev if p.prev else '-' }}</p>
      <div class="ladder">
        {% for step in range(steps, -1, -1) %}
        <div class="rung">
          <span class="step-no">{{ 'Finish' if step == steps else ('Start' if step == 0 else step) }}</span>
          {% if p.pos == step %}<span class="token t{{ pi }}"></span>{% endif %}
        </div>
        {% endfor %}
      </div>
    </div>
    {% endfor %}

    <section class="center" style="grid-column: 2; grid-row: 1;">
      {% if game.winner %}
        <p class="winner">{{ game.message }}</p>
      {% else %}
        <p class="turn">Turn: <strong>{{ game.players[game.turn].name }}</strong></p>
      {% endif %}

      <div class="dice {% if not game.roll %}empty{% endif %}" aria-label="Dice shows {{ game.roll or 'nothing' }}">
        {% for cell in range(1, 10) %}
          <span class="dot {% if game.roll and cell in faces[game.roll] %}on{% endif %}"></span>
        {% endfor %}
      </div>
      <p class="message">{{ game.message }}</p>

      <div class="actions">
        {% if not game.winner %}
        <form method="post" action="{{ url_for('roll') }}">
          <button class="button" type="submit">Roll dice</button>
        </form>
        {% endif %}
        <form method="post" action="{{ url_for('reset') }}">
          <button class="button secondary" type="submit">{{ 'Play again' if game.winner else 'New game' }}</button>
        </form>
      </div>
    </section>

  </div>
  {% endif %}
</main>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(PAGE, game=session.get("game"),
                           steps=STEPS, faces=FACES)


@app.route("/start", methods=["POST"])
def start():
    names = []
    for i in range(2):  # the board has two ladders
        name = request.form.get(f"name{i}", "").strip()
        names.append(name or f"Player {i + 1}")
    session["game"] = new_game(names)
    return redirect(url_for("index"))


@app.route("/roll", methods=["POST"])
def roll():
    game = session.get("game")
    if game and not game["winner"]:
        play_turn(game)
        session["game"] = game
    return redirect(url_for("index"))


@app.route("/reset", methods=["POST"])
def reset():
    session.pop("game", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
