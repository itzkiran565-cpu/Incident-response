import os
from dotenv import load_dotenv
from hindsight_client import Hindsight
from groq import Groq

load_dotenv()

hs = Hindsight(
    base_url=os.getenv("HINDSIGHT_BASE_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY")
)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SERVICES = ["payments-api", "auth-service"]


# ============================================================
# MEMORY: RETAIN
# ============================================================

def log_incident(
    service,
    incident_date,
    symptoms,
    root_cause,
    fix,
    minutes,
    runbook,
    effective=True
):
    """
    Stores a resolved incident in Hindsight memory.
    """

    summary = f"""
INCIDENT RECORD
Service: {service}
Date: {incident_date}
Symptoms: {symptoms}
Root cause: {root_cause}
Fix applied: {fix}
Resolution time: {minutes} minutes
Runbook: {runbook}
Fix effective: {effective}
"""

    hs.retain(
        bank_id=service,
        content=summary
    )


def log_outcome_feedback(service, root_cause, fix, worked):
    """
    Stores the outcome of an agent recommendation.
    This is the learning step.
    """

    outcome = "CONFIRMED EFFECTIVE" if worked else "NOT EFFECTIVE"

    note = f"""
INCIDENT OUTCOME FEEDBACK
Service: {service}
Root cause: {root_cause}
Suggested fix: {fix}
Outcome: {outcome}

The on-call engineer reported that this fix was
{'successful' if worked else 'unsuccessful'}.
Future recommendations should {'prioritize' if worked else 'deprioritize'} this approach.
"""

    hs.retain(
        bank_id=service,
        content=note
    )


# ============================================================
# MEMORY: RECALL
# ============================================================

def get_memory_context(service, alert_text):
    """
    Retrieves relevant historical knowledge from Hindsight.
    """

    memory = hs.reflect(
        bank_id=service,
        query=alert_text
    )

    return memory.text


def count_matching_memory(memory_text, keyword):
    """
    Counts how many incident records in the recalled memory
    contain the requested pattern.
    """

    if not memory_text or not keyword:
        return 0

    lines = memory_text.lower().splitlines()

    incident_count = 0

    for line in lines:
        if "incident" in line and keyword.lower() in line:
            incident_count += 1

    # Fallback if Hindsight summarizes the incidents differently
    if incident_count == 0:
        incident_count = memory_text.lower().count(keyword.lower())

    return incident_count


# ============================================================
# AGENT WITH MEMORY
# ============================================================

def get_suggestion(service, alert_text, recurrence_keyword=None):

    memory_text = get_memory_context(
        service,
        alert_text
    )

    match_count = count_matching_memory(
        memory_text,
        recurrence_keyword
    )

    system_prompt = f"""
You are an incident-response agent for production systems.

Your special capability is persistent memory.

You MUST use the historical memory provided below when
diagnosing the new incident.

MEMORY SIGNAL:
{match_count} relevant historical matches were detected.

IMPORTANT RULES:

1. If there is no useful historical evidence:
   - Say that no relevant historical incident was found.
   - Give general troubleshooting steps.
   - Confidence: LOW.

2. If there is one relevant historical incident:
   - Use it as supporting evidence.
   - Mention the previous fix.
   - Confidence: MEDIUM.

3. If there are multiple relevant historical incidents:
   - Explicitly say that this is a recurring pattern.
   - Identify the recurring root cause.
   - Cite previous dates.
   - Cite previous fixes.
   - Cite resolution times when available.
   - Recommend the previously successful approach.
   - Confidence: HIGH.

4. If historical feedback says a previous fix FAILED:
   - Do not recommend it as the first option.
   - Explain that the previous attempt was unsuccessful.

5. Never invent incident dates, fixes or outcomes.
   Only use information present in memory.

6. Clearly separate:
   - Evidence from memory
   - Current diagnosis
   - Recommended action

7. End with:
   Confidence: LOW / MEDIUM / HIGH
"""

    completion = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"""
HISTORICAL MEMORY:

{memory_text}

--------------------------------

CURRENT INCIDENT:

{alert_text}

Analyse this incident using the historical memory.
"""
            }
        ]
    )

    return {
        "response": completion.choices[0].message.content,
        "memory": memory_text,
        "match_count": match_count
    }


# ============================================================
# AGENT WITHOUT MEMORY
# ============================================================

def get_cold_suggestion(alert_text):
    """
    Simulates a stateless agent.

    IMPORTANT:
    This function deliberately does NOT call Hindsight.
    It is used only for the Before/After demonstration.
    """

    system_prompt = """
You are a stateless incident-response assistant.

You have NO access to previous incidents,
previous fixes, previous engineers,
or historical memory.

Analyse ONLY the current alert.

Give:
1. Possible causes
2. Generic troubleshooting steps
3. Confidence

Do not claim knowledge of previous incidents.
"""

    completion = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"Current alert:\n{alert_text}"
            }
        ]
    )

    return completion.choices[0].message.content


# ============================================================
# CLARIFYING QUESTION
# ============================================================

def clarifying_check(service, alert_text):

    memory_text = get_memory_context(
        service,
        alert_text
    )

    completion = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": """
You are an incident-response agent.

Look at the historical memory.

If there are two or more genuinely different plausible
root causes for the current alert, ask ONE short question
that would help the engineer distinguish them.

If the memory clearly points to one cause, output exactly:

NONE

Do not invent causes that are not present in memory.
"""
            },
            {
                "role": "user",
                "content": f"""
Historical memory:

{memory_text}

Current alert:

{alert_text}
"""
            }
        ]
    )

    return completion.choices[0].message.content.strip()


if __name__ == "__main__":

    result = get_suggestion(
        "payments-api",
        "TimeoutError: connection pool exhausted",
        recurrence_keyword="connection pool"
    )

    print(result["response"])