from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # INHERITED FIELDS:
        # id (pk)
        # password
        # last_login
        # is_superuser
        # first_name
        # last_name
        # is_staff
        # is_active
        # date_joined
    username = models.CharField(max_length=24, unique=True)
    email = models.EmailField(max_length=254, unique=True, blank=False)
    storage_limit = models.BigIntegerField(default=10737418240) # default is 10GB 
