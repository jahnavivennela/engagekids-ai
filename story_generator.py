import streamlit as st


def story_generator_tab(client):

    st.subheader("📚 Story Time Generator")

    st.markdown(
        "*Get a short story to tell right now, matched to the moment*"
    )

    age_group = st.selectbox(
        "Age group",
        ["Babies 0-1 years", "Toddlers 1-3 years", "Preschool 3-5 years"],
        key="story_gen_age"
    )

    purpose = st.selectbox(
        "What do you need this story to do right now?",
        [
            "Calm restless or overstimulated children",
            "Re-engage children who are losing interest",
            "Fit today's theme",
            "Help with a transition (e.g. clean up, moving to next activity)",
            "Just for fun / free choice"
        ],
        key="story_gen_purpose"
    )

    theme = st.text_input(
        "Theme or topic (optional)",
        placeholder="e.g. dinosaurs, going to sleep, sharing",
        key="story_gen_theme"
    )

    length = st.select_slider(
        "Length",
        options=["Very short (2-3 min)", "Short (5 min)", "Medium (8-10 min)"],
        key="story_gen_length"
    )

    if st.button(
        "Generate Story",
        type="primary",
        key="story_gen_button"
    ):

        with st.spinner("Writing story..."):

            system_prompt = """
            You are an expert early childhood educator and children's
            storyteller. You write short stories to be told or read
            aloud to young children in real time during a classroom
            session.

            Your stories must be:
            - Age appropriate in language and content
            - Written to be spoken aloud naturally, not read silently
            - Matched precisely to the stated purpose (e.g. a calming
              purpose needs slow pacing and soothing language, a
              re-engagement purpose needs more energy and surprise)
            - Simple enough that an educator can tell it with little
              preparation
            - Include a natural pause point or two where the educator
              can ask the children a question
            """

            theme_text = theme.strip() if theme.strip() else "no specific theme, your choice"

            prompt = f"""
            Age group: {age_group}
            Purpose: {purpose}
            Theme: {theme_text}
            Length: {length}

            Write the story in this format:

            STORY TITLE:

            STORY:
            (Written to be told aloud, matched to the purpose and length)

            WHERE TO PAUSE AND ASK A QUESTION:

            HOW TO TELL IT (tone, pacing, any actions/voices to use):
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
                    f"Story generator API error: {e}"
                )