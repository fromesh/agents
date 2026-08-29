"""
example-agent: the smallest possible "agent" loop, written by hand.

An agent is nothing more than this loop:

    1. Send the conversation + tool definitions to the model.
    2. If the model's response contains a tool_use block, run that tool locally.
    3. Feed the tool's result back into the conversation as a tool_result.
    4. Repeat until the model responds with plain text (no more tool calls).

Everything a framework gives you (subagents, memory, permissions, retries) is built
on top of this loop. Read this file top to bottom before reaching for a framework —
once this is boring and obvious, the frameworks stop being magic.
"""

import json
import os

from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-sonnet-4-6"


# --- Step 1: define a tool ---------------------------------------------------
# A tool is just a JSON schema describing a function, plus the actual Python
# function that runs when the model asks for it. The model never executes code;
# it only ever asks you to run something and hands you the arguments as JSON.

def get_word_length(word: str) -> int:
    return len(word)


TOOLS = [
    {
        "name": "get_word_length",
        "description": "Return the number of characters in a word.",
        "input_schema": {
            "type": "object",
            "properties": {"word": {"type": "string"}},
            "required": ["word"],
        },
    }
]

TOOL_IMPLEMENTATIONS = {"get_word_length": get_word_length}


# --- Step 2: the loop ---------------------------------------------------------

def run_agent(user_message: str, max_turns: int = 10) -> str:
    messages = [{"role": "user", "content": user_message}]

    for _ in range(max_turns):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )
        print(response.content) 
        # Did the model ask to use a tool, or is it done talking?
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

        if not tool_use_blocks:
            # No tool calls -> the model is giving its final answer.
            text_blocks = [b.text for b in response.content if b.type == "text"]
            return "\n".join(text_blocks)

        # The model's turn (including its tool_use requests) goes back into history.
        messages.append({"role": "assistant", "content": response.content})

        # Run every requested tool locally and collect results.
        tool_results = []
        for block in tool_use_blocks:
            fn = TOOL_IMPLEMENTATIONS[block.name]
            result = fn(**block.input)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                }
            )

        # Feed the results back in as a user turn, and loop again.
        messages.append({"role": "user", "content": tool_results})

    return "Hit max_turns without a final answer."


if __name__ == "__main__":
    answer = run_agent("How many characters are in the word 'anthropic'?")
    print(answer)
