import os
from django.shortcuts import render, get_object_or_404
from django.template import Template, Context
from .models import Template as PlanTemplate, Response
from django.utils.safestring import mark_safe

import markdown
import openai
import tiktoken


model = "chatgpt"
model_version = "gpt-3.5-turbo-16k"
openai.api_key = os.getenv("OPENAI_API_KEY")


def get_system_message(race_type, parsed_target_time):
    return f"You are advising a running coach working with an athlete, who is training for a { race_type }. They are training to complete the { race_type } in a time of { parsed_target_time }."


def send_to_chatgpt4(system_message, prompt_header, prompt_content):
    response = openai.ChatCompletion.create(
        model=model_version,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt_header},
            {"role": "user", "content": prompt_content},
        ],
        temperature=0.4,
        max_tokens=8000,
    )

    print(response)
    # Process the response and extract the generated message
    generated_message = response["choices"][0]["message"]["content"]

    return generated_message


def format_distance(race_distance):
    return race_distance.replace("-", " ")


def get_max_distance(race_distance):
    if race_distance == "5km":
        return "3.1"
    elif race_distance == "10km":
        return "6.2"
    elif race_distance == "half-marathon":
        return "13.1"
    else:
        return "26.2"


def format_time(hours_input=0, minutes_input=0):
    hours = int(hours_input)
    minutes = int(minutes_input)
    if hours == 0 and minutes == 1:
        return "1 minute"
    elif hours == 1 and minutes == 0:
        return "1 hour"
    elif hours == 0:
        return f"{minutes} minutes"
    elif minutes == 0:
        return f"{hours} hours"
    else:
        return f"{hours} hours {minutes} minutes"


def index(request):
    if request.method == "POST":
        email = request.POST.get("email")
        target_time = request.POST.get("target_time")
        race_distance = request.POST.get("race_distance")

        print(" ------------------------ ")
        print(target_time)
        print(race_distance)
        print(" ------------------------ ")

        parsed_target_time = format_time(*target_time.split(":"))
        max_distance = get_max_distance(race_distance)
        parsed_race_distance = format_distance(race_distance)

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
            context = Context(
                {
                    "race_distance": parsed_race_distance,
                    "target_time": parsed_target_time,
                    "max_distance": max_distance,
                }
            )
            header_content = prompt_header_temp.render(context)
            prompt_content = prompt_content_temp.render(context)

            print(get_system_message(parsed_race_distance, parsed_target_time))
            print(header_content)
            print(prompt_content)

            response = send_to_chatgpt4(
                system_message=get_system_message(
                    parsed_race_distance, parsed_target_time
                ),
                prompt_header=header_content,
                prompt_content=prompt_content,
            )

            encoding = tiktoken.encoding_for_model("gpt-4")
            tokens = encoding.encode(response)

            Response.objects.create(
                response=response,
                email=email,
                template=template,
                template_version=latest_version,
                model=model,
                model_version=model_version,
                token_length=len(
                    tokens
                ),  # Assuming token length is the number of words
            )

            html_content = markdown.markdown(response)
            safe_html_content = mark_safe(html_content)

            return render(request, "plans/view.html", {"content": safe_html_content})

    return render(request, "plans/index.html")


def response_detail(request, id):
    item = get_object_or_404(Response, id=id)
    html_content = markdown.markdown(item.response)
    safe_html_content = mark_safe(html_content)
    return render(request, "plans/view.html", {"content": safe_html_content})
