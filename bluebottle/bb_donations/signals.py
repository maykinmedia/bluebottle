from django_fsm.signals import post_transition
from bluebottle.bb_donations.donationmail import successful_donation_fundraiser_mail, new_oneoff_donation
from bluebottle.utils.model_dispatcher import get_order_model
from bluebottle.utils.utils import StatusDefinition
from django.dispatch.dispatcher import receiver

ORDER_MODEL = get_order_model()


@receiver(post_transition, sender=ORDER_MODEL)
def _order_status_changed(sender, instance, **kwargs):
    """
    - Update amount on project when order is in an ending status.
    - Get the status from the Order and Send an Email.
    """

    if instance.status in [StatusDefinition.SUCCESS, StatusDefinition.PENDING, StatusDefinition.FAILED]:
        for donation in instance.donations.all():
            donation.project.update_amounts()

        # Send mail if status transitions in ro success/pending for the first time.
        if (kwargs['source'] not in [StatusDefinition.SUCCESS, StatusDefinition.PENDING]
            and  kwargs['target'] in [StatusDefinition.SUCCESS, StatusDefinition.PENDING]):

            for donation in instance.donations.all():
                successful_donation_fundraiser_mail(donation)
                new_oneoff_donation(donation)
