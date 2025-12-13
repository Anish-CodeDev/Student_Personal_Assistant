from langgraph.graph import StateGraph,START,END
from langchain_core.messages import BaseMessage,SystemMessage,HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict,Sequence,Annotated
from google import genai
from dotenv import load_dotenv
from gemini_functions import Gemini
import pandas as pd
import os
from mongodb import MongoDBHandler
from quiz import open_quiz_window
import subprocess
import sys
import json
load_dotenv()
client = genai.Client()
mongodb_handler = MongoDBHandler()
gemini = Gemini()
@tool
def generate_timetable(messages:str):
    """
    This tool is used when the user wants to generate a timetable.
    
    ARGS: SUBJECTS
    """
    print("Good")
    res = client.models.generate_content(
        model='gemini-2.5-flash-lite',
        contents=[
            f"""
            Generate a time table based on the user's input: {messages}, return only the timetable and nothing else
            
            The output must be a json with the first key as the day of the week and the second key as the time of the day and the value as the time.

            JUST RETURN THE TIMETABLE AND NOTHING ELSE
            """
        ]
    )   
    res = res.text.replace('`','').replace('json','')
    res = eval(res)
    print(res)

    df_timetable = pd.DataFrame.from_dict(res,orient='index')
    df_timetable.index.name = 'Day'
    df_timetable.to_csv('timetable.csv')
    os.startfile('timetable.csv')
@tool
def generate_todo_list(message:str):
    """
    This tool is used when the user wants to generate a todo list or wants to add new events to the todo list.
    The user must specify the date along with year
    ARGS: TASKS, DATE
    """
    date = gemini.extract_date(message)
    print(date)
    res = client.models.generate_content(
        model='gemini-2.5-flash-lite',
        contents=[
            f"""
            Generate a todo list based on the user's input: {message}, return only the todo list and nothing else
            
            The output must be a json with the first key as the date(along with year) with value has another dictionary with first key as events and second key as priority.

            JUST RETURN THE TODO LIST AND NOTHING ELSE
            """
        ]
    )   
    res = res.text.replace('`','').replace('json','')
    res = eval(res)
    print(res)
    mongodb_handler.insert(date,res)

@tool
def fetch_todo_list(date:str):
    """
    This tool is used when the user wants to fetch a todo list.   
    
    ARGS: DATE
    """
    date = gemini.extract_date(date)
    d = mongodb_handler.read(date)[0]
    arr = []
    try:
        for i in d.keys():
            if i == "_id":
                continue
            print("Date: ",i)
            print("Events: ",d[i]['events'])    
            print("Priority: ",d[i]['priority'])
            arr.append({"Date":i,"Events":d[i]['events'],"Priority":d[i]['priority']})
    except:
        return "Could'nt fetch todo list"
    return arr
@tool
def update_todo_list(message:str):
    """
    This tool is used to enhance the todo list based on the user's requirements.
    
    ARGS: TASKS, DATE
    """
    date = gemini.extract_date(message)
    try:
        todo = mongodb_handler.read(date)[0]
    except:
        return "No todo list found for the given date"
    
    try:

        res = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=[
                f"""
                Enhance the current todo list: {todo}, based on the user's input: {message}
                I want you to create a new todo list based on the user's input and the current todo list, not append to the previous one
                The output must be a json with the first key as the date(along with year) with value has another dictionary with first key as events and second key as priority.
                Just return the new todo list and nothing else
                """
            ]
        )   
        res = res.text.replace('`','').replace('json','')
        res = eval(res)
        mongodb_handler.delete_collection(date)
        mongodb_handler.insert(date,res)
        return "The todo list was successfully updated" 
    except:
        return "There was an error updating the todo list" 

@tool
def delete_todo_list(date:str):
    """
    This tool is used to delete the todo list based on the user's requirements.
    
    ARGS: DATE
    """
    date = gemini.extract_date(date)
    try:
        mongodb_handler.delete_collection(date)
        return "The todo list was successfully deleted" 
    except:
        return "There was an error while deleting the todo list" 

@tool
def generate_questions(message:str):
    """
    This tool is used to generate questions based on the user's requirements.
    
    ARGS: TOPIC, NUMBER OF QUESTIONS, DIFFICULTY
    """
    params = gemini.extract_quiz_params(message)
    topic = params[0]
    number_of_questions = params[1]
    difficulty = params[2]
    res = gemini.generate_questions(topic,number_of_questions,difficulty)
    score = 0
    json.dump(res['questions'],open('data/questions.json','w'))
    '''
    for i in res['questions']:
        print("Question: ",i['question'])
        print("Enter 1,2,3,4")
        print("Options: ",i['answers'])
        user_inp = input("User: ")
        if i['answers'][int(user_inp)-1] == i['correct_answer']:
            print("Correct")
            score += 1
        else:
            print("Incorrect")
            print("The correct answer was ",i['correct_answer'])
    '''
    process = subprocess.run([sys.executable,'quiz.py'])
    score,percentage = open('data/score.txt','r').read().split(' ')
    return "Thank for taking the quiz, your score is " + str(score) + " and your percentage is " + str(percentage) 
tools = [generate_timetable,generate_todo_list,fetch_todo_list,update_todo_list,delete_todo_list,generate_questions]
llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash').bind_tools(tools)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage],add_messages]

def agent(state: AgentState):
    instruction = SystemMessage(content="You are a helpful assistant designed to solve user's problems.")
    res = llm.invoke([instruction]+state['messages'])
    return {"messages":res} 

graph = StateGraph(AgentState)
tool_node = ToolNode(tools=tools)
graph.add_node("agent",agent)
graph.add_node("tool_node",tool_node)
graph.add_edge(START,"agent")

def decide(state: AgentState):
    if state['messages'][-1].tool_calls:
        return "continue"
    else:
        return "END"
graph.add_conditional_edges(    
    "agent",
    decide,
    {
        "continue": "tool_node",
        "END": END
    }
)
graph.add_edge("tool_node","agent")
app = graph.compile()

conversational_history = []
def call_agent(history):
    result = app.invoke({"messages":history[-3:]})
    history = result['messages']
    print("AI: ",dict(history[-1])['content'])
    try:
        if dict(history[-1])['content'][0]['text']:
            return dict(history[-1])['content'][0]['text']
    except:
        return dict(history[-1])['content']

if __name__ == "__main__":
    user_inp = input("User: ")
    while user_inp !='exit':
        try:

            conversational_history.append(HumanMessage(content=user_inp))
            result = app.invoke({"messages":conversational_history[-3:]})
            conversational_history = result['messages']
            print("AI: ",dict(conversational_history[-1])['content'])
            user_inp = input("User: ")
        except:
            print("AI: An Error Occured")