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

# Check if RLR is ready to review links
if (st.session_state['rlr'].ready_to_review):
    st.write("Review ready. TBD.")
else:
    st.write("Not all pieces necessary for review have been initialized:")
    # Check which parts are not yet initialized
    if not st.session_state['rlr'].dataL_loaded:
        st.write("  - Need to load a left data set (refer to data input page)")
    if not st.session_state['rlr'].dataR_loaded:
        st.write("  - Need to load a right data set (refer to data input page)")
    if not st.session_state['rlr'].var_schema_loaded:
        st.write("  - Need to define a variable comparison schema (refer to data input page)")
    if not st.session_state['rlr'].comps_loaded:
        st.write("  - Need to load a file of linkages for review (refer to sidebar)")
    if len(st.session_state['rlr'].label_choices) == 0:
        st.write("  - Need to define the label choices (refer to sidebar)")