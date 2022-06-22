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
st.write("RLR (pronounced like ***ruler***) is an app to help manually review and label potential "+
        " linkages between two datasets. This page describes the interface elements and gives "+
        "instructions for getting started. ")

st.header("Interface Descriptions")
st.write("At the top of the sidebar to the left you will find links to the important pages of this app."+
        " These pages and their contents are:")
text = " - **RLR Home**: Homepage (where you currently are) which includes instructions and background.\n"
text+= " - **Data Input**: This is where users load the data sets and define variable comparison groups. The sidebar"
text+= " of that page also lets you load and save 'review packet' files (see below for more information).\n"
text+= " - **Linkage Review**: This is where users are able to review, label, and annotate pairs of potential "
text+= "linkages. In the left sidebar of that page users can load linkage files (i.e. the list of potential "
text+= "pairs of records to review), see the current distribution of labels, and change the potential labels."
st.markdown(text)

st.header("Getting Started")
text = "In order to review and label potential linkages there are 3 elements that need to be loaded or defined:\n"
text+= " - **Data Files (L and R)**: A left file and a right file which each contain the individual "
text+= "record data.\n"
text+= " - **Variable Comparison Groups**: Groupings of variables that indicate which variables"
text+= " should be compared (i.e. compare column 'addy_st' in the left file with column 'state' in the right file).\n"
text+= " - **Linkage Review File**: Data file which lists the pairs of records for review and labeling."
st.markdown(text)
text = "There are two ways to load or define the above elements. It can be done either piecemeal "
text+= "(i.e. loading each individual aspect as for a new linkage project) or it can be done all at once with "
text+= "a 'review packet' (i.e. a single json file which loads all necessary parts for review). "
text+= "These two options are described in more detail in the subsequent section."
st.markdown(text)
text = "Overall, this leads to 3 simple steps to use RLR:\n"
text+= " 1. Load all above elements using the Data Input page (either piecemeal or with a review packet).\n"
text+= " 2. Navigate through, review, and label record pairs in the Linkage Review page.\n"
text+= " 3. Download the labeled data via the sidebar in the Linkage Review page (or take advantage of autosave)."
st.markdown(text)

st.subheader("Piecemeal")
st.markdown("""
        This method is best suited for starting a new project or when you are reviewing linkages for a 
        relatively simple situation. Essentially load each of the necessary elements as found in the 
        main part of the Data Input page. For each of the data files (i.e. the left and the right) the user
        must indicate which columns uniquely identify a record in that data file. These variable are
        also those that are used in the Review File for indicating which record is being referred to.

        ** UNDER CONSTRUCTION **
""")

st.subheader("Review Packet")
st.markdown("""
        This method is great for existing linkage review projects since it allows the user to load everything 
        simultaneously and immediately get to reviewing record pairs. This is done by defining a 'review packet'
        file, which is simply a json file with key value pairs indicating the value or location of all the
        necessary review elements. Once this file has been written and saved somewhere, simply upload it using
        the sidebar to the left on the Data Input page. If the file was specifified correctly, then all elements
        should be loaded instantly and the app will be ready for reviewing and labeling.

        This json file must have the following required keys:
         - **file_L**: Path to either a .csv or .dta file that contains the left side record data.
         - **file_L_ids**: List of column names (from the left file) that uniquely identify a row.
         - **file_R**: Path to either a .csv or .dta file that contains the right side record data.
         - **file_R_ids**: List of column names (from the right file) that uniquely identify a row.
         - **file_comps**: Path to either a .csv or .dta file containing pairs of record indices for review. 
         - **var_group_schema**: List of dictionaries where each element defines a variable group and has "name"
                "lvars" and "rvars" as keys which identify the group label, left columns, and right columns in the 
                group respectively.
                
        It may also have the following optional keys:
         - **label_choices**: List of label options. If not specified it will default to ["Match", "Not a Match"].

        An example of a simple 'review packet' is given below.
        ```
        {
                "file_L": "data/firm_data_file_1.csv",
                "file_L_ids": ["year", "ein"],
                "file_R": "data/firm_data_file_2.csv",
                "file_R_ids": ["ref_year", "ui_num"],
                "file_comps": "data/firm_linkset_1_raw.csv",
                "var_group_schema": [
                        {       "name": "Name",
                                "lvars": ["name"],
                                "rvars": ["company_name"] 
                        },
                        {       "name": "Address",
                                "lvars": ["addy_city", "addy_state"],
                                "rvars": ["city", "state"]
                        },
                        {       "name": "Industry",
                                "lvars": ["sic_code", "sic_text"],
                                "rvars": ["naics", "naics_name"]
                        }
                ],
                "label_choices": ["Match", "Not a Match","Maybe a Match"]
        }
        ```
""")