from django.db import models

class GalleryItem(models.Model):
    title = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to="gallery/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "File"
        verbose_name_plural = "Files"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title or self.file.name
