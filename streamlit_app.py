# -*- coding: utf-8 -*-
"""
Created on Fri Nov 20 11:06:45 2025
@author: foceguera
"""

import streamlit as st

st.set_page_config(
    
        page_title="EolicStats",
        page_icon="🌦️",
        layout="wide")
        
st.title("📊 Cargador de datos")

st.text_input("Your name", key="name")

st.session_state.name

x = st.slider('x')  
st.write(x, 'squared is', x * x)
    
