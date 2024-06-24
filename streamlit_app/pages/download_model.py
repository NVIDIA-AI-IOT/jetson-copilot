import ollama
import streamlit as st
import pandas as pd

import time
import os

import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
# logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)
import utils.func 
import utils.constants as const

# App title
st.set_page_config(page_title="Jetson Copilot - Download Model", menu_items=None)

st.subheader("List of Models Already Downloaded")
with st.spinner('Checking existing models hosted on Ollama...'):
    models = ollama.list()["models"]
    models_data = []
    for model in models:
        models_data.append((
            model['name'],
            model['size'] / 1024 / 1024,
            model['details']['format'],
            model['details']['family'],
            model['details']['parameter_size'],
            model['details']['quantization_level']
        ))
    logging.info(f"{len(models)} models found!")
    df = pd.DataFrame(models_data, columns=[
        'Name', 'Size(MiB)', 'Format', 'Family', 'Parameter', 'Quantization'
    ])
    if len(models) != 0:
        st.dataframe(df.style.format({'Size(MiB)' : "{:,.1f}"}))

def on_newmodel_name_change():
    logging.info("on_newmodel_name_change()")
    newmodel_name = st.session_state.my_newmodel_name
    if newmodel_name.strip():
        logging.info("Name supplied")
        st.session_state.download_model_disabled = False
    else:
        logging.info("Name NOT supplied")
        st.session_state.download_model_disabled = True

def download_model():
    logging.info("download_model()")
    newmodel_name = st.session_state.my_newmodel_name
    with container_status:
        start_time = time.time()
        my_bar = st.progress(0, text="progress text")
        try:
            for res in ollama.pull(newmodel_name, stream=True):
                logging.info(res)
                if 'total' in res and 'completed' in res:
                    total = res['total']
                    completed = res['completed']
                    total_in_mib = total / 1024 / 1024
                    completed_in_mib = completed / 1024 / 1024
                    percent = completed / total
                    my_bar.progress(percent, text=f"Downloading ({completed_in_mib:.1f} MiB / {total_in_mib:.1f} MiB)")
                else:
                    my_bar.progress(100, text=f"{res['status']}")
        except ollama.ResponseError as e:
            # Handle ResponseError specifically
            logging.error(f"A ResponseError occurred: {e}")
            st.error(f"It looks like \"**`{newmodel_name}`**\" is not the right name.", icon="🚨")
            # You might want to log the error or retry the operation
        except Exception as e:
            # Handle any other exceptions
            logging.error(f"An unexpected error occurred: {e}")
            st.error(f"Some other error happend : {e}", icon="🚨")

st.subheader("Download a New Model")
# st.markdown("⚠ Check the model name on [Ollama Library](https://ollama.com/library) page.")
st.info("Check the model name on [Ollama Library](https://ollama.com/library) page.", icon=":material/info:")

model_name = st.text_input(
    "Name of model to download",
    key='my_newmodel_name', 
    on_change=on_newmodel_name_change
)
st.button(
    "Download Model", 
    key='my_button', 
    on_click=download_model, 
    disabled=st.session_state.get("download_model_disabled", True)
)
container_status = st.container()

st.page_link("app.py", label="Back to home", icon="🏠")