import streamlit as st
import pandas as pd

###########################################################################
#### Function Definitions #################################################
###########################################################################


###########################################################################
#### App - Var. Group Schema ##############################################
###########################################################################

# Heading and input description
st.title("Record Linkage Review")
st.write("Use the below inputs to designate which variables from each "+
            "data set should be compared to one another. Add or delete "+
            "comparison groups as necessary.")

# Initialize the group schema
if 'var_group_schema' not in st.session_state:
    st.session_state['var_group_schema'] = []

# Check if user has loaded datasets or not
if (st.session_state['rlr'].ready_to_review):
    st.write("Review ready. TBD.")
else:
    # Check which parts are not yet initialized
    st.write("Not all pieces necessary for review have been initialized.")