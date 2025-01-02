from django.db import models


class API(models.Model):
    name = models.CharField('Nome', max_length=100)
    url = models.URLField('URL')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'APIs'
        ordering = ['name']
    

class Discount(models.Model):
    banner = models.ImageField('Banner', upload_to='discounts')
    title = models.CharField('Título', max_length=100)
    description = models.TextField('Descrição', blank=True, null=True)
    link = models.URLField('Link', blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Promoção'
        verbose_name_plural = 'Promoções'
        ordering = ['title']


class Reel(models.Model):
    video = models.FileField('Vídeo', upload_to='reels')
    title = models.CharField('Título', max_length=100)
    description = models.TextField('Descrição', blank=True, null=True)
    link = models.URLField('Link', blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Reel'
        verbose_name_plural = 'Reels'
        ordering = ['title']
    

class Media(models.Model):
    image = models.ImageField('Imagem', upload_to='media')
    title = models.CharField('Título', max_length=100)
    description = models.TextField('Descrição', blank=True, null=True)
    link = models.URLField('Link', blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Mídia'
        verbose_name_plural = 'Mídias'
        ordering = ['title']


class Product(models.Model):
    name = models.CharField('Nome', max_length=100)
    description = models.TextField('Descrição', blank=True, null=True)
    price = models.DecimalField('Preço', max_digits=8, decimal_places=2)
    image = models.ImageField('Imagem', upload_to='products')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['name']
