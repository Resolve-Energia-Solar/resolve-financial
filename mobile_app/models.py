from django.db import models


class API(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'API'
        ordering = ['name']
    

class Discount(models.Model):
    banner = models.ImageField(upload_to='discounts')
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=100, blank=True, null=True)
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Promoção'
        verbose_name_plural = 'Promoções'
        ordering = ['title']


class Reel(models.Model):
    video = models.FileField(upload_to='reels')
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=100, blank=True, null=True)
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Reel'
        verbose_name_plural = 'Reels'
        ordering = ['title']
    

class Media(models.Model):
    image = models.ImageField(upload_to='media')
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=100, blank=True, null=True)
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Mídia'
        verbose_name_plural = 'Mídias'
        ordering = ['title']