from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.

class FAQ(models.Model):
    """FAQ model for frequently asked questions."""

    question = models.CharField(
        max_length=255,
        verbose_name=_("Question"),
        help_text=_("Question for this FAQ")
    )

    answer = models.TextField(
        verbose_name=_("Answer"),
        help_text=_("Answer for this FAQ")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("FAQ")
        verbose_name_plural = _("FAQs")

    def __str__(self):
        return self.question


class StaticPage(models.Model):
    """Model for static pages like Terms, Privacy Policy, etc."""
    
    class PageType(models.TextChoices):
        TERMS = "terms", _("Terms and Conditions")
        PRIVACY_POLICY = "privacy_policy", _("Privacy Policy")
        ACHAM_HISTORY = "acham_history", _("Acham History")
        WORK_WITH_US = "work_with_us", _("Work With Us")
        DECLARATION_OF_CONFORMITY = "declaration_of_conformity", _("Declaration of Conformity")
        RETURNS = "returns", _("Returns")
    
    page_type = models.CharField(
        max_length=50,
        choices=PageType.choices,
        unique=True,
        verbose_name=_("Page Type"),
        help_text=_("Type of static page")
    )
    
    title = models.CharField(
        max_length=255,
        verbose_name=_("Title"),
        help_text=_("Page title")
    )
    
    image = models.ImageField(
        upload_to='static_pages/',
        verbose_name=_("Image"),
        help_text=_("Page image (optional)"),
        blank=True,
        null=True
    )
    
    content = models.TextField(
        verbose_name=_("Content"),
        help_text=_("Page content (HTML allowed)")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['page_type']
        verbose_name = _("Static Page")
        verbose_name_plural = _("Static Pages")
    
    def __str__(self):
        return f"{self.get_page_type_display()} - {self.title}"


class ContactMessage(models.Model):
    """Model for storing contact form submissions."""
    
    first_name = models.CharField(
        max_length=150,
        verbose_name=_("First Name"),
        help_text=_("Contact's first name")
    )
    
    last_name = models.CharField(
        max_length=150,
        verbose_name=_("Last Name"),
        help_text=_("Contact's last name")
    )
    
    email = models.EmailField(
        verbose_name=_("Email"),
        help_text=_("Contact's email address")
    )
    
    phone = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_("Phone Number"),
        help_text=_("Contact's phone number")
    )
    
    subject = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Subject"),
        help_text=_("Message subject/title")
    )
    
    message = models.TextField(
        verbose_name=_("Message"),
        help_text=_("Contact's message")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Contact Message")
        verbose_name_plural = _("Contact Messages")
    
    def __str__(self):
        return f"Contact from {self.first_name} {self.last_name} ({self.email}) - {self.created_at.strftime('%Y-%m-%d')}"


class ReturnRequest(models.Model):
    """Model for storing return request form submissions."""
    
    order_number = models.CharField(
        max_length=255,
        verbose_name=_("Order Number"),
        help_text=_("Order number for the return request")
    )
    
    email_or_phone = models.CharField(
        max_length=255,
        verbose_name=_("Email or Phone Number"),
        help_text=_("Contact email or phone number")
    )
    
    message = models.TextField(
        verbose_name=_("Message"),
        help_text=_("Return request message/details")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Return Request")
        verbose_name_plural = _("Return Requests")
    
    def __str__(self):
        return f"Return request for order {self.order_number} - {self.created_at.strftime('%Y-%m-%d')}"