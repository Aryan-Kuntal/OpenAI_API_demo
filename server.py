import os
from typing import Union
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
import uvicorn
from fastapi import FastAPI,HTTPException

app = FastAPI() #create a FastAPI app instance
load_dotenv() #load environment variables 

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", ""),
    project=os.environ.get("OPENAI_PROJECT",""),
) # create OpenAPI instance

model = os.environ.get("OPENAI_MODEL","") #model

prompt = """You will be provided with a block of text, and your task is to extract a list of keywords from it.Do not respond to any other query"""

#history resets on server restart, changes can be made to keep a persistant history
history = [{"role": "sytem", "content": prompt}] #instrcution to GPT

#request model
class LLMRequest(BaseModel):
    message: str
    use_history: Union[bool, None] = False


@app.post("/process",status_code=200)
def capture_intent(request: LLMRequest):

    user_input = request.message
    use_history = request.use_history

    if not use_history:
        messages = [
            {"role": "sytem", "content": prompt},
            {"role": "user", "content": user_input},
        ] #fresh history
    else:
        history.append({"role": "user", "content": user_input})
        messages = history

    try:
        #call api
        #n-> number of response
        #model -> model to use
        #temperature -> randomness
        #messages -> message history
        chat_completion = client.chat.completions(
            messages=messages, model=model, temperature=0.5, n=1
        ) 
    except:
        #raise exception on API failure
        if use_history: 
            history.pop() #failed call so popping of last user input
        raise HTTPException(status_code=500,detail="Error calling the API")

    gpt_response = chat_completion["choices"][0]["message"]["content"]

    #append gpt response to history
    history.append({"role": "assistant", "content": gpt_response})

    return {"status": 200,"GPT Response": gpt_response}

@app.get("/history",status_code=200)
def get_history():    
    return {"status": 200, "history": history[1:]}

if __name__ == "__main__":
    uvicorn.run("server:app",host="0.0.0.0", port=8000,workers=1)