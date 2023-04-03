import streamlit as st
import openai
import time
from prompts import prompt_template, summary_prompt, system_message
from emailing import send_email, add_html_blocks, github_markup_to_html


def initiate_states():

    # Create default session states
    if 'messages' not in ss:
        ss['messages'] = [
            {"role": "system", "content": system_message},
        ]

    if 'state' not in ss:
        ss['state'] = "Intro"

    if 'model_reply' not in ss:
        ss['model_reply'] = ""

    if 'user_reply' not in ss:
        ss['user_reply'] = ""

    if 'current_topic' not in ss:
        ss['current_topic'] = {}

    if 'topics' not in ss:
        ss['topics'] = {}

    if 'counts' not in ss:
        ss['counts'] = 1

    if 'user_info' not in ss:
        ss['user_info'] = {}

    if 'load_questions' not in ss:
        ss['load_questions'] = False


def next_question():
    if ss.counts <= 4:
        local_prompt = ss.user_reply
        update_messages(local_prompt)
        ss.counts = ss.counts + 1
        ss.user_reply = ""
        st.session_state["reply"] = ""
    else:
        ss.state = 'Summary'
        update_messages(summary_prompt)


def update_messages(local_prompt):
    ss.messages.append({"role": "assistant", "content": ss.model_reply})
    ss.messages.append({"role": "user", "content": local_prompt})
    ss.model_reply = ""
    ss.user_reply = ""


def update_model_response():
    """Calls the OpenAI API and updates model_response_display"""
    openai.api_key = st.secrets['SECRET_KEY']

    qu_attempts = 1
    while qu_attempts <= 10:

        try:
            response = []
            for resp in openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=ss.messages,
                    stream=True):
                if 'content' in resp['choices'][0]['delta']:
                    response.append(resp['choices'][0]['delta']['content'])
                    result = "".join(response).strip()
                    model_response_display.markdown(f'{result}')

            ss.model_reply = "".join(response).strip()
            qu_attempts = 11

        except:
            print(f"openai error, attempt {qu_attempts}")
            qu_attempts += 1
            time.sleep(2)

    st.experimental_rerun()


# Initiate states and variables
st.set_page_config(page_title="Stress Coach | Change Voyage", page_icon=":relieved:", layout="centered",
                   initial_sidebar_state="collapsed", menu_items=None)

ss = st.session_state
initiate_states()


# Update display, dependent on state
match ss.state:

    case "Intro":
        st.image('cv_logo.png', width=150)

        st.header('Stress Coach')

        st.markdown('Please share a stress in your professional or personal life that you would like to discuss today. Everything shared is confidential.')

        max_questions = 4

        stressor = st.text_area('Stressor', label_visibility='collapsed',
                                placeholder='Please share as much detail as possible, '
                                            'including physical, mental and emotional effects.')

        if st.button("Next", type='primary'):
            ss.state = 'Questions'
            prompt = prompt_template.format(stressor=stressor)
            update_messages(prompt)
            ss.user_reply = ""
            st.experimental_rerun()

    case "Questions":

        if ss.model_reply == "":
            model_response_display = st.empty()
            update_model_response()
        else:
            model_response_display = st.markdown(ss.model_reply)

        if ss.counts <= 4:
            ss.user_reply = st.text_area("Response:", label_visibility='collapsed',
                                         placeholder="Take your time to think about your reply.",
                                         key='reply')

        st.button("Next", on_click=next_question, type='primary')

    case "Summary":

        st.image('cv_logo.png', width=100)
        actions = []
        response = ['Error: No actions loaded...']

        if ss.model_reply == "":
            model_response_display = st.empty()
            update_model_response()
            st.experimental_rerun()
        else:
            response = ss.model_reply.split('::Action::')
            model_response_display = st.markdown(response[0])

            for i, action in enumerate(response[1:]):
                action_text = action.strip()
                actions.append("")
                actions[i] = st.text_area(label=str(i), label_visibility='collapsed', value=action_text)

        col1, col2 = st.columns(2)

        with col1:
            email_address = st.text_input("Email address", label_visibility='collapsed', placeholder="Enter your email")
            if st.button("Send me a copy", type='primary'):

                action_bullets = ""
                for action in actions:
                    action_bullets = action_bullets + '* ' + action + '\n\n'

                html_blocks = {
                    '{summary}': github_markup_to_html(response[0]),
                    '{actions}': github_markup_to_html(action_bullets)
                }

                html_file_path = 'email_template.html'

                updated_html = add_html_blocks(html_file_path, html_blocks)

                if send_email("Stress Management - Discussion Summary and Actions", updated_html, email_address):
                    st.text("Email sent!")
                else:
                    st.text("Problem with email address provided. Email not sent.")

        with col2:
            if st.button("Discuss another topic"):
                ss.state = 'Intro'
                ss.counts = 1
                st.experimental_rerun()

