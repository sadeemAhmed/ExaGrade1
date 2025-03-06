import requests
import re
import json
from django.conf import settings

def grade_with_gpt(question_text, student_answer, ideal_answer, max_marks):
    """Calls OpenAI GPT-4o Mini API to grade the answer with detailed logging."""

    api_url = "https://api.openai.com/v1/chat/completions"
    api_key = settings.OPENAI_API_KEY  # ✅ Ensure you have this key in settings.py

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # ✅ Prepare Prompt for AI Grading
    prompt = f"""
    You are an AI grader using GPT-4o Mini. Grade the student's answer based on the ideal response.

    **Question:** {question_text}
    **Ideal Answer:** {ideal_answer}
    **Student Answer:** {student_answer}

    **Instructions:**
    - Assign a **numeric grade between 0 and {max_marks}**.
    - Provide a **brief feedback explanation**.
    - **Format response exactly like this:**
    
    ```
    Grade: X
    Feedback: Y
    ```

    **Example Response:**
    ```
    Grade: 7.5
    Feedback: Your answer is mostly correct but missing one key point.
    ```
    """

    # ✅ API Request Payload
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are an expert AI grader."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3  # ✅ Keep it low for consistent grading
    }

    # ✅ Debugging: Print Payload Sent to GPT-4o
    print("\n🔍 [DEBUG] Sending Request to GPT-4o Mini...")
    print(json.dumps(payload, indent=4))

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response_data = response.json()

        # ✅ Debugging: Print Full API Response
        print("\n✅ [DEBUG] GPT-4o Mini Response Received:")
        print(json.dumps(response_data, indent=4))

        # ✅ Extract AI-generated response text
        ai_response = response_data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

        # ✅ Debugging: Print AI Response Text
        print("\n📝 [DEBUG] Extracted AI Response:")
        print(ai_response)

        # ✅ Use regex to extract numeric grade
        match = re.search(r"Grade:\s*([\d.]+)", ai_response)
        score = float(match.group(1)) if match else 0  # ✅ Default to 0 if no number found

        # ✅ Ensure score does not exceed max marks
        if score > max_marks:
            score = max_marks

        # ✅ Extract feedback (everything after the grade line)
        feedback_lines = ai_response.split("\n")
        feedback = "\n".join([line.strip() for line in feedback_lines if "Grade:" not in line])
        feedback = feedback if feedback else "No feedback provided."

        # ✅ Debugging: Print Extracted Score & Feedback
        print(f"\n🎯 [DEBUG] Final Extracted Score: {score} / {max_marks}")
        print(f"💬 [DEBUG] AI Feedback: {feedback}")

        return round(score, 2), feedback  # ✅ Return properly formatted grade and feedback

    except Exception as e:
        print(f"❌ [ERROR] GPT API Error: {e}")
        return 0, "Error grading answer. Manual review required."
