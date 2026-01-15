from django.views.generic import TemplateView
from .models import AboutPageSection


class AboutPageView(TemplateView):
    """View for displaying the About page with editable sections."""
    template_name = "pages/about.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all active sections ordered by their order field
        sections = AboutPageSection.objects.filter(is_active=True).order_by('order', 'section_type')
        
        # Organize sections by type for easy access in template
        context['hero_section'] = sections.filter(section_type=AboutPageSection.SectionType.HERO).first()
        context['history_section'] = sections.filter(section_type=AboutPageSection.SectionType.HISTORY).first()
        context['philosophy_section'] = sections.filter(section_type=AboutPageSection.SectionType.PHILOSOPHY).first()
        context['fabrics_section'] = sections.filter(section_type=AboutPageSection.SectionType.FABRICS).first()
        context['process_section'] = sections.filter(section_type=AboutPageSection.SectionType.PROCESS).first()
        
        # Also provide all sections as a list
        context['sections'] = sections
        
        return context

