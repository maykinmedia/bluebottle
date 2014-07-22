from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _
from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField
from djchoices import DjangoChoices, ChoiceItem

from django.contrib.auth import get_user_model

USER_MODEL = get_user_model()


class DonationStatuses(DjangoChoices):
    new = ChoiceItem('new', label=_("New"))
    in_progress = ChoiceItem('in_progress', label=_("In progress"))
    pending = ChoiceItem('pending', label=_("Pending"))
    paid = ChoiceItem('paid', label=_("Paid"))
    failed = ChoiceItem('failed', label=_("Failed"))


class Donation(models.Model):
    """
    Donation of an amount from a user to a project.
    """
    amount = models.DecimalField(_("Amount"), max_digits=16, decimal_places=2)

    # User is just a cache of the order user.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("User"), null=True, blank=True)
    project = models.ForeignKey(settings.PROJECTS_PROJECT_MODEL, verbose_name=_("Project"))
    order = models.ForeignKey('bb_orders.Order', verbose_name=_("Order"), related_name='donations', null=True, blank=True)

    status = models.CharField(_("Status"), max_length=20, choices=DonationStatuses.choices, default=DonationStatuses.new, db_index=True)

    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))
    completed = models.DateTimeField(_("Ready"), blank=True, editable=False, null=True)

