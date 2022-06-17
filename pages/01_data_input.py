import streamlit as st
import pandas as pd
import json, io, os

st.set_page_config(page_title="RLR: Data Input", page_icon="📈")

###########################################################################
#### Function Definitions #################################################
###########################################################################

def remove_data_file(side):
    """ Removes the data file from the deisgnated side """
    if side == 'l':
        st.session_state['rlr'].dataL_loaded = False
        st.session_state['rlr'].dataL = None
        st.session_state['rlr'].ready_to_review = False
    elif side == 'r':
        st.session_state['rlr'].dataR_loaded = False
        st.session_state['rlr'].dataR = None
        st.session_state['rlr'].ready_to_review = False
    else:
        raise NotImplementedError(f"Unrecognized side, {side}, must by 'l' or 'r'.")

def add_var_group():
    # Add empty var group to end of list of the variable group schema
    var_comp_schema = st.session_state['rlr'].get_var_comp_schema()
    var_comp_schema.append({'name': "", 'lvars': [], 'rvars': []})
    st.session_state['rlr'].set_var_comp_schema(var_comp_schema)

def del_var_group(vargp_index):
    # Delete var group at the passed index in the list of variable group schemas
    var_comp_schema = st.session_state['rlr'].get_var_comp_schema()
    del var_comp_schema[vargp_index]
    st.session_state['rlr'].set_var_comp_schema(var_comp_schema)

###########################################################################
#### App - Sidebar ########################################################
###########################################################################

with st.sidebar:
    input_mech_options = ['Load Piecmeal', 'Local Data Folder']
    input_mech = st.radio("Input Mechanism", input_mech_options)

    # Display upload for entire review packet
    rev_packet = st.file_uploader("Upload Review Packet", key = "rev_packet_file",
                                    accept_multiple_files=False, type = ['json'])
    if rev_packet is None:
        st.write("")
    else:
        # Open the review packet file and load the dictionary into RLR
        rev_packet_dict = json.load(rev_packet)
        st.session_state['rlr'].load_review_packet(rev_packet_dict)
        # st.write(rev_packet_dict)
    
    # Download buttons to save a review packet
    if (st.session_state['rlr'].ready_to_review):
        rev_dict = st.session_state['rlr'].get_review_packet()
        if rev_dict is not None:
            st.write("Download Review Packet")
            with io.BytesIO() as buffer:
                buffer.write(json.dumps(rev_dict, indent = 4).encode())
                st.download_button("Download json", buffer, 
                                    file_name = "review_packet.json")
                st.write("")

###########################################################################
#### App - Inputting Data Files ###########################################
###########################################################################

st.header("Data Loading and Initialization")
with st.expander("Left Data Set:", expanded = True):
    # Checking if left data has already been loaded
    if st.session_state['rlr'].dataL_loaded:
        st.write("Left Data Set Already Loaded")
        st.dataframe(st.session_state['rlr'].dataL.head())
        st.write(f"IDs: {st.session_state['rlr'].id_vars_l}")
        st.button("Load a different data set", key = "reload_l", on_click = remove_data_file, args=('l', ))
    else:
        # Input the first data file
        data_file_L = st.file_uploader("Upload file", key = "L_file",
                                        accept_multiple_files=False, type = ['csv', 'dta'])
        if data_file_L is None:
            st.write("")
        else:
            # Open the data file (after determining type)
            data_ext = os.path.splitext(data_file_L.name)[1]
            if      data_ext == ".csv":   dfL = pd.read_csv(data_file_L)
            elif    data_ext == ".dta":   dfL = pd.read_stata(data_file_L)
            else:                           
                raise NotImplementedError(f"Filetype of {data_path} must be either .csv or .dta")
            # Print the first few rows
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
                st.session_state['rlr'].load_dataset(dfL, dfL_id_vars, 'l')
            else:
                msg = "** Variables chosen do not uniquely identify rows. **"
                msg_text = f'<p style="color:Red;">{msg}</p>'
                st.session_state['data_L_loaded'] = False
            st.markdown(msg_text, unsafe_allow_html=True)


with st.expander("Right Data Set:", expanded = True):
    # Checking if left data has already been loaded
    if st.session_state['rlr'].dataR_loaded:
        st.write("Right Data Set Already Loaded")
        st.dataframe(st.session_state['rlr'].dataR.head())
        st.write(f"IDs: {st.session_state['rlr'].id_vars_r}")
        st.button("Load a different data set", key = "reload_r", on_click = remove_data_file, args=('r', ))
    else:
        # Input the second data file
        data_file_R = st.file_uploader("Upload file", key = "R_file",
                                        accept_multiple_files=False, type = ['csv', 'dta'])
        if data_file_R is None:
            st.write("")
        else:
            # Open the data file (after determining type)
            data_ext = os.path.splitext(data_file_R.name)[1]
            if      data_ext == ".csv":   dfR = pd.read_csv(data_file_R)
            elif    data_ext == ".dta":   dfR = pd.read_stata(data_file_R)
            else:                           
                raise NotImplementedError(f"Filetype of {data_path} must be either .csv or .dta")
            # Print the first few rows
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
                st.session_state['rlr'].load_dataset(dfR, dfR_id_vars, 'r')
            else:
                msg = "** Variables chosen do not uniquely identify rows. **"
                msg_text = f'<p style="color:Red;">{msg}</p>'
                st.session_state['data_R_loaded'] = False
            st.markdown(msg_text, unsafe_allow_html=True)

###########################################################################
#### App - Setting Up Variable Comparison Schema ##########################
###########################################################################

st.header("Variable Comparison Group Definitions")
# Checking if both data sets have been properly loaded
if (st.session_state['rlr'].dataL_loaded) and (st.session_state['rlr'].dataR_loaded):
    # Input description
    st.write("Use the below inputs to designate which variables from each "+
                "data set should be compared to one another. For example, comparing "+
                "variable 'name' in the left dataset with the variables 'first_name' "+
                "and 'last_name' in the right data set. Add or delete "+
                "comparison groups as necessary.")

    # Gather var schema from rlr instance if loaded
    if (st.session_state['rlr'].var_schema_loaded):
        var_comp_schema = st.session_state['rlr'].get_var_comp_schema()
    else:
        var_comp_schema = [{'name': "", 'lvars': [], 'rvars': []}]

    # Gathering variables from loaded dataset
    l_vars = st.session_state['rlr'].dataL.columns
    r_vars = st.session_state['rlr'].dataR.columns

    # Iterate through each var group and print out related inputs
    for i in range(len(var_comp_schema)):
        var_group = var_comp_schema[i].copy()
        with st.expander(f"Var. Group: {var_group['name']}", expanded = True):
            col_1, col_2 = st.columns([1,3])
            var_name = col_1.text_input("Var. Group Name:", value = var_group['name'], key = f"vargp_{i}_name")
            vars_l = col_2.multiselect("Pick Vars from Left Data Set:", l_vars,
                                        default = var_group['lvars'], key = f"vargp_{i}_lvars")
            vars_r = col_2.multiselect("Pick Vars from Right Data Set:", r_vars, 
                                        default = var_group['rvars'], key = f"vargp_{i}_rvars")
            del_button = col_1.button("Delete Group", key = f"vargp_{i}_del",
                                        on_click = del_var_group, args=(i, ))
            var_comp_schema[i] = {'name': var_name, 'lvars': vars_l, 'rvars': vars_r}
    st.session_state['rlr'].set_var_comp_schema(var_comp_schema)
    add_button = st.button("Add Group", on_click = add_var_group)

    # st.write(st.session_state['rlr'].get_var_comp_schema())
else:
    st.write("User must load two data sets with identifying variables before defining the comparison schema.")