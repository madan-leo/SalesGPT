# Test script to debug hard coded DUCKDB queries instead of asking LLM to generate the SQL.
import duckdb
import streamlit as st
import numpy as np
import altair as alt
import os
from dotenv import load_dotenv
load_dotenv()

prompt = st.chat_input("Say something")

if prompt:
    azcontainer = os.getenv('AZURE_CONTAINER')
    azpath = f'az://{azcontainer}/getdata/**'
    # query = f"""
    # SELECT Name, Id FROM read_parquet(f'{azpath}/opportunity.parquet') GROUP BY BillingCountry
    # """
    query1 = f"""
    SELECT o.Name, o.CreatedDate FROM read_parquet(f'{azpath}/opportunity.parquet') AS o WHERE DATE_TRUNC('quarter', CAST(o.CreatedDate AS DATE)) = DATE_TRUNC('quarter', CURRENT_DATE) ORDER BY o.CreatedDate DESC LIMIT 100
    """
    query2 = f"""
    SELECT Opportunity_Type__c, COUNT(*) FROM read_parquet(f'{azpath}/opportunity.parquet') GROUP BY Opportunity_Type__c
    ORDER BY COUNT(*) DESC
    """
    query3 = f"""
    SELECT u.FirstName, COUNT(o.Id) FROM read_parquet(f'{azpath}/user.parquet') AS u JOIN read_parquet(f'{azpath}/opportunity.parquet') AS o ON u.Id = o.CreatedById WHERE u.CountryCode__c = 'US' GROUP BY u.FirstName
"""
    st.write(query1)
    result = duckdb.query(query1).to_df()
    result.fillna('<blank>', inplace=True)
    # result[result.columns[0]] = result[result.columns[0]].str.replace('$', '', regex=False)

    st.write(result)
    # x = result[result.columns[0]]
    # y = result[result.columns[1]]
    # fig, ax = plt.subplots()
    # ax.plot(x, y)
    # col = [np.random.random(), np.random.random(), np.random.random()]
    # col= ['red', 'blue', 'orange', 'green', 'black', 'purple']
    # ax.bar(x,y,color=col, width=4)
    # ax.set_xlabel(result.columns[0])
    # ax.set_ylabel(result.columns[1])
    st.write("Here is the requested Chart:")
    # st.pyplot(fig)
    # st.bar_chart(data=result,x=result.columns[0], y=result.columns[1],color=col)
    if "count(" in query1.lower():
        st.write("I am here")
        colors = [f'#{np.random.randint(0, 0xFFFFFF):06x}' for _ in range(len(result))]
        result['Color'] = colors
        chart = alt.Chart(result).mark_bar().encode(x=result.columns[0], y=result.columns[1], color=alt.Color('Color:N', legend=None)).properties(title='Here is the Chart')
    # Display the chart in Streamlit
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("Chart Cannot be Displayed")
