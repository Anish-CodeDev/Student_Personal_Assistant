from google import genai
from dotenv import load_dotenv
load_dotenv()
client = genai.Client()
'''
1. TODO LIST
2. TIMETABLE
3. LEARNING COACH(Quiz,Flashcard)
4. Internship Tracker(Linkedin)
5. SKILL GAP(Provided by the user)
'''


class Gemini:
    def __init__(self):
        self.client = genai.Client()
    def generate_content(self, contents,model='gemini-2.5-flash-lite'):
        res = self.client.models.generate_content(
            model=model,
            contents=contents
        )
        return res.text
    
    def extract_messages(self,question,topic):
        res = self.client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=[
                f"""
                Your job is to extract the messages from the user's question, do that precisely to obtain the {topic}
                User's question: {question}
                """
            ]
        )
        return res.text
    
    def convert_to_dictionary(self,inp):
        res = self.client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=[
                f"""
                Your job is to convert the input to a dictionary, do that precisely
                Input: {inp}
                """
            ]
        )
        return res.text
    
    def extract_date(self,inp):
        res = self.client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=[
                f"""
                Your job is to extract the date from the user's input, do that precisely
                Input: {inp}
                THE FORMAT OF THE DATE IS DD-MM-YY
                EXAMPLE: 27th Nov 2025 becomes 27-11-25
                """
            ]
        )   
        return (res.text.replace('`',''))
    
    
    
    def extract_quiz_params(self,inp):
        res = self.client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=[
                f"""
                Your job is to extract the topic, number of questions and difficulty from the user's input, do that precisely
                Input: {inp}
                The output must be a tuple
                """
            ]
        )   
        return eval(res.text)
    def generate_questions(self,topic,number_of_questions,difficulty):
        res = self.client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=[
                f"""
                Your job is to generate {number_of_questions} questions for the given topic, do that precisely
                Topic: {topic}
                Difficulty: {difficulty}

                The output must be a json with the first key as "questions" and the value as a list of questions
                The second key "question" must be the question, third key "answers" is the list of answer and the fourth key "correct_answer" is the correct answer
                
                
                """
            ]
        )   
        return eval(res.text.replace('`','').replace("json",""))
    
    def generate_questions_from_resume(self):
        res = self.client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=[
                f"""
                Your job is to generate questions for a person applying for a job
                The questions must be based on these args:
                - role/position
                - location
                - salary range
                - job type (full-time, contract, etc.)
                - experience level
                - specific skills

                Return the questions in the form of a list(no-python code), when I mean questions, the questions which would be required for determining the type of job the candidate would apply
                The output must be a pythonic list(no-python code) [No extra content]
                """
            ]
        )   
        return eval(res.text.replace('`',''))
    
    def extract_option_number(self,inp,answers):
        res = self.client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=[
                f"""
                Your job is to extract the option number from the user's input, do that precisely by considering the possible answers
                Input: {inp}
                Answers: {answers}
                If no options matches return the most probable option number
                If a numerical value is passed don't do anything

                The output must be a number(1-4). Please do it precisely
                """
            ]
        )   
        return (res.text.replace('`',''))
if __name__ == "__main__":
    gemini = Gemini()
    #res = gemini.generate_questions_from_resume()
    #print(gemini.extract_date("Todo list for the date of 1st Dec 2025"))
    print(gemini.extract_option_number("2. ",["Paris","London","Berlin","Madrid"]))
