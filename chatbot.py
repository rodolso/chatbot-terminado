import streamlit as st
import replicate
import os

# Código refactorizado de https://github.com/sfc-gh-cnantasenamat/streamlit-replicate-app
# y https://github.com/a16z-infra/llama2-chatbot

# Configuración del proyecto
APP_NAME = 'My First Chatbot'
MODEL_NAME = 'Meta Llama 3 8B Instruct'
MODEL_ENDPOINT = 'meta/meta-llama-3-8b-instruct'
MODEL_DOC_LINK = 'https://replicate.com/meta/meta-llama-3-8b-instruct'

# Configuración inicial
st.set_page_config(
    page_title=APP_NAME, 
    page_icon=':robot:'
    )

# Inicialización de variables
default_system_prompt = '''You are a helpful assistant.
You do not respond as "User" or pretend to be "User".
You only respond once as "Assistant".'''

default_start_message = '¡Hola!, ¿en qué puedo ayudarte hoy?'

if 'messages' not in st.session_state:
    st.session_state.messages = [{'role': 'assistant', 'content': default_start_message}]
if 'system_prompt' not in st.session_state:
    st.session_state.system_prompt = default_system_prompt

# Barra lateral
with st.sidebar:
    st.title(APP_NAME)
    
    # API token
    try:
        if st.secrets and 'REPLICATE_API_TOKEN' in st.secrets:
            replicate_api_token = st.secrets['REPLICATE_API_TOKEN']
            st.success('API token already provided!', icon='✅')
        else:
            raise KeyError
    except:
        replicate_api_token = st.text_input('Enter Replicate API token:', type='password')
        if not (replicate_api_token and replicate_api_token.startswith('r8_') and len(replicate_api_token) == 40):
            st.warning('Please enter a valid Replicate API token!', icon='⚠️')
            if replicate_api_token:
                st.info("Replicate tokens start with 'r8_' and are 40 characters long")
        else:
            st.success('Proceed to chat!', icon='👉')
    
    if replicate_api_token:
        os.environ['REPLICATE_API_TOKEN'] = replicate_api_token
    
    # System Prompt editable
    st.subheader('System Prompt')

    def on_system_prompt_change():
        st.session_state.system_prompt = st.session_state.system_prompt_textarea

    st.text_area(
        'Edit the prompt that guides the model:',
        value=st.session_state.system_prompt,
        height=150,
        key='system_prompt_textarea',
        on_change=on_system_prompt_change
    )
    
    # Información del modelo
    st.subheader('Model')
    st.info(f'Using {MODEL_NAME}')
    st.markdown(f'👉 [Learn more about this model]({MODEL_DOC_LINK}) 👈')

    # Botón para limpiar historial 
    def clear_chat_history():
        st.session_state.messages = [{'role': 'assistant', 'content': default_start_message}]

    st.button('Clear Chat', on_click=clear_chat_history, use_container_width=True)

# Generación de respuestas
def generate_response():
    conversation_context = f'System: {st.session_state.system_prompt}\n\n'
    for dict_message in st.session_state.messages:
        role = dict_message.get('role', '')
        if role in ('user', 'assistant'):
            conversation_context += f'{role.capitalize()}: {dict_message["content"]}\n\n'
    
    input_params = {
        'prompt': f'{conversation_context}Assistant: '
        }
    
    try:
        for event in replicate.stream(MODEL_ENDPOINT, input=input_params):
            yield str(event)
    except replicate.exceptions.ReplicateError as e:
        yield f'Replicate API Error: {e}'
    except Exception as e:
        yield f'Unexpected error: {e}. Please check your connection and API token.'

# Entrada del usuario
if prompt := st.chat_input('Type your message here...', disabled=not replicate_api_token):
    st.session_state.messages.append({'role': 'user', 'content': prompt})

# Mostrar mensajes
for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.write(message['content'])

# Generar respuesta
if st.session_state.messages and st.session_state.messages[-1]['role'] == 'user':
    with st.chat_message('assistant'):
        with st.spinner('Thinking...'):
            response = generate_response()
            full_response = st.write_stream(response)
    st.session_state.messages.append({'role': 'assistant', 'content': full_response})
