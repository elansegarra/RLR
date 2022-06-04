import streamlit as st
import pandas as pd

###########################################################################
#### Function Definitions #################################################
###########################################################################



###########################################################################
#### App - Inputting Data Files ###########################################
###########################################################################

st.title("Load and Initialize Data Files")
with st.expander("Left Data Set:", expanded = True):
    # Input the first data file
    data_file_L = st.file_uploader("Upload file", key = "L_file",
                                    accept_multiple_files=False, type = ['csv', 'dta'])
    if data_file_L is None:
        st.write("")
    else:
        # Open the data file and print the first few rows
        dfL = pd.read_csv(data_file_L)
        st.dataframe(dfL.head())

        # Let the user determine which fields make up the row id
        dfL_id_vars = st.multiselect("Choose which fields uniquely identify rows:", dfL.columns)
        
        # Verify that passed variables uniquely identify a row
        if len(dfL_id_vars) == 0:
            msg = "** Please choose which columns uniquely identify each row. **"
            msg_text = f'<p style="color:Red;">{msg}</p>'
            st.session_state['data_L_loaded'] = False
        elif dfL.set_index(dfL_id_vars).index.is_unique:
            msg = "Variables chosen are valid identifiers. Loading of the left data set is complete."
            msg_text = f'<p style="color:Green;">{msg}</p>'
            st.session_state['data_L_loaded'] = True
        else:
            msg = "** Variables chosen do not uniquely identify rows. **"
            msg_text = f'<p style="color:Red;">{msg}</p>'
            st.session_state['data_L_loaded'] = False
        st.markdown(msg_text, unsafe_allow_html=True)


with st.expander("Right Data Set:", expanded = True):
    # Input the second data file
    data_file_R = st.file_uploader("Upload file", key = "R_file",
                                    accept_multiple_files=False, type = ['csv', 'dta'])
    if data_file_R is None:
        st.write("")
    else:
        # Open the data file and print the first few rows
        dfR = pd.read_csv(data_file_R)
        st.dataframe(dfR.head())

        # Let the user determine which fields make up the row id
        dfR_id_vars = st.multiselect("Choose which fields uniquely identify rows:", dfR.columns)
        
        # Verify that passed variables uniquely identify a row
        if len(dfR_id_vars) == 0:
            msg = "** Please choose which columns uniquely identify each row. **"
            msg_text = f'<p style="color:Red;">{msg}</p>'
            st.session_state['data_R_loaded'] = False
        elif dfR.set_index(dfR_id_vars).index.is_unique:
            msg = "Variables chosen are valid identifiers. Loading of the right data set is complete."
            msg_text = f'<p style="color:Green;">{msg}</p>'
            st.session_state['data_R_loaded'] = True
        else:
            msg = "** Variables chosen do not uniquely identify rows. **"
            msg_text = f'<p style="color:Red;">{msg}</p>'
            st.session_state['data_R_loaded'] = False
        st.markdown(msg_text, unsafe_allow_html=True)

link_pairs = [[2,'D'],[6,'C'],[4,'G']]
if 'curr_link_pair' not in st.session_state:
    st.session_state['curr_link_pair'] = 0