import pandas as pd
import openai, json
from config import settings
import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
 
# Sidebar contents
with st.sidebar:
    st.title('GPT-Powered Web Automator')
    st.markdown('''
    ## About
    Processes the dataset in the source .csv file and compares each column in the source file to the columns 
    in the template .csv file and uses the most similar columns in the template file to transform the columns 
    in the source file. It alos discards duplicate columns and irrelevant columns.
    - [Streamlit](https://streamlit.io/)
    - [OpenAI](https://platform.openai.com/docs/models) LLM model
 
    ''')
    add_vertical_space(5)
    
 
def main():
    st.header("Web Automator (Transforms Source File to Desired Template) 💬")

    key_1 = "source"
    key_2 = "template"
 
    # upload a .csv file
    source = st.file_uploader("Upload your source .csv file", type=["csv"], key=key_1)
    template = st.file_uploader("Upload your template .csv file", type=["csv"], key=key_2)
 
    # st.write(pdf)
    if (source is not None) & (template is not None):

        # Use Pandas to read the uploaded CSV file
        source_2 = pd.read_csv(source)
        template = pd.read_csv(template)

        source = source_2.head(3).copy(deep=True) #Extracts a chunk of the source data to stay within the limit of the prompt
    
        #Converts the dataframes to json to feed to the GPT model
        source_dict = source.to_json(orient='records')  
        template_dict = template.to_json(orient='records')
        
        transformed_source = {} #Creates the dictionary to store the new transformed data

        #Loops through each column of the source dataset to individually check for the most similar column in the template
        for column in list(source.columns):
            openai.api_key = settings.openai_key #API Key for accessing the GPT model.

            messages = []   

            #Creates the prompt to check for the most similar column
            prompt_1 = f"Here is a Source DataFrame:\n{source_dict}."
            prompt_2 = f"Here is a Template DataFrame:\n{template_dict}."
            prompt_3 = f"For {column} column in source dataframe, which column in the template dataframe is most similar to it considering both column name and values in the column."

            #Adds the prompts to the chat memory
            messages.append({"role": "user", "content": prompt_1},)
            messages.append({"role": "user", "content": prompt_2},)
            messages.append({"role": "user", "content": prompt_3},)

            #GPT model is triggered and response is generated.
            chat = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=messages, 
                temperature=0.0
            ) 

            #Response is extracted
            response = chat.choices[0].message.content
            
            #The most similar column in the template dataframe is gotten
            for column_name in list(template.columns):
                if column_name in response:
                    temp_column = column_name
            

            transf_list = [] #List to store the transformed data using the format of the selected column from the template Dataframe
            for i in range(0, source_2.shape[0], 3):
                #Loops through the entire dataset in batches so as to process them regardless of size.
                messages_1 = []
                
                #Creates new prompt to convert the values of the current column in th source dataframe
                prompt_4 = f"Here is a list of values from the Source DataFrame:\n{list(source_2[column])[i:i+3]}"
                prompt_5 = f"Here is a sample of the format from the Template DataFrame:\n{list(template[temp_column][:3])}"
                prompt_6 = f"Output a new list (with no extra write up) containing the list of values from the Source DataFrame having the same format as the format of the samples from the Template DataFrame."

                #Adds the prompts to the chat memory
                messages_1.append({"role": "user", "content": prompt_4},)
                messages_1.append({"role": "user", "content": prompt_5},)
                messages_1.append({"role": "user", "content": prompt_6},)

                #GPT model is triggered and response is generated.
                chat_1 = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", messages=messages_1, 
                    temperature=0.0
                )

                #Response is gotten and wrangles to extract the transformed data
                response_1 = chat_1.choices[0].message.content
                response_1 = response_1.replace(']','')
                response_1 = response_1.replace('[','')
                response_1 = response_1.replace("'",'')
                response_1 = response_1.split(',')

                #Wrangled response is added to the list to store the transformed values for a given column
                transf_list = transf_list + response_1

            #Adds the final list for a given column to the dictionary containing all transofrmed columns (omitting duplicate columns of course)
            if (len(transf_list) == 9) & (temp_column not in list(transformed_source.keys())):
                    transformed_source[temp_column] = transf_list

        #Converts the dictionary to a dataframe and saves the result using the target dataset name provided to the function.
        final_source = pd.DataFrame(transformed_source)
        final_source.to_csv('target.csv')
        st.write("Transformed DataFrame:")
        st.write(final_source)
 
if __name__ == '__main__':
    main()