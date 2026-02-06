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


class EmailSubscription(models.Model):
    """Model for storing email newsletter subscriptions."""
    
    LANGUAGE_CHOICES = [
        ('ru', _('Russian')),
        ('en', _('English')),
        ('uz', _('Uzbek')),
    ]
    
    email = models.EmailField(
        unique=True,
        verbose_name=_("Email"),
        help_text=_("Email address for newsletter subscription")
    )
    
    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='ru',
        verbose_name=_("Language"),
        help_text=_("Preferred language for emails")
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Whether this subscription is active")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Email Subscription")
        verbose_name_plural = _("Email Subscriptions")
    
    def __str__(self):
        return f"Subscription: {self.email} ({self.language}) - {self.created_at.strftime('%Y-%m-%d')}"


class AboutPageSection(models.Model):
    """Singleton model for About page content that can be edited through admin."""
    
    # Hero section fields
    founder_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Founder Name"),
        help_text=_("Name of the founder (for hero section)")
    )
    founder_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Founder Title"),
        help_text=_("Title/role of the founder (e.g., 'Founder of ACHAM')")
    )
    hero_image = models.ImageField(
        upload_to='about_page/',
        blank=True,
        null=True,
        verbose_name=_("Hero Image"),
        help_text=_("Hero section image (founder photo)")
    )
    
    # History section fields
    history_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("History Title"),
        help_text=_("Title for history section")
    )
    history_content = models.TextField(
        blank=True,
        verbose_name=_("History Content"),
        help_text=_("Content for history section")
    )
    history_image = models.ImageField(
        upload_to='about_page/',
        blank=True,
        null=True,
        verbose_name=_("History Image"),
        help_text=_("Image for history section")
    )
    
    # Philosophy section fields
    philosophy_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Philosophy Title"),
        help_text=_("Title for philosophy section")
    )
    philosophy_content = models.TextField(
        blank=True,
        verbose_name=_("Philosophy Content"),
        help_text=_("Content for philosophy section")
    )
    philosophy_image = models.ImageField(
        upload_to='about_page/',
        blank=True,
        null=True,
        verbose_name=_("Philosophy Image"),
        help_text=_("Image for philosophy section")
    )
    
    # Fabrics section fields
    fabrics_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Fabrics Title"),
        help_text=_("Title for fabrics section")
    )
    fabrics_content = models.TextField(
        blank=True,
        verbose_name=_("Fabrics Content"),
        help_text=_("Content for fabrics section")
    )
    fabrics_image = models.ImageField(
        upload_to='about_page/',
        blank=True,
        null=True,
        verbose_name=_("Fabrics Image"),
        help_text=_("Main image for fabrics section")
    )
    fabrics_image_2 = models.ImageField(
        upload_to='about_page/',
        blank=True,
        null=True,
        verbose_name=_("Fabrics Image 2"),
        help_text=_("Additional image for fabrics section")
    )
    fabrics_image_3 = models.ImageField(
        upload_to='about_page/',
        blank=True,
        null=True,
        verbose_name=_("Fabrics Image 3"),
        help_text=_("Additional image for fabrics section")
    )
    
    # Process section fields
    process_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Process Title"),
        help_text=_("Title for process section")
    )
    process_description = models.TextField(
        blank=True,
        verbose_name=_("Process Description"),
        help_text=_("Description for process section")
    )
    process_items = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Process Items"),
        help_text=_("List of process items with icons and labels (JSON format)")
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Whether the page is displayed")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("About Page")
        verbose_name_plural = _("About Page")
    
    def __str__(self):
        return _("About Page Content")
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance."""
        instance, created = cls.objects.get_or_create(pk=1)
        return instance
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists."""
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of singleton instance."""
        pass