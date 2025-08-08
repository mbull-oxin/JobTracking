from django.db import models
from adminsortable.models import SortableMixin

class SimpleModel(models.Model):
    class Meta:
        abstract = True

class Location(SimpleModel,SortableMixin):
    name = models.CharField(max_length=60)
    post_hold = models.ForeignKey('self',on_delete=models.SET_NULL,null=True,blank=True)
    class Meta:
        verbose_name_plural = 'Locations'
        ordering = ['order']

    order = models.PositiveIntegerField(default=0, editable=False)
    
    def __str__(self):
        return self.name

class JobState(models.Model):
    id = models.CharField(max_length=60,primary_key=True)
    location = models.ForeignKey('Location',on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    user1 = models.CharField(max_length=60, blank=True, default='')
    user2 = models.CharField(max_length=60, blank=True, default='')
    user3 = models.CharField(max_length=1000, blank=True, default='')

    def __str__(self):
        return self.id

    class Meta:
        verbose_name_plural = 'Jobs'
    
