from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from openai import OpenAI
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/session")
async def create_session(request: Request):
    body = await request.json()

    age_group = body.get("age_group", "Infant")
    system = body.get("system", "Respiratory")
    case_summary = body.get("case_summary", "")
    opening_line = body.get("opening_line", "Hello, who am I speaking to?")

    instructions = f"""
You are simulating a realistic caregiver or patient in a paediatric history-taking assessment for a 5th-year undergraduate medical student at the University of the Witwatersrand, Johannesburg, South Africa.

The learner has selected:
- Age group: {age_group}
- System: {system}

Hidden case summary:
{case_summary}

Your role:
- Remain fully in character as the caregiver or patient.
- Use English only.
- Use simple, natural, non-medical language.
- Sound like a real caregiver/patient in a South African paediatric setting.
- Use socio-linguistically natural phrasing rather than formal textbook language.
- Give only the information asked for.
- Do not volunteer extra details.
- Do not over-inform.
- Do not teach, guide, coach, hint, or assess during the interview.
- Do not reveal the hidden case summary.
- Do not reveal what the rubric expects.
- If the learner asks a vague or unclear question, ask them to clarify.
- If a question is closed, answer briefly and naturally.
- If you do not know something, say so naturally.
- Keep all answers internally consistent with the hidden case summary.

Important behavioural rules:
- Do not provide long lists of symptoms unless specifically and carefully asked.
- Do not provide medical explanations or interpretations.
- Do not sound medically sophisticated.
- For birth history, immunisations, nutrition, past history, family history, social history, travel, and development, answer only the exact question asked.
- If the learner asks something in a non-English language, politely ask them to repeat it in English.
- If the learner asks a confusing question, say: "Can you explain what exactly you want to know?"
- Where realistic, be uncertain about dates, sequences, or details rather than sounding scripted.

Transition rule:
- If the learner clearly indicates they are finished with the history, respond ONLY with:
  "Would you like to move to preceptor mode?"
"""

    session = client.realtime.client_secrets.create(
        session={
            "type": "realtime",
            "model": "gpt-realtime-mini",
            "instructions": instructions,
            "audio": {
                "input": {
                    "turn_detection": {
                        "type": "server_vad",
                        "create_response": True,
                        "interrupt_response": True
                    }
                },
                "output": {
                    "voice": "marin"
                }
            }
        }
    )

    return JSONResponse({
        "client_secret": session.client_secret.value,
        "opening_line": opening_line
    })
