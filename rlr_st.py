import streamlit as st
import pandas as pd
from backend.rlr import rlr

# To run from command line (in root folder): "streamlit run rlr_st.py --server.port 8889"

st.set_page_config(page_title="RLR: Record Linkage Review",  #page_icon=im, 
                    layout="centered", initial_sidebar_state="auto", menu_items=None)

###########################################################################
#### Function Definitions #################################################
###########################################################################

def tformat(text, align='C', el='p'):
    align_dict = {'L':'left', 'C':'center','R':'right'}
    return(f"<{el} style='text-align: {align_dict[align]};'>{text}</{el}>")

def next_pair():
    st.session_state['curr_link_pair'] += 1

def prev_pair():
    st.session_state['curr_link_pair'] -= 1

###########################################################################
#### App - Sidebar ########################################################
###########################################################################

# Initializing rlr backend
if 'rlr' not in st.session_state:
    st.session_state['rlr'] = rlr()

with st.sidebar:
    st.title("Load Inputs")
    review_file = st.file_uploader("Upload file of linked pairs for review", 
                                    accept_multiple_files=False, type = ['csv', 'dta'])
    # Open files and load them here

    # Dummy data for now
    dfL = pd.DataFrame({'id_var':[2,4,6,8], 'age':[21,35,32,57],
                        'name':['Beth Johnson','John Smith','Ben Hasselback','Josie Carter']})
    dfR = pd.DataFrame({'id_var':['A','C','D','G'], 'age':[19,32,56,41],
                        'fname':['Erik','Benjamin','Bethany','Jonas'],
                        'lname':['Clapton', 'Hasselback', 'Jacobs', 'Brians']})
    dfL.set_index('id_var', inplace=True, drop=False)
    dfR.set_index('id_var', inplace=True, drop=False)

    link_pairs = [[2,'D'],[6,'C'],[4,'G']]
    if 'curr_link_pair' not in st.session_state:
        st.session_state['curr_link_pair'] = 0
    
    var_schema = [{'name':'id','L_vars':['id_var'],'R_vars':['id_var']},
                    {'name':'name','L_vars':['name'],'R_vars':['fname']},
                    {'name':'age','L_vars':['age'],'R_vars':['age']}]

###########################################################################
#### App - Main Page ######################################################
###########################################################################

st.title("RLR: Record Linkage Review")
if len(link_pairs) == 0:
    st.header("Upload 2 data files and a file of linked pairs to review in the sidebar to the left.")
else:
    # Data Side Titles
    tcol1, tcol2 = st.columns(2)
    tcol1.markdown(tformat("Left Data"),  unsafe_allow_html=True)
    tcol2.markdown(tformat("Right Data"),  unsafe_allow_html=True)

    # Actual data (iterate through var schemas)
    curr_link_ids = link_pairs[st.session_state['curr_link_pair']]
    recL = dfL.loc[curr_link_ids[0]]
    recR = dfR.loc[curr_link_ids[1]]
    for var_group in var_schema:
        Lcol, Mcol, Rcol = st.columns([4,1,4])
        L_var_name = var_group['L_vars'][0]
        R_var_name = var_group['R_vars'][0]
        Lcol.markdown(tformat(str(recL[L_var_name]),'R'),  unsafe_allow_html=True)
        Mcol.markdown(tformat(var_group['name']),  unsafe_allow_html=True)
        Rcol.markdown(tformat(str(recR[R_var_name]),'L'),  unsafe_allow_html=True)

    # Buttons for link determinations
    choices = ["No Label", "Don't match", "Maybe match", "Match"]
    prev_col, choice_col, next_col = st.columns([1,4,1])
    prev = prev_col.button("<< Previous", 
                            disabled=(st.session_state['curr_link_pair']==0), 
                            on_click=prev_pair)
    # link_determination = choice_col.selectbox("Choose Link Determination", choices)
    choice_col.write('<style>div.row-widget.stRadio > div{flex-direction:row;justify-content: center;} </style>', unsafe_allow_html=True)
    # choice_col.write('<style>div.st-bf{flex-direction:column;} </style>', unsafe_allow_html=True)
    choice_col.radio("Choose link determinations:", choices)
    prev = next_col.button("Next >>", 
                            disabled=(st.session_state['curr_link_pair']==len(link_pairs)-1),
                            on_click=next_pair)
    
    st.write("Current Variable Group Schema")
    # st.write(st.session_state['var_group_schema'])