import streamlit as st
import pandas as pd
import numpy as np
import time
# MyClass gets redefined every time app.py reruns
class MyClass:
    def __init__(self, var1, var2):
        self.var1 = var1
        self.var2 = var2

if "my_instance" not in st.session_state:
  st.session_state.my_instance = MyClass("foo", "bar")

# Displays True on the first run then False on every rerun
st.write(isinstance(st.session_state.my_instance, MyClass))

st.button("Rerun")



df = pd.DataFrame(np.random.randn(15, 3), columns=(["A", "B", "C"]))
my_data_element = st.line_chart(df)

for tick in range(10):
    time.sleep(.5)
    add_df = pd.DataFrame(np.random.randn(1, 3), columns=(["A", "B", "C"]))
    my_data_element.add_rows(add_df)

st.button("Regenerate")