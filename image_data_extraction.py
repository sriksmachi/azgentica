import base64
from langchain_core.messages import HumanMessage


def encode_image(image_path):
    '''Getting the base64 string'''
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def create_prompt_with_image(image_path, prompt):
    """Create a prompt with the image included."""
    # img_base64 = encode_image(image_path)
    return [
        HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                            # Use base64 encoded image
                            "url": f"data:image/jpeg;base64,{image_path}"
                    },
                },
            ]
        )
    ]

# Function to summarize an image using the LLM client


def image_analysis(image_path, llm_client, prompt):
    """Make image summary"""
    img_base64 = encode_image(image_path)
    result = llm_client.invoke(
        [
            HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            # Use base64 encoded image
                            "url": f"data:image/jpeg;base64,{img_base64}"
                        },
                    },
                ]
            )
        ]
    )

    return result


if __name__ == "__main__":
    # Example usage
    image_path = "protect-apis.png"
    result_json = image_analysis(image_path)
    print(result_json)
