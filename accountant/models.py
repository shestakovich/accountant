from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import CustomUser

User = get_user_model()


class Company(models.Model):
    name = models.CharField(max_length=1024)

    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Service(models.Model):
    name = models.CharField(max_length=1024)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='services')

    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('company', 'name')


class Client(models.Model):
    name = models.CharField(max_length=1024, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='clients')

    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"ID:{str(self.id)}"


class Sale(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='sales')
    client = models.ForeignKey(Client,
                               on_delete=models.SET_NULL,
                               blank=True,
                               null=True,
                               related_name='purchases'
                               )

    date = models.DateTimeField(auto_now_add=True)
    service_provider = models.ForeignKey(User,
                                         on_delete=models.SET_NULL,
                                         related_name='rendered_services',
                                         blank=True,
                                         null=True
                                         )

    def __str__(self):
        return f"{self.client.name} {self.date}"


class SoldService(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='services')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='sold')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    lead_time = models.DurationField(null=True, blank=True)
    amount = models.IntegerField(default=1)

    def __str__(self):
        return ' '.join([str(self.service), str(self.price)])


@receiver(post_save, sender=CustomUser)
def add_company(sender, instance, created, **kwargs):
    if created and instance.company is None:
        instance.company = Company.objects.create(name=instance.username)
        instance.save()
