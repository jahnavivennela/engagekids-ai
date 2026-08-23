import streamlit as st

from db import get_children
from milestones_data import AGE_BANDS, milestones_summary_text

# Children are added under "Select Child" and saved with an age_group string
# like "3-5 years" (free text) — map anything we don't recognise to the
# closest of our 5 dropdown bands so a saved child still gets a sensible default.
def _closest_age_band(stored_age_group: str) -> str:
    if not stored_age_group:
        return AGE_BANDS[0]
    t = stored_age_group.lower()
    if "0" in t and "1" in t:
        return "0-1 years"
    if t.strip() in [b.lower() for b in AGE_BANDS]:
        return next(b for b in AGE_BANDS if b.lower() == t.strip())
    if "1" in t and "2" in t:
        return "1-2 years"
    if "2" in t and "3" in t:
        return "2-3 years"
    if "4" in t or "5" in t:
        return "4-5 years"
    if "3" in t:
        return "3-4 years"
    return AGE_BANDS[0]


def learning_story_tab(client):

    st.subheader("📖 Learning Story Generator")

    st.markdown(
        "*Describe what the child did — get a documented learning story ready to use*"
    )

    children = get_children()
    selected_child = None

    if children:
        options = [f"{c['name']}" for c in children] + ["Someone not in this list"]
        choice = st.selectbox(
            "Child's name",
            options,
            key="story_child_choice",
        )
        if choice != "Someone not in this list":
            selected_child = next(c for c in children if c["name"] == choice)
            child_name = selected_child["name"]
            if selected_child.get("interests"):
                st.caption(f"On file for {child_name}: {selected_child['interests']}")
        else:
            child_name = st.text_input("Child's name (or initials)", key="story_child_name_other")
    else:
        st.caption("No children added yet under Select Child — you can still write a story using just a name/initials below.")
        child_name = st.text_input("Child's name (or initials)", key="story_child_name_other")

    default_age_index = 0
    if selected_child:
        default_band = _closest_age_band(selected_child.get("age_group", ""))
        default_age_index = AGE_BANDS.index(default_band)

    age_group = st.selectbox(
        "Age group",
        AGE_BANDS,
        index=default_age_index,
        key="story_age_group"
    )

    observation = st.text_area(
        "What did you observe? Describe simply, in your own words.",
        placeholder=(
            "e.g. Spent 15 minutes stacking blocks, kept trying different "
            "orders after they fell, didn't give up, laughed when it worked."
        ),
        key="story_observation"
    )

    tone = st.selectbox(
        "Tone",
        ["Warm and narrative", "Concise and formal"],
        key="story_tone"
    )

    if st.button(
        "Generate Learning Story",
        type="primary",
        key="story_button"
    ):

        if not observation.strip():
            st.warning("Please describe what you observed first.")
            return

        with st.spinner("Writing learning story..."):

            milestones_context = milestones_summary_text(age_group)

            system_prompt = f"""
            You are an expert early childhood educator who writes
            documented learning stories for children's portfolios,
            aligned to the Early Years Learning Framework (EYLF)
            Version 2.0 Australia.

            A good learning story:
            - Describes what the child actually did, specifically, not
              generic phrases like "engaged in play"
            - Identifies what the child was learning or practising in
              that moment
            - Links clearly to relevant EYLF outcomes
            - Is written in a way that is meaningful to parents, not
              just other educators
            - Is honest and specific to the observation given, not
              padded with generic developmental language

            Reference developmental milestones for this age band (from the
            Developmental Milestones and EYLF/NQS practice-based resource) —
            use this to ground "what this shows" in realistic, age-appropriate
            language, not to force the observation to match every bullet:
            {milestones_context}
            """

            name_text = child_name.strip() if child_name and child_name.strip() else "The child"
            interests_line = f"\nKnown interests: {selected_child['interests']}" if selected_child and selected_child.get("interests") else ""

            prompt = f"""
            Child: {name_text}
            Age group: {age_group}
            Tone: {tone}{interests_line}

            Observation:
            {observation}

            Write a documented learning story in this format:

            LEARNING STORY TITLE:

            WHAT HAPPENED:
            (Written in the given tone, specific to the observation)

            WHAT THIS SHOWS ABOUT {name_text.upper()}'S LEARNING:

            EYLF OUTCOMES ADDRESSED:

            WHAT'S NEXT:
            (One suggestion for extending this learning)
            """

            try:

                message = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    reasoning_effort="low",
                    max_tokens=1500,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                )
                response = (message.choices[0].message.content or "").strip()
                if not response:
                    response = "Couldn't generate the story this time — please try again."
                st.success("Story ready")
                st.markdown(response)

            except Exception as e:

                st.error(
                    f"Learning story API error: {e}"
                )