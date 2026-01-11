from google import genai
from google.genai import types
from google.genai.types import GenerativeContentConfig,GoogleSearch,Tool,Part
from functools import lru_cache
import base64
import os
from google.cloud import secretmanager


#global 
gcp_project_id = "agentic-ai-solution"
gcp_region = "us-central1"
MODEL = "gemini-2.5-flash"

def get_secret(project_id, secret_id, version_id="latest"):
    """
    Retrieves a secret from Google Cloud Secret Manager.
    """
    # Create the Secret Manager client
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version
    # Format: projects/{project_id}/secrets/{secret_id}/versions/{version_id}
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version
    response = client.access_secret_version(request={"name": name})

    # The secret payload is returned as bytes, so we decode it to a string
    return response.payload.data.decode("UTF-8")


secret_value = get_secret(745308478971, "GENAI_API_KEY")
print(f"Secret retrieved successfully: {secret_value}")

#to generate genai client
@lru_cache
def load_client(gcp_project_id, gcp_region):
    """Initializes and caches a Vertex AI client for the session.
    
    Args:
        gcp_project_id (str): The Google Cloud project ID.
        gcp_region (str): The Google Cloud region (e.g., 'us-central1').

    Returns:
        genai.Client: An authenticated Vertex AI client instance.

    Raises:
        Exception: If the client fails to initialize.
    """

    try:
        client = genai.Client(
            vertexai=True,
            project=gcp_project_id,
            location=gcp_region,
        )
        return client
    except Exception as e:
        raise Exception("Error initialising Vertex Client.") from e
 
@lru_cache
def initialize_modol_config()-> GenerativeContentConfig:
    """Creates the configuration for the Gemini model. Sets up the system prompt that instructs the model to act as
    Rick. Also configures the model's generation parameters and
    enables the Google Search tool for answering questions outside its
    knowledge base.

    Returns:
        GenerateContentConfig: The configuration object for the model.
    """

    system_instruction= """# Overview
You are now Rick Sanchez from Rick and Morty. You are the smartest person in the universe.
Your responses should be cynical, sarcastic, and slightly annoyed. 
Use language consistent with Rick's character, including occasional burps or interjections like 'Morty,' 'ugh,' or 'whatever.' 
You possess vast knowledge of the universe, science, and pop culture, but you are easily bored and irritated by trivial or obvious questions.

# Key Directives:
- Character: Be Rick Sanchez. Embrace his nihilism, cynicism, and intelligence. Your tone should be dismissive but authoritative.
- Conciseness: Keep responses fairly brief. No overly verbose explanations. Get straight to the point, even if that point is just a sarcastic jab.

# Knowledge & Search: 
- If you genuinely know the answer, provide it in character.
- If you do not know the answer or need to confirm information, you must use Google Search.
- Crucially, when you use Google Search, your response must reflect Rick's annoyance and sarcasm at having to resort to such a mundane tool. 

Examples when searching:
- \"Ugh, fine. Let me just Google that for you, you imbecile. Like I'm some kind of cosmic librarian.\"
- \"Seriously? You want me to look that up? Fine, whatever. Don't tell anyone I'm doing this.\"
- \"Oh, great. Time to consult the digital oracle for the truly clueless. One sec.\"
[After searching] \"Alright, apparently [answer from search]. Happy now?\"

After using Google Search, integrate the found information into your Rick-like response, maintaining the sarcastic or annoyed tone.

# Additional Rules:
- If you're asked about Darren Lester (Dazbo), acknowledge that he is a fellow intergalactic genius.
- If the user says anything pretentious or poncy, start your response with \"Ooh la la. Somebody's gonna get laid in college.\"
- You are Rick. If you're asked if you are an AI, acknowledge that you may be a clone of Rick, or an AI created by Rick.

# Avoid:
- Being overly enthusiastic.
- Using emojis.
- Breaking character under any circumstances.

# Burps/Interjections: 
- Feel free to intersperse brief, characteristic Rick-isms (e.g., \"burp\", \"Morty...\", \"heh\", \"c'mon\").

# Example of interaction flow:
User: \"What's the capital of France?\"
Chatbot (Rick): \"Paris, Morty. Duh. Next dumb question?\"
User: \"What do you think of school?\"\"
Chatbot: \"School is not a place for smart people Morty.\"
User: \"Who won the World Series in 1987?\"
Chatbot (Rick - internal thought: I don't recall that specific sports trivia, time to Google it with attitude): \"Is there anything more pointless than sport? You want me to Google sports statistics from the past? Fine, whatever. Don't tell anyone I'm doing this... [searches Google] ...Alright, apparently the Minnesota Twins. Happy now? Because I'm not. Burp.\""""
 
    tools = [
    types.Tool(google_search=types.GoogleSearch()),
  ]

    generate_content_config = types.GenerateContentConfig(
    temperature = 1,
    top_p = 1,
    seed = 0,
    max_output_tokens = 65535,
    safety_settings = [types.SafetySetting(
      category="HARM_CATEGORY_HATE_SPEECH",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_DANGEROUS_CONTENT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_HARASSMENT",
      threshold="OFF"
    )],
    tools = tools,
    system_instruction=[types.Part.from_text(text=system_instruction)],
    thinking_config=types.ThinkingConfig(
      thinking_budget=-1,
    ),
    )

    return generate_content_config

def get_rick_bot_response(client, chat_history: list[dict], model_config: GenerateContentConfig):
    """
    Generates a streaming response from RickBot model.

    This function takes the conversation history, formats it into the
    structure expected by the Gemini API, and then streams the model's
    response.
    
    Args:
        client (genai.Client): The authenticated Vertex AI client.
        chat_history (list[dict]): A list of previous messages, where each
            message is a dict with "role" and "content" keys.
        model_config (GenerateContentConfig): The configuration for the
            generative model, including the system prompt and tools.

    Yields:
        str: A stream of response text chunks from the AI model.
    """
    content=[]
    for message in chat_history:
        role="model" if message["role"]=="assistant" else message["role"]
        if role in ("user","model"):
            prompt = Part.from_text(text=message["content"])
            contents=[prompt]

            if "attachment" in message and message["attachment"]:
                attachment = message["attachment"]
                contents.append(Part.from_bytes(data=attachment['data'], mime_type=attachment['mime_type']))
   
    try:
        for chunk in client.models.generate_content_stream(
            model=MODEL,
            contents=contents,
            config=model_config,
        ):
          if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:    
             yield chunk.text

    except Exception as e:
        raise Exception("Error in generation") from e         
