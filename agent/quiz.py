from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from agent.schemas import Quiz

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

# Setup Parser to ensure strict JSON output
parser = PydanticOutputParser(pydantic_object=Quiz)


def generate_quiz(topic: str, context: str = ""):
    """
    Generates a structured quiz based on the user's topic and learning plan context.
    """

    prompt_text = """
    You are an expert tutor creating a quiz to test a student's knowledge.

    TOPIC: {topic}
    LEARNING CONTEXT: {context}

    INSTRUCTIONS:
    1. Create a quiz with 5-10 multiple choice questions.
    2. The questions should test understanding of concepts, not just syntax.
    3. Provide 4 options for each question.
    4. Provide a clear explanation for the correct answer.
    5. The output MUST be valid JSON matching the specified format.

    {format_instructions}
    """

    prompt = ChatPromptTemplate.from_template(prompt_text)

    # Chain: Prompt -> LLM -> JSON Parser
    chain = prompt | llm | parser

    try:
        quiz_data = chain.invoke({
            "topic": topic,
            "context": context,
            "format_instructions": parser.get_format_instructions()
        })
        return quiz_data
    except Exception as e:
        print(f"Error generating quiz: {e}")
        return None