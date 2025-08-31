import streamlit as st

st.title("Tab Test")

tab1, tab2, tab3 = st.tabs(["Tab 1", "Tab 2", "API Testing"]) 

with tab1:
    st.write("First tab")

with tab2:
    st.write("Second tab")
    
with tab3:
    st.write("🎉 Third tab is working!")