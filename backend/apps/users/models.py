from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.functions import Lower


class UserManager(BaseUserManager):
    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email):
        return super().normalize_email(email).strip().lower()

    def create_user(self, email, name, password=None, **extra_fields):
        if not email or not name.strip():
            raise ValueError("Nome e e-mail são obrigatórios.")
        user = self.model(email=self.normalize_email(email), name=name.strip(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("Superusuário deve possuir is_staff e is_superuser.")
        return self.create_user(email, name, password, **extra_fields)


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None
    name = models.CharField("nome", max_length=150)
    email = models.EmailField("e-mail", unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]
    objects = UserManager()

    class Meta:
        constraints = [models.UniqueConstraint(Lower("email"), name="users_email_case_insensitive_unique")]

    def save(self, *args, **kwargs):
        self.email = UserManager.normalize_email(self.email)
        super().save(*args, **kwargs)

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    def __str__(self):
        return self.email
