from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django_softdelete.managers import SoftDeleteManager
from django_softdelete.models import SoftDeleteModel
from simple_history.models import HistoricalRecords
from core.choices import Roles


class UsuarioManager(SoftDeleteManager, BaseUserManager):
    def create_user(self, username, password=None, rol: Roles = Roles.CIUDADANO, **extra_fields):
        if not username:
            raise ValueError("El nombre de usuario es obligatorio")
        user = self.model(username=username, rol=rol, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, rol=Roles.ADMINISTRADOR, **extra_fields)


class Usuario(SoftDeleteModel, AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=200, unique=True)
    rol = models.CharField(max_length=20, choices=Roles, default=Roles.CIUDADANO)

    is_staff = models.BooleanField(default=False)

    history = HistoricalRecords()
    objects = UsuarioManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []
