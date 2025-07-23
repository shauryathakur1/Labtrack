from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import (
    BaseUserManager,
    AbstractBaseUser,
    PermissionsMixin,
)
from django.contrib.auth import get_user_model



from django.contrib.auth.models import Group, Permission

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('lab_expert', 'Lab Expert'),
        ('teacher', 'Teacher'),
        ('other', 'Other'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
        related_query_name='customuser',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
        related_query_name='customuser',
    )

msds_file = models.FileField(upload_to='msds/', null=True, blank=True)

# Create your models here.
class UserAccountManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError('Users must have an email address')

        email = self.normalize_email(email)
        email = email.lower()

        user = self.model(
            email=email,
            **kwargs
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **kwargs):
        user = self.create_user(
            email,
            password=password,
            **kwargs
        )

        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


from django.contrib.auth.models import Group, Permission

class UserAccount(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, max_length=255)

    groups = models.ManyToManyField(
        Group,
        related_name='useraccount_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
        related_query_name='useraccount',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='useraccount_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
        related_query_name='useraccount',
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email
    
User = get_user_model() 
class Chemical(models.Model):
    FORM_CHOICES = [
        ('powder', 'Powder'),
        ('aqueous', 'Aqueous'),
        ('crystalline', 'Crystalline'),
    ]

    DANGER_LEVELS = [
        ('green', 'All users'),
        ('yellow', 'Teachers & Assistants'),
        ('red', 'Teachers only'),
    ]

    name = models.CharField(max_length=100)
    form = models.CharField(max_length=20, choices=FORM_CHOICES)
    concentration = models.CharField(max_length=50, blank=True, null=True)
    volume = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    quantity = models.IntegerField()
    storage_location = models.CharField(max_length=255)
    expiry_date = models.DateField()
    msds_file = models.FileField(upload_to='msds/', null=True, blank=True)
    danger_classification = models.CharField(max_length=10, choices=DANGER_LEVELS)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.form})"


class Equipment(models.Model):
    CONDITION_CHOICES = [
        ('working', 'Working'),
        ('needs_maintenance', 'Needs Maintenance'),
        ('broken', 'Broken'),
    ]

    name = models.CharField(max_length=100)
    condition = models.CharField(max_length=30, choices=CONDITION_CHOICES)
    quantity = models.IntegerField()
    last_maintenance_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    changes = models.TextField(blank=True, null=True)  # JSON diff or description

    def __str__(self):
        return f"{self.user} {self.action} {self.model_name} {self.object_id} at {self.timestamp}"