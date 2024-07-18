from CallLLM import callopenai
import streamlit as st
import duckdb
import numpy as np
import altair as alt
import datetime
import os
from dotenv import load_dotenv
load_dotenv()

# Store chat conversations in a session variable and loop through list to display at the end
if 'chat_results' not in st.session_state:
    st.session_state.chat_results = []
if 'chat_logs' not in st.session_state:
    st.session_state.chat_logs = []

# For browser bar - title, logo etc. & to keep side bar expanded
st.set_page_config(
    page_title="salesGPT",
    page_icon="icon.jpg",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Set sidebar logo and color
st.sidebar.image("logo.jpg", width=250)
st.markdown("""
<style>
    [data-testid=stSidebar] {
        background-color: #1A2129;
    }
</style>
""", unsafe_allow_html=True)
st.sidebar.markdown("<h2 style='text-align: left; color: white;'>Chat History</h2>", unsafe_allow_html=True)

# Display Clear Chat button on the sidebar. Clear chat conversations when clicked.
with st.sidebar:
    if st.sidebar.button("Clear Chat"):
        st.session_state.chat_results = []
        st.session_state.chat_logs = []

# List of conversation starters
conversation_starters = [
    "Show Top 5 Opportunities",
    "How many accounts are in the US",
    "Show a chart of opportunities created by quarter this year",
    "Show top 5 quotes by revenue created in the last quarter",
    "Show chart of total Quotes by type",
    "How many accounts have Opportunities",
    "Show top 5 opportunities by Net total with order intake in the future",
]

# Randomly select four questions
# Create buttons for each selected question
# selected_questions = random.sample(conversation_starters, 4)
# with st.sidebar.f:
#     for question in selected_questions:
#         if st.sidebar.button(question):
#             st.write(question)

# Function to add new chat conversation entry.
# role could be user/assistant, type could be text/table/chart, content is text, dataframe or a chart
# entry is appended to the session variable, after each Question and answer


def add_chat_entry(role, type, content):
    # Create a chat entry
    record = {
        'role': role,
        'type': type,
        'content': content,
    }
    st.session_state.chat_results.append(record)

# Actual Chat block


tab1, tab2 = st.tabs(["Chat", "Logs"])
with tab1:
    try:
        container = st.container(height=450, border=True)
        prompt = st.chat_input("Say something")
        container.chat_message("assistant").write("How may I help you!")

        if prompt:
            st.session_state.chat_logs.append(f"<u><b> {prompt} </b></u>")
            st.session_state.chat_logs.append(str(datetime.datetime.now()) + "- <b> Start </b>")
            add_chat_entry("user", "text", prompt)
            # First retrieve the tables needed for SQL, so related schemas can be pulled and passed in the second call
            tableRetrieverPrompt = """You are a helpful database assistant. Output the tables needed for a SQL query, from this list : "Account", "Opportunity", "Quote", "QuoteLineItem", "User", "Lead"
                                    If the question does not seem related to the database, just return 'nonDbPrompt' as the answer. 
                                    Output the tables in an array.
                                    """
            # Call OpenAI
            tableRetrieverOutput = callopenai(prompt, tableRetrieverPrompt)
            st.session_state.chat_logs.append(str(datetime.datetime.now()) + "-  <u>Retrieved Tables:</u> " + tableRetrieverOutput)

            # Parse the output string into an array
            tableRetrieverOutput = tableRetrieverOutput.replace(" ", "").replace('"', '').replace('[', '').replace(']', '').replace("'", "").split(',')

            # If the question is not related to database, 'nonDbPrompt' is outputted. Process the Tables to query CRM data only if 'nonDbPrompt' is not returned
            if tableRetrieverOutput[0] != "nonDbPrompt":
                # Set context with schema of tables returned from previous OpenAI Call
                # Schema is detailed enough to have column names, synonyms, data types, picklist values, foreign key details, etc.
                context = ""
                for i in tableRetrieverOutput:
                    if i == "Account":
                        context = '\n'.join([context, f"account.parquet (Id PRIMARY KEY, Name, Customer_Hierarchy_L4__c 'Synonym: Categorization', Account_Classification__c, Phone, Website, Status__c PICKLIST Open for Business/Under Construction/No Longer in Business, BillingStreet USE %LIKE%, BillingCity, BillingState 'California, New Jersey, etc', BillingPostalCode, BillingCountry 'United States, Canada, etc.', OwnerId FOREIGN KEY REFERENCES user.parquet, ComEx_Template__c, Language__c 'English abbreviated as EN, ES as Spanish, etc.', ComEx_ID__c 'Synonym: Account Number', CurrencyIsoCode, Type, CreatedById FOREIGN KEY REFERENCES user.parquet, CreatedDate DATE,  LastModifiedById FOREIGN KEY REFERENCES user.parquet, LastModifiedDate DATE)"])
                    elif i == "Opportunity":
                        context = '\n'.join([context, f"opportunity.parquet (Id PRIMARY KEY, Opportunity_Number__c, Name, AccountId FOREIGN KEY REFERENCES account.parquet, StageName PICKLIST Qualifying/Analyzing/Negotiating/Quoting/Cancelled/Won/Lost, Probability, Opportunity_Type__c use %LIKE%, Modality__c, Source__c use %LIKE%, Description, OwnerId FOREIGN KEY REFERENCES user.parquet, Warranty_Contract_End_Date__c DATE,  CloseDate DATE 'Synonym: Order Intake Date', Expected_Delivery_Date__c DATE, Install_Completion_Date__c DATE, Forecast_Category__c PICKLIST Pipeline/Commit/Omitted/Closed/Best case, QuoteAmount__c, Sales_Channel__c, CurrencyIsoCode, Payer__c use %LIKE%, Reason_Won_Lost__c, Won_Lost_description__c, Winning_Competitor__c, Competitor_Price_c__c , Renewal__c, Demo__c, Tender__c, Project__c, Integrated_Margin_Calculation__c, Integrated_Margin_ApprovalBy__c, CampaignName__c, Quote_Number__c, Gforce_Division__c, CreatedById FOREIGN KEY REFERENCES user.parquet, CreatedDate DATE,  LastModifiedById FOREIGN KEY REFERENCES user.parquet, LastModifiedDate DATE)"])
                    elif i == "Quote":
                        context = '\n'.join([context, f"encquote.parquet (Id PRIMARY KEY, Quote_NumberAndRev__c, Name, Account__c FOREIGN KEY REFERENCES account.parquet, Opportunity__c FOREIGN KEY REFERENCES opportunity, Type__c PICKLIST Standard Quote/Budgetary Quote/Tender Quote/'Consumables/Disposables'/AfterMarket Sales, IsActive__c true/false, Status__c PICKLIST New/Successfully Priced/ Not Successfully Priced/Submitted for Approval/Approved/Rejected/Lost/Submitted to SAP, Contact__c, Print_Language__c, CurrencyIsoCode, Description__c, NetTotal__c, OwnerId FOREIGN KEY REFERENCES user.parquet, ExpirationDate__c DATE 'Synonym: Valid Until', PriceDate__c, Division__c, Source__c, SalesOrganizationName__c, GFS__c true/false, CreatedById FOREIGN KEY REFERENCES user.parquet, CreatedDate DATE,  LastModifiedById FOREIGN KEY REFERENCES user.parquet, LastModifiedDate DATE)"])
                    elif i == "QuoteLineItem":
                        context = '\n'.join([context, f"enclineitem.parquet (Id PRIMARY KEY, ProductNumber__c, Quote__c FOREIGN KEY REFERENCES quote.parquet, Name, NewAmount__c 'Synonym: Quantity', positionType__c, Optional__c true/false, Hybrid__c true/false, listPrice__c, contractPrice__c, startPrice__c, ManualPrice__c, contractDiscount__c, NewRelativePositionDiscount__c 'Synonym: Addition Discount%', net_positionAdditionalDiscountAmount__c 'Synonym: Additional Discount Amount', Total_Disc_calculated__c 'Synonym: Total Discount', SAP_680_SUM__c 'Synonym: Net Total, Net Amount', SAP_760_SUM__c 'Synonym: Gross Total, Gross Amount', Contract_Number__c, Gpo_ERP_Account__c 'Synonym: GPO Contract', CreatedById FOREIGN KEY REFERENCES user.parquet, CreatedDate DATE,  LastModifiedById FOREIGN KEY REFERENCES user.parquet, LastModifiedDate DATE)"])
                    elif i == "User":
                        context = '\n'.join([context, f"user.parquet (Id PRIMARY KEY, FullName__c USE '%LIKE%', Username, CurrencyIsoCode, u_number__c, ComEx_Team_Role__c, TM_Category__c, Title, SAP_Customer_Number_Short__c, UserRoleId, FederationIdentifier, ProfileId, Profile_Name__c, RegionalSalesManager__c, Product_Division__c, Phone, Portal_User__c, ParentRolesIds__c, MobilePhone, ManagerId, Manager_Name__c, Last_login_browserSF1__c, IsFrozen__c, IsPortalEnabled, Gforce_Division__c, Company__c,Division, Department, CountryCode__c, AreaDirector__c, IsActive true/false)"])

                st.session_state.chat_logs.append(str(datetime.datetime.now()) + "-  <u>Schemas:</u> " + context)
                # System Prompt to retrieve SQL query based on the table schemas mentioned in the context
                # Output in the format [Aggregate/Table/Chart: "SQL Query"]
                sqlRetrieverPrompt = f"""You are a helpful, cheerful database assistant.
                                   Use the following parquet filenames and columns inside them, to generate a SQL query to search the parquet files in duckdb SQL query syntax (Synonyms are mentioned in quotes)
                                   {context}
                                   Output SQL should be in the following format:
                                   "SELECT "COLUMN NAME" FROM read_parquet("FILENAME") JOIN "Table" ON "Relationship" WHERE "CONDITION" LIMIT n", replace "COLUMN NAMES" with relevant columns, "FILENAME" with the parquet filename, and "CONDITION" with filter conditions
                                   Only use Aliases after SELECT command. Do not use full parquet file names.
                                   Always Use CAST("Date Column" as DATE) format for Date columns.
                                   Use "DATE_TRUNC" for date conditions.
                                   Output at least first 2 columns of each table
                                   Only output in the format [Aggregate or Table or Chart:"YOUR QUERY"], where first element specifies if the output should be presented as Aggregate or Table or Chart. 
                                   Replace "YOUR Query" with output SQL query in Duckdb syntax.
                                   Output 'Chart' only if words Chart or Dashboard are mentioned in the prompt.
                                   Output only 2 columns in SQL for Chart.
                                   If you cannot figure out an answer, just return "I cannot answer that".                     
                                    """
                # Call OpenAI
                sqlRetrieverOutput = callopenai(prompt, sqlRetrieverPrompt)
                st.session_state.chat_logs.append(str(datetime.datetime.now()) + "-  <u>LLM Output:</u> " + sqlRetrieverOutput)

                # Parse the output from string to an array
                sqlRetrieverOutput = sqlRetrieverOutput.replace('[', '').replace(']', '').replace('"', '').split(':')

                # Retrieve the SQL into a variable
                initialquery = f"""{sqlRetrieverOutput[1]}"""

                # Reformat the SQL by removing the double quotes around, and replacing the parquet file names with full azure blob storage container path
                azcontainer = os.getenv('AZURE_CONTAINER')
                azpath = f'az://{azcontainer}/getdata/**'
                query = initialquery.replace('"', '').replace('user.parquet', f'{azpath}/user*.parquet').replace('account.parquet', f'{azpath}/account*.parquet').replace('encquote.parquet', f'{azpath}/encquote*.parquet').replace('opportunity.parquet', f'{azpath}/opportunity*.parquet').replace('enclineitem.parquet', f'{azpath}/enclineitem*.parquet')
                st.session_state.chat_logs.append(str(datetime.datetime.now()) + "-  <u>Executed SQL Query:</u> " + query)

                # Run the SQL on parquet files using duck db
                sqlResult = duckdb.query(query).to_df()
                st.session_state.chat_logs.append(str(datetime.datetime.now()) + "<b>- Done </b>")
                st.session_state.chat_logs.append(f"----------------------Query Executed-------------------------")

                # Replace null values with <blank> string
                sqlResult.fillna('<blank>', inplace=True)

                # Replace any special characters. Opportunity Type had a '$$' which was causing an error
                sqlResult[sqlResult.columns[0]] = sqlResult[sqlResult.columns[0]].str.replace('$', '', regex=False)

                # Write the output in the chat results session variable, in the specified format Table/Aggregate/Chart
                if sqlRetrieverOutput[0] == 'Table':
                    add_chat_entry("assistant", "table", sqlResult)
                elif sqlRetrieverOutput[0] == 'Chart':
                    # Only display chart if there is an aggregate function count() in the SQL
                    if ("count(" in query.lower()) or ("sum(" in query.lower()) or ("avg(" in query.lower()):
                        # Retrieve first column of results dataframe into x, second column into y
                        x = sqlResult[sqlResult.columns[0]]
                        y = sqlResult[sqlResult.columns[1]]

                        # Generate random colors of each bar in the chart
                        colors = [f'#{np.random.randint(0, 0xFFFFFF):06x}' for _ in range(len(sqlResult))]

                        # Add a Color column to the df, and build chart
                        sqlResult['Color'] = colors
                        chart = alt.Chart(sqlResult).mark_bar().encode(x=sqlResult.columns[0], y=sqlResult.columns[1], color=alt.Color('Color:N', legend=None)).properties(title='Here is the Chart:')

                        sqlResultfiltered = sqlResult.drop('Color', axis=1)  # df without the color column
                        add_chat_entry("assistant", "table", sqlResultfiltered)
                        add_chat_entry("assistant", "chart", chart)
                    else:
                        add_chat_entry("assistant", "text", "No Aggregated data. Chart Cannot be Displayed")
                elif sqlRetrieverOutput[0] == 'Aggregate':
                    # Call OpenAI to form an answer sentence based on the aggegrated result
                    aggregatePrompt = f"""Given the answer of {sqlResult}, Write a sentence to output the answer to the user based on the original question."""
                    aggregateOutput = callopenai(prompt, aggregatePrompt)
                    add_chat_entry("assistant", "text", aggregateOutput)
                    st.session_state.chat_logs.append(str(datetime.datetime.now()) + "-  Aggregation LLM response: " + aggregateOutput)
                else:
                    # If the output is not of type Table/Aggregate/Chart
                    add_chat_entry("assistant", "text", "The output format was not defined by the LLM")
            else:
                # If the question is not related to database, 'nonDbPrompt' is outputted. Answer the question directly via internet search
                nondbPrompt = """Answer the question with your knowledge from Internet
                                    Summarize answer to a maximum of 500 characters"""
                nondbOutput = callopenai(prompt, nondbPrompt)
                add_chat_entry("assistant", "text", nondbOutput)
                st.session_state.chat_logs.append(str(datetime.datetime.now()) + "-  Non Database prompt output: " + nondbOutput)

        # Loop through the chat results session variable to display the output in the correct format based on type text/aggregate/chart
        # This keeps track of all the history of conversations, loops through and display after each interaction
        for i, entry in enumerate(st.session_state.chat_results):
            if entry['role'] == "user":
                with container.chat_message("user"):
                    if entry['type'] == "text":
                        st.write(entry['content'])
                        # Enter the prompt history on the sidebar
                        st.sidebar.markdown(f"<h5 style='text-align: left; color: white;'>{entry['content']}</h5>", unsafe_allow_html=True)
            elif entry['role'] == "assistant":
                with container.chat_message("assistant"):
                    if entry['type'] == "text":
                        st.write(entry['content'])
                    elif entry['type'] == "table":
                        st.dataframe(entry['content'])
                    elif entry['type'] == "chart":
                        st.altair_chart(entry['content'])
    except Exception as e:
        with container.chat_message("assistant"):
            st.write(e)
            st.session_state.chat_logs.append(str(datetime.datetime.now()) + "- Error: " + str(e))

with tab2:
    if st.session_state.chat_logs:
        for j, entry1 in enumerate(st.session_state.chat_logs):
            st.markdown(f"{entry1}", unsafe_allow_html=True)
    else:
        st.write("No Log Found")
