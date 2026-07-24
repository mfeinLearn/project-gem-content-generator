import json
from typing import Any, Dict, List, Optional

import anthropic
from tools.definitions import TOOLS, make_error
from prompts.system_single import SYSTEM_PROMPT


client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY from environment


def run_agentic_loop(
    user_message: str,
    max_iterations: int = 8,
    model: str = "claude-sonnet-5",
) -> Dict[str, Any]:
    """
    Classic agentic loop that continues while stop_reason == "tool_use".
    This is the exact pattern tested in Domain 1 of the CCA-F exam.
    """

    messages: List[Dict[str, Any]] = [
        {"role": "user", "content": user_message}
    ]

    for iteration in range(max_iterations):
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Record the assistant turn
        messages.append({
            "role": "assistant",
            "content": response.content
        })

        # ----- Key exam concept: check stop_reason -----
        if response.stop_reason == "end_turn":
            # Model is done
            final_text = ""
            for block in response.content:
                if block.type == "text":
                    final_text += block.text
            return {
                "status": "completed",
                "iterations": iteration + 1,
                "final_text": final_text,
                "messages": messages,
            }

        if response.stop_reason == "tool_use":
            # Execute every tool call the model requested
            tool_results = []

            for block in response.content:
                if block.type != "tool_use":
                    continue

                tool_name = block.name
                tool_input = block.input
                tool_use_id = block.id

                print(f"  → Tool call: {tool_name}")

                # --------------------------------------------------
                # Tool execution (we will flesh this out in next steps)
                # For now we return a structured placeholder
                # --------------------------------------------------
                if tool_name == "generate_exercise":
                    result = {
                        "status": "generated_placeholder",
                        "note": "Real generation logic will be added next",
                        "input_received": tool_input,
                    }
                elif tool_name == "validate_exercise":
                    result = {
                        "status": "validated_placeholder",
                        "note": "Real validation logic will be added next",
                        "input_received": tool_input,
                    }
                else:
                    result = make_error(
                        message=f"Unknown tool: {tool_name}",
                        error_category="validation",
                        is_retryable=False,
                    )

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": json.dumps(result),
                })

            # Feed tool results back into the conversation
            messages.append({
                "role": "user",
                "content": tool_results
            })

        else:
            # Unexpected stop reason
            return {
                "status": "unexpected_stop",
                "stop_reason": response.stop_reason,
                "messages": messages,
            }

    return {
        "status": "max_iterations_reached",
        "iterations": max_iterations,
        "messages": messages,
    }