import pandas as pd
import openai, datetime, sys
import datetime
from config import settings   
 
#Arguments passed through the command line as requested.
source_link = sys.argv[1]
template_link = sys.argv[2]
target_name = str(sys.argv[3])

def main(source_link, template_link, target_name):
    '''This function takes in the source dataset and the template dataset, and using the columns in the 
    template dataset most similar to columns in the source dataset, it transforms the values in the source
    dataset to match the preferred format in the template dataset. It also discards duplicate columns and 
    irrelevant columns.'''
    
    source = pd.read_csv(source_link, nrows=9)
    template = pd.read_csv(template_link, nrows=3)
    
    source_short = source.head(3).copy(deep=True) #Extracts a chunk of the source data to stay within the limit of the prompt
    
    #Converts the dataframes to json to feed to the GPT model
    source_dict = source_short.to_json(orient='records')  
    template_dict = template.to_json(orient='records')
    
    exec_scripts = {} #Creates the dictionary to store the new transformed data

    #Loops through each column of the source dataset to individually check for the most similar column in the template
    columns = list(source.columns)
    for column in columns:
        openai.api_key = settings.openai_key
        

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
        print(f"{column}: Done!")

        messages_1 = []

        #Creates new prompt to convert the values of the current column in th source dataframe
        prompt_4 = f" Please write a one-line python code to change the format of values in the {column} column in {source_dict} dataframe to the format of the values in {list(template[temp_column][:3])}, using source as the dataframe name." 

        #Adds the prompts to the chat memory
        messages_1.append({"role": "user", "content": prompt_4},)

        #GPT model is triggered and response is generated.
        chat_1 = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messages_1, 
            temperature=0.0
        )

        #Response is gotten and wrangles to extract the transformed data
        response_1 = chat_1.choices[0].message.content
        #print(response_1)
        
        exec_scripts[column] = [temp_column, response_1]
    
    for key in exec_scripts.keys():
        exec(exec_scripts[key][1])
        #source.rename(columns={key: exec_scripts[key][0]}, inplace=True)
        
    source.to_csv(target_name)
    with open('conversion_code.txt', 'w') as file:
        file.write(str(exec_scripts))
    print(source)
 
if __name__ == '__main__':
    main(source_link, template_link, target_name)