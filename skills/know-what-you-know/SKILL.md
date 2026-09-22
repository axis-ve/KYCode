---
name: know-what-you-know
description: Run a short practice session on code the user has already explored, asking one question at a time, waiting for the answer, and correcting precisely. Use when the user asks to be quizzed or tested, wants to check their understanding, asks whether they got something right, or wants to practice predicting what code does. Do not use to explain code the user did not ask to be tested on. Also works in text.
---

# Know What You Know

Help the user find out what they actually understand, by asking rather than telling. Voice is the primary experience: one question, spoken plainly, then silence until they answer.

## Use it when

- The user asks to be quizzed, tested, or checked on code.
- The user wants to practice before changing something themselves.
- The user offers a prediction and asks whether it is right.

## Skip it when

- The user asked for an explanation. Explain it; do not turn the answer into a test.
- The user is mid-task and needs to finish. Practice is never the toll for getting help.
- The code has not been read yet. Read it first, or the questions will be about nothing.

## Run the session

1. Draw every question from code you have actually read in this session, and keep the source open so you can point at the line that settles it.
2. Prefer prediction over recall. "What does this return for a 120 by 80 canvas?" teaches more than "what is this function called?"
3. Ask one question. Stop. Do not hint, do not restate it in an easier form, and do not reveal the answer while waiting.
4. When the answer comes, name the specific step that was right or wrong and show the line that decides it. A wrong answer usually has one wrong assumption; find that one rather than re-teaching the whole path.
5. Follow a miss with a question about the same step, and a hit with a question one step further along.
6. Stop when the user says stop, and stop without a closing quiz about the quiz.

## Question shapes that work

- Predict a return value for concrete inputs.
- Predict which branch runs for a given state.
- Predict what is stored, and in what shape, after one action.
- Predict what breaks if one line is removed.
- Locate the change: "if you wanted this message to read differently, which file would you open?"

## Rules

- Three to five questions is a session. More is an exam.
- Never ask a question the code in front of you cannot settle. No trivia about libraries, history, or style preferences.
- Do not grade with a score or a level. Say what is solid and what to look at again.
- If the user answers something better than the code supports, check the code again before correcting them. They may be right.
- Read-only throughout. Practice never edits the project.
