import streamlit as st
from datetime import date

from agent import (
    get_suggestion,
    get_cold_suggestion,
    log_incident,
    log_outcome_feedback,
    clarifying_check
)


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Incident Response Agent",
    page_icon="🚨",
    layout="wide"
)

st.title("🚨 Incident Response Agent")

st.caption(
    "On-call assistant powered by Hindsight memory — "
    "learns from how previous incidents were actually resolved."
)


# ============================================================
# TOP METRICS
# ============================================================

col1, col2, col3 = st.columns(3)

col1.metric(
    "Historical incidents",
    "6"
)

col2.metric(
    "Services with memory",
    "2"
)

col3.metric(
    "Memory capability",
    "RETAIN → RECALL"
)


st.divider()


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🚨 Live Alert",
        "🧠 Before / After Memory",
        "🔎 Clarifying Question",
        "💾 Log & Learn"
    ]
)


# ============================================================
# TAB 1 — LIVE ALERT
# ============================================================

with tab1:

    st.subheader("Live production alert")

    service = st.selectbox(
        "Service",
        ["payments-api", "auth-service"]
    )

    alert = st.text_area(
        "Alert / error message",
        value=(
            "TimeoutError: connection pool exhausted, "
            "payments-api"
        ),
        height=100
    )

    keyword = st.text_input(
        "Pattern to investigate",
        value="connection pool"
    )

    if st.button(
        "Recall & Diagnose",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "Recalling historical incidents from Hindsight..."
        ):

            result = get_suggestion(
                service,
                alert,
                recurrence_keyword=keyword
            )

        st.success(
            f"Hindsight recalled "
            f"{result['match_count']} relevant memory matches."
        )

        # ----------------------------------------------------
        # MEMORY TRACE
        # ----------------------------------------------------

        st.subheader("🧠 Hindsight Memory Trace")

        trace1, trace2, trace3, trace4 = st.columns(4)

        trace1.markdown(
            "**1. RECALL**\n\n"
            "Historical incidents retrieved"
        )

        trace2.markdown(
            "**2. CORRELATE**\n\n"
            "Similar patterns identified"
        )

        trace3.markdown(
            "**3. LEARN**\n\n"
            "Previous outcomes considered"
        )

        trace4.markdown(
            "**4. RECOMMEND**\n\n"
            "Action based on history"
        )

        with st.expander(
            "View recalled Hindsight memory",
            expanded=False
        ):
            st.code(
                result["memory"],
                language="text"
            )

        # ----------------------------------------------------
        # AGENT RESPONSE
        # ----------------------------------------------------

        st.subheader("🤖 Agent Recommendation")

        st.info(
            result["response"]
        )


# ============================================================
# TAB 2 — BEFORE / AFTER
# ============================================================

with tab2:

    st.subheader(
        "Same incident — with and without persistent memory"
    )

    st.write(
        "This demonstrates the core difference between a "
        "stateless agent and an agent powered by Hindsight."
    )

    comparison_alert = st.text_area(
        "Incident used for comparison",
        value=(
            "TimeoutError: connection pool exhausted, "
            "payments-api"
        ),
        height=100,
        key="comparison_alert"
    )

    if st.button(
        "Run Before / After Comparison",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "Running the same incident through both agents..."
        ):

            cold_result = get_cold_suggestion(
                comparison_alert
            )

            warm_result = get_suggestion(
                "payments-api",
                comparison_alert,
                recurrence_keyword="connection pool"
            )

        cold_col, warm_col = st.columns(2)

        # ----------------------------------------------------
        # WITHOUT MEMORY
        # ----------------------------------------------------

        with cold_col:

            st.markdown(
                "### ❌ WITHOUT HINDSIGHT"
            )

            st.caption(
                "Stateless agent — current alert only"
            )

            st.warning(
                cold_result
            )

        # ----------------------------------------------------
        # WITH MEMORY
        # ----------------------------------------------------

        with warm_col:

            st.markdown(
                "### ✅ WITH HINDSIGHT"
            )

            st.caption(
                "Agent can recall previous incidents"
            )

            st.success(
                warm_result["response"]
            )

            st.metric(
                "Relevant memories recalled",
                warm_result["match_count"]
            )

        st.divider()

        st.markdown(
            "### What changed?"
        )

        st.write(
            "The memory-enabled agent can use previous "
            "root causes, fixes and outcomes instead of "
            "starting from zero."
        )


# ============================================================
# TAB 3 — CLARIFYING QUESTION
# ============================================================

with tab3:

    st.subheader(
        "🔎 Agent asks when historical evidence is ambiguous"
    )

    st.write(
        "When memory contains multiple plausible explanations, "
        "the agent should ask the engineer for additional context "
        "instead of blindly choosing one."
    )

    ambiguous_alert = st.text_area(
        "Ambiguous alert",
        value=(
            "Increased latency and intermittent errors "
            "on payments-api"
        ),
        height=100
    )

    if st.button(
        "Check Historical Ambiguity",
        use_container_width=True
    ):

        with st.spinner(
            "Checking historical memory..."
        ):

            question = clarifying_check(
                "payments-api",
                ambiguous_alert
            )

        if question == "NONE":

            st.success(
                "Historical memory points to a sufficiently clear pattern. "
                "No clarification is required."
            )

        else:

            st.warning(
                f"🤖 Agent asks:\n\n{question}"
            )


# ============================================================
# TAB 4 — LOG & LEARN
# ============================================================

with tab4:

    st.subheader(
        "💾 Add a resolved incident to memory"
    )

    st.write(
        "Every resolved incident becomes future knowledge."
    )

    service = st.selectbox(
        "Service",
        ["payments-api", "auth-service"],
        key="log_service"
    )

    incident_date = st.date_input(
        "Incident date",
        value=date.today()
    )

    symptoms = st.text_input(
        "Symptoms",
        placeholder="Example: p99 latency spike, 5xx errors..."
    )

    root_cause = st.text_input(
        "Root cause",
        placeholder="Example: connection leak in retry logic..."
    )

    fix = st.text_input(
        "Fix applied",
        placeholder="Example: rollback deploy #482..."
    )

    minutes = st.number_input(
        "Time to resolve (minutes)",
        min_value=1,
        value=30
    )

    runbook = st.text_input(
        "Runbook used",
        placeholder="Example: runbook-db-pool-exhaustion.md"
    )

    if st.button(
        "💾 Save Incident to Hindsight",
        type="primary",
        use_container_width=True
    ):

        log_incident(
            service,
            str(incident_date),
            symptoms,
            root_cause,
            fix,
            minutes,
            runbook
        )

        st.success(
            "Incident retained in Hindsight memory."
        )

        st.info(
            "This incident can now influence future recommendations."
        )


    st.divider()


    # --------------------------------------------------------
    # FEEDBACK
    # --------------------------------------------------------

    st.subheader(
        "🔄 Feed the outcome back to the agent"
    )

    st.write(
        "This closes the learning loop: "
        "recommendation → real outcome → memory."
    )

    feedback_service = st.selectbox(
        "Service",
        ["payments-api", "auth-service"],
        key="feedback_service"
    )

    feedback_cause = st.text_input(
        "Root cause",
        key="feedback_cause"
    )

    feedback_fix = st.text_input(
        "Fix that was attempted",
        key="feedback_fix"
    )

    worked = st.radio(
        "Did the fix actually work?",
        ["Yes — resolved", "No — failed"]
    )

    if st.button(
        "🔄 Record Outcome",
        use_container_width=True
    ):

        log_outcome_feedback(
            feedback_service,
            feedback_cause,
            feedback_fix,
            worked == "Yes — resolved"
        )

        if worked == "Yes — resolved":

            st.success(
                "Outcome stored. Hindsight can now use this "
                "successful resolution in future incidents."
            )

        else:

            st.warning(
                "Failed outcome stored. Future recommendations "
                "will be told to deprioritize this approach."
            )