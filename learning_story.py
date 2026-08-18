import streamlit as st
def learning_story_tab(client):

    st.subheader("📖 Learning Story Generator")

    st.markdown(
        "*Describe what the child did — get a documented learning story ready to use*"
    )

    child_name = st.text_input(
        "Child's name (or initials)",
        key="story_child_name"
    )

    age_group = st.selectbox(
        "Age group",
        ["Babies 0-1 years", "Toddlers 1-3 years", "Preschool 3-5 years"],
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

            system_prompt = """
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
            """

            name_text = child_name.strip() if child_name.strip() else "The child"

            prompt = f"""
            Child: {name_text}
            Age group: {age_group}
            Tone: {tone}

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
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )

                response = message.choices[0].message.content

                st.success("Learning story ready")

                st.markdown(response)

            except Exception as e:

                st.error(
                    f"Learning story API error: {e}"
                )