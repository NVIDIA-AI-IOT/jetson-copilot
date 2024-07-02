import ollama
import openai
import streamlit as st
import pandas as pd

from llama_index.core import VectorStoreIndex, Settings, SimpleDirectoryReader
from llama_index.llms.ollama import Ollama
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import SummaryIndex
from llama_index.readers.web import SimpleWebPageReader
from llama_index.core.readers.base import BaseReader
from llama_index.core import Document
from typing import Dict, Type

from PIL import Image
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

class ExcelReader(BaseReader):
    def load_data(self, file_path: str, extra_info: dict = None):
        data = pd.read_excel(file_path).to_string()
        return [Document(text=data, metadata=extra_info)]
    
DEFAULT_FILE_READER_CLS: Dict[str, Type[BaseReader]] = {
    ".xlsx": ExcelReader,
    ".xls": ExcelReader,
}

def on_settings_change():
    logging.info(" --- settings updated ---")

def on_local_model_change():
    Settings.embed_model = OllamaEmbedding(model_name=st.session_state.my_local_model)
    logging.info(f" --- Settings.embed_model=OllamaEmbedding(model_name={st.session_state.my_local_model}) ---")

def on_openai_model_change():
    Settings.embed_model = OpenAIEmbedding(model_name=st.session_state.my_openai_model, dimensions=1024)
    logging.info(f" --- Settings.embed_model=OpenAIEmbedding(model_name={st.session_state.my_openai_model}) ---")

def on_indexname_change():
    name = st.session_state.my_indexname
    name = utils.func.make_valid_directory_name(name)
    if os.path.exists(os.path.join(const.INDEX_ROOT_PATH, name)):
        with container_name:
            st.error('The title name is not valid', icon="🚨")
    else:
        st.session_state.index_path_to_be_created = f"{const.INDEX_ROOT_PATH}/{name}"
        st.session_state.index_name = f"{name}"
        with container_name:
            st.markdown(f"`{st.session_state.index_path_to_be_created}` will be created")

def on_docspath_change():
    logging.info("### on_docspath_change")
    st.session_state['docpath_untouched'] = False
    dir = st.session_state.docspath
    with container_docs:
        with st.spinner('Checking files under the directory...'):
            files = utils.func.get_files_with_extensions(dir, const.SUPPORTED_FILE_TYPES)
            total_docs_size = utils.func.get_total_size_mib(dir)
            md = f"**`{len(files)}`** files found! (Total file size: **`{total_docs_size:,.2f}`** MiB)"
            logging.info(f"{len(files)} files found!")
            df = pd.DataFrame(files, columns=['Filename', 'Size (KiB)'])
            st.markdown(md)
            st.session_state.num_of_files_to_read = len(files)
            if len(files) != 0:
                st.dataframe(df.style.format({'Size (KiB)' : "{:,.1f}"}))

def on_urllist_change():
    urls = st.session_state.my_urllist
    if utils.func.check_urls(urls):
        st.session_state.num_of_urls_to_read = utils.func.count_urls(urls)
        with container_urls:
            st.success(f"{utils.func.count_urls(urls)} URLs supplied.", icon="✅")
        st.session_state.urllist = utils.func.extract_urllist(urls)
    else:
        st.session_state.num_of_urls_to_read = 0
        with container_urls:
            st.error("Invalid URL(s) contained.", icon="🚨")
        st.session_state.ready_to_index = False

def check_if_ready_to_index():
    logging.info("### check_if_ready_to_index()")
    if hasattr(st.session_state, "index_path_to_be_created"):
        is_name_ready = len(st.session_state.index_path_to_be_created)
    else:
        is_name_ready = False
    logging.info(f"is_name_ready: {is_name_ready}")
    if hasattr(st.session_state, "num_of_files_to_read"):
        num_of_files = st.session_state.num_of_files_to_read
    else:
        num_of_files = 0
    logging.info(f"num_of_files : {num_of_files}")
    if not hasattr(st.session_state, "num_of_urls_to_read"):
        st.session_state.num_of_urls_to_read = 0
    num_of_urls = st.session_state.num_of_urls_to_read
    logging.info(f"num_of_urls  : {num_of_urls}")
    if is_name_ready and (num_of_files or num_of_urls):
        logging.info("### check_if_ready_to_index() ---> Ready")
        st.session_state.index_button_disabled = False

# App title
st.set_page_config(page_title="Jetson Copilot - Build Index", menu_items=None)

### Building Index with Embedding Model
def index_data():
    with container_status:
        start_time = time.time()
        with st.status("Indexing documents..."):
            logging.info(f"Setting Embedding model... {Settings.embed_model}")
            docs = []
            web_docs = []
            if st.session_state.num_of_files_to_read != 0:
                reader = SimpleDirectoryReader(input_dir=st.session_state.docspath, recursive=True)
                st.write(    "Loading local documents...")
                logging.info("Loading local documents...")
                docs = reader.load_data()
                st.write(    f"{len(docs)} local documents loaded.")
                logging.info(f"{len(docs)} local documents loaded.")
                st.write(    "Building Index from local docs (using GPU)...")
                logging.info("Building Index from local docs (using GPU)...")
                index = VectorStoreIndex.from_documents(docs)
            if st.session_state.num_of_urls_to_read != 0:
                st.write(    "Loading web documents...")
                logging.info("Loading web documents...")
                web_docs = SimpleWebPageReader(html_to_text=True).load_data(st.session_state.urllist)
                st.write(    f"{len(web_docs)} web documents loaded.")
                logging.info(f"{len(web_docs)} web documents loaded.")
                logging.info(f"len(web_docs): {len(web_docs)}")
                logging.info(f"web_docs[0]  : {web_docs[0]}")
                st.write(    "Building Index from web docs (using GPU)...")
                logging.info("Building Index from web docs (using GPU)...")
                if 'index' not in locals():
                    index = VectorStoreIndex.from_documents(web_docs)
                else:
                    for d in web_docs:
                        index.insert(document = d)
            st.write(    "Saving the built index to disk...")
            logging.info("Saving the built index to disk...")
            index.storage_context.persist(persist_dir=st.session_state.index_path_to_be_created)
            st.write(    "Indexing done!")
            logging.info("Indexing done!")
        end_time = time.time()
        elapsed_time = end_time - start_time
    
    total_size_mib = utils.func.get_total_size_mib(st.session_state.index_path_to_be_created)

    md = f"""
    Index named **"{st.session_state.index_name}"** was built from **`{len(docs)}` local** documents and **`{len(web_docs)}` online** documents!

    The index is saved under `{st.session_state.index_path_to_be_created}` and the total size of this index is **`{total_size_mib:.2f}`** MiB. 

    The indexing task took **`{elapsed_time:.1f}`** seconds to complete.
    """

    with container_result:
        st.markdown(md)
        logging.info(md)

# Side bar
with st.sidebar:
    st.title("Building Index")
    st.info('Build your own custom Index based on your local/online documents.')

    st.subheader("Embedding Model")
    t1,t2 = st.tabs(['Local','OpenAI'])
    with t1:
        models = [model["name"] for model in ollama.list()["models"]]
        st.selectbox("Choose local embedding model", models, index=models.index("mxbai-embed-large:latest"), key='my_local_model', on_change=on_local_model_change)
    with t2:
        openai.api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
        os.environ["OPENAI_API_KEY"] = openai.api_key
        logging.info(f"> openai.api_key = {openai.api_key}")
        st.selectbox("Choose OpenAI embedding model", ["-- Choose from below --", "text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"], index=0, key='my_openai_model', on_change=on_openai_model_change)
    use_customized_chunk = st.toggle("Customize chunk parameters", value=False)
    if use_customized_chunk:
        Settings.chunk_size = st.slider("Chunk size", 100, 5000, 1024, key='my_chunk_size', on_change=on_settings_change)
        Settings.chunk_overlap = st.slider("Chunk overlap", 10, 500, 50, key='my_chunk_overlap', on_change=on_settings_change)
        logging.info(f"> Settings.chunk_size    = {Settings.chunk_size}")
        logging.info(f"> Settings.chunk_overlap = {Settings.chunk_overlap}")

st.subheader("Index Name")
index_name = st.text_input("Enter the name for your new index", key='my_indexname', on_change=on_indexname_change)
container_name = st.container()

st.subheader('Local documents')
subdirs = utils.func.get_subdirectories(const.DOC_ROOT_PATH)
st.selectbox("Select the path to the local directory that you had stored your documents", subdirs, key='docspath', on_change=on_docspath_change)
container_docs = st.container()
if 'docpath_untouched' not in st.session_state:
    st.session_state['docpath_untouched'] = True
    st.session_state.num_of_files_to_read = 0
if len(subdirs) != 0 and st.session_state['docpath_untouched']:
    logging.info(f"################ st.session_state['docpath_untouched']: {st.session_state['docpath_untouched']}")
    on_docspath_change()

st.subheader('Online documents')
list_urls = st.text_area("List of URLs (one per a line)", key='my_urllist', on_change=on_urllist_change)
container_urls = st.container()

st.warning("Check the model and its configurations on the sidebar (⬅️) and then hit the button below to build a new Index.", icon="⚠️")

container_settings = st.container()

check_if_ready_to_index()
logging.info(f"Setting Embedding model... {Settings.embed_model}")

st.button("Build Index", on_click=index_data, key='my_button', disabled=st.session_state.get("index_button_disabled", True))
container_status = st.container()
container_result = st.container()

st.page_link("app.py", label="Back to home", icon="🏠")