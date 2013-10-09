from django.conf import settings
from django.db import models
from django.db.models.aggregates import Count, Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.translation import ugettext as _


from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField
from djchoices import DjangoChoices, ChoiceItem
from sorl.thumbnail import ImageField
from taggit_autocomplete_modified.managers import TaggableManagerAutocomplete as TaggableManager


class ProjectPhasesBase(DjangoChoices):
    """
    Convenience class to return previous/next phase.

    DjangoChoices applies ordering either by argument (ChoiceItem.order) or by
    order of addition of the field to the class.
    """

    @classmethod
    def get_current_phase_object(cls, value):
        for field_name, choice_item in cls._fields.items():
            if choice_item.value == value:
                return choice_item
        raise AttributeError("No ChoiceItem with value '%s' was found." % value)

    @classmethod
    def get_next_phase(cls, current_phase_value):
        """ 
        Takes the current phase as argument, returns the next one 

        :param current_phase_value: is a string with the choice value.
        """
        # phases is SortedDict instance
        phases = cls._fields.items() 
        current_phase = cls.get_current_phase_object(current_phase_value)
        next_phases = [phase for field_name, phase in phases if
                        phase.order > current_phase.order]
        if next_phases:
            return next_phases[0].value
        raise IndexError("'%s' was the last phase." % current_phase_value)
        


class ProjectPhases(ProjectPhasesBase):
    pass



class AbstractBaseProject(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                verbose_name = _('initiator'),
                help_text=_('Project owner'),
                related_name='owner'
            )
    title = models.CharField(_("title"), max_length=255, unique=True)
    slug = models.SlugField(_("slug"), max_length=100, unique=True)

    phase = models.CharField(_("phase"), max_length=20, 
                choices=ProjectPhases.choices, 
                help_text=_("Phase this project is in right now.")
            )

    created = CreationDateTimeField(_("created"), 
        help_text=_("When this project was created."))
    updated = ModificationDateTimeField()


    # for rankings (hot, popular, etc...)
    popularity = models.FloatField(null=False, default=0)

    class Meta:
        abstract = True


    def update_popularity(self):
        raise NotImplementedError()