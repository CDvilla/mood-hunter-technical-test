from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Request(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        IN_REVIEW = "in_review", "In review"
        IN_PROGRESS = "in_progress", "In progress"
        PAUSED = "paused", "Paused"
        DONE = "done", "Done"

    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED,
        help_text="Stable textual status code; no database catalog ID is used.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "requests"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
