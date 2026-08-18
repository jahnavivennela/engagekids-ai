import streamlit as st
def observation_tab(client):
    st.subheader("👀 Situation-Based Support")
    st.markdown("*Describe what's happening right now — get an immediate, practical response*")

    situation = st.text_area(
        "What's happening right now?",
        placeholder="e.g. Two children fighting over a toy, one keeps crying even after redirecting."
    )

    intensity = st.select_slider(
        "How intense is it right now?",
        options=["Mild — manageable", "Escalating — not responding to first attempts", "High — crying/shouting/throwing, other children affected"]
    )

    considerations = st.multiselect(
        "Anything specific to consider for this group?",
        [
            "Child with additional needs / neurodivergent child",
            "Hyperactive / high energy child",
            "Child with low physical activity / reluctant to engage",
            "Multiple language backgrounds in the room",
            "Limited resources available right now"
        ]
    )

    if st.button("Get Guidance", type="primary", key="obs_button"):
        with st.spinner("Thinking..."):

            system_prompt = """You are an expert early childhood educator specialising in real classroom
            behaviour management under the EYLF Version 2.0 Australia. You are talking to an educator who is
            currently IN the situation, not reading a textbook. Match your advice to the intensity given:
            - Mild: standard redirection is fine
            - Escalating: give a firmer, more physical/structural response (e.g. separating children, removing
              the trigger item, changing the environment) — not just calmer words, since calm words already failed
            - High: prioritise safety first (physical intervention if needed, removing other children from the
              area, calling for a second educator), THEN emotional regulation. Do not suggest calm verbal
              redirection as the first step if the situation is already high intensity — it has already failed by
              that point in real classrooms.
            Never suggest an approach that assumes children will simply listen and calm down on request."""

            considerations_text = ", ".join(considerations) if considerations else "no specific considerations noted"

            prompt = f"""Situation: {situation}
            Intensity: {intensity}
            Specific considerations: {considerations_text}

            Format your response as:

            IMMEDIATE ACTION (physical/safety steps first if intensity is high):

            WHAT TO SAY (realistic, not just "let's calm down"):

            IF THEY DON'T RESPOND IN 30 SECONDS:

            HOW TO INCLUDE EVERY CHILD:

            AFTER IT SETTLES (repair/reconnect step):"""

            message = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )

            st.success("Guidance ready")
            st.markdown(message.choices[0].message.content)