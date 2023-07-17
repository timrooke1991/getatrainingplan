import re
import os
import uuid
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.template import Template, Context
from .models import Template as PlanTemplate, Response
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string

import pdfkit

import markdown
import openai
import tiktoken


model = "chatgpt"
model_version = "gpt-3.5-turbo-16k"
openai.api_key = os.getenv("OPENAI_API_KEY")


# Regex patterns
TIME_PATTERN = r"^([01]?[0-9]|2[0-3])(:[0-5][0-9]){1,2}$"
EMAIL_PATTERN = r"^[\w\.-]+@[\w\.-]+\.\w+$"


def validate_form(request):

    # Get form data
    age = request.POST.get("age")
    gender = request.POST.get("gender")
    experience = request.POST.get("experience")
    email = request.POST.get("email")
    event = request.POST.get("event")
    target = request.POST.get("target")
    pb = request.POST.get("pb")
    length = request.POST.get("length")
    frequency = request.POST.get("frequency")

    # Validation
    errors = {}

    if not re.match(r"^\d+$", str(age)) or int(age) < 0:
        errors["age"] = "Invalid age"

    if gender not in ["male", "female", "non-binary", "prefer-not-to-say"]:
        errors["gender"] = "Invalid gender"

    if experience not in ["beginner", "intermediate", "advanced", "elite"]:
        errors["experience"] = "Invalid experience"

    if not re.match(EMAIL_PATTERN, email):
        errors["email"] = "Invalid email"

    if event not in ["marathon", "half-marathon", "10km", "5km"]:
        errors["event"] = "Invalid event"

    if not re.match(TIME_PATTERN, target):
        errors["target"] = "Invalid target time"

    if not re.match(TIME_PATTERN, pb):
        errors["pb"] = "Invalid PB time"

    if not re.match(r"^\d+$", str(length)) or int(length) < 1:
        errors["length"] = "Invalid length"

    if not re.match(r"^\d+$", str(frequency)) or int(frequency) < 1:
        errors["frequency"] = "Invalid frequency"

    if len(errors) > 0:
        return {"status": "Error", "errors": errors}

    return {
        "status": "Success",
        "data": {
            "personal": {
                "age": age,
                "gender": gender,
                "experience": experience,
                "email": email,
            },
            "goal": {
                "event": format_dash(event),
                "target": target,
                "pb": pb,
            },
            "training": {
                "length": length,
                "frequency": frequency,
                "max_distance": get_max_distance(event),
            },
        },
    }


def get_system_message(data):
    gender = (
        ""
        if data["personal"]["gender"] == "prefer-not-to-say"
        else format_dash(data["personal"]["gender"])
    )

    return f'You are advising a running coach working with a {gender} athlete, who is training for a { data["goal"]["event"] }. They are training to complete the { data["goal"]["event"] } in a time of { data["goal"]["target"] }. They are an { data["personal"]["experience"]} runner who has a { data["goal"]["event"] } personal best time of { data["goal"]["pb"] }.'


def send_to_chatgpt4(system_message, prompt_header, prompt_content):
    print("Sending request to chatGPT")
    response = openai.ChatCompletion.create(
        model=model_version,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt_header},
            {"role": "user", "content": prompt_content},
        ],
        temperature=0.8,
        max_tokens=7000,
    )

    print(response)
    # Process the response and extract the generated message
    generated_message = response["choices"][0]["message"]["content"]

    return generated_message


def format_dash(text):
    return text.replace("-", " ")


def get_max_distance(race_distance):
    if race_distance == "5km":
        return "3.1"
    elif race_distance == "10km":
        return "6.2"
    elif race_distance == "half-marathon":
        return "13.1"
    else:
        return "26.2"


def index(request):
    if request.method == "POST":

        form_data = validate_form(request)
        if form_data["status"] == "Success":
            parsed_data = form_data["data"]

            # Fetch the template by its key
            template = PlanTemplate.objects.get(key="run_plan")

            # Get the latest TemplateVersion for the template
            latest_version = template.versions.order_by("-id").first()

            if latest_version:
                template_header = latest_version.header
                # Create a Django template object from the template content
                template_content = latest_version.content
                prompt_header_temp = Template(template_header)
                prompt_content_temp = Template(template_content)

                # Render the template with user-submitted context data
                context = Context({"data": parsed_data})
                header_content = prompt_header_temp.render(context)
                prompt_content = prompt_content_temp.render(context)

                # ai_response = send_to_chatgpt4(
                #     system_message=get_system_message(parsed_data),
                #     prompt_header=header_content,
                #     prompt_content=prompt_content,
                # )

                # # Token encoding
                # encoding = tiktoken.encoding_for_model("gpt-4")
                # tokens = encoding.encode(ai_response)

                # print("Storing response")

                # Response.objects.create(
                #     request_system_message=get_system_message(parsed_data),
                #     request_header=header_content,
                #     request_content=prompt_content,
                #     response=ai_response,
                #     email=parsed_data["personal"]["email"],
                #     template=template,
                #     template_version=latest_version,
                #     model=model,
                #     model_version=model_version,
                #     token_length=len(
                #         tokens
                #     ),  # Assuming token length is the number of words
                # )

                # html_content = markdown.markdown(response)
                # safe_html_content = mark_safe(html_content)
                html_content = render_to_string("pdf.html", {"data": parsed_data})
                pdf = pdfkit.from_string(html_content, False)

                response = HttpResponse(pdf, content_type="application/pdf")
                response[
                    "Content-Disposition"
                ] = f'attachment; filename="training_plan_{uuid.uuid4().hex}.pdf"'

                return response

    return render(request, "plans/index.html")


def response_detail(request, id):
    item = get_object_or_404(Response, id=id)
    html_content = markdown.markdown(item.response)
    safe_html_content = mark_safe(html_content)
    return render(request, "plans/view.html", {"content": safe_html_content})
