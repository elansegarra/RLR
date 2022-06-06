import streamlit as st
import pandas as pd
from backend.rlr import rlr

# To run from command line (in root folder): "streamlit run rlr_st.py --server.port 8889"

st.set_page_config(page_title="RLR: Record Linkage Review", page_icon="📈", 
                    layout="centered", initial_sidebar_state="auto", menu_items=None)

###########################################################################
#### Function Definitions #################################################
###########################################################################


###########################################################################
#### App - Sidebar ########################################################
###########################################################################

# Initializing rlr backend
if 'rlr' not in st.session_state:
    st.session_state['rlr'] = rlr()

###########################################################################
#### App - Main Page ######################################################
###########################################################################

st.title("RLR: Record Linkage Review")