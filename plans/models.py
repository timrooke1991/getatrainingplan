from django.db import models
from django.utils import timezone
import tiktoken


def generate_token_length(text):
    encoding = tiktoken.encoding_for_model("gpt-4")
    tokens = encoding.encode(text)
    return len(tokens)


class Template(models.Model):
    key = models.CharField(max_length=100)
    name = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(max_length=800, null=True, blank=True)

    def __str__(self):
        return self.key


class TemplateVersion(models.Model):
    template = models.ForeignKey(
        Template, on_delete=models.CASCADE, related_name="versions"
    )
    header = models.TextField()
    content = models.TextField()
    token_length = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.pk:  # Only set the value if the instance is being created

            self.token_length = generate_token_length(
                self.header
            ) + generate_token_length(self.content)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Version {self.id} of {self.template.key}"


class Response(models.Model):
    request_system_message = models.TextField(null=True, blank=True)
    request_header = models.TextField(null=True, blank=True)
    request_content = models.TextField(null=True, blank=True)
    response = models.TextField()
    email = models.EmailField(max_length=255, null=True, blank=True)
    model = models.CharField(max_length=30, null=True, blank=True)
    model_version = models.CharField(max_length=30, null=True, blank=True)
    token_length = models.PositiveIntegerField()
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    template_version = models.ForeignKey(TemplateVersion, on_delete=models.CASCADE)

    def __str__(self):
        return f"Response ID: {self.id}"
