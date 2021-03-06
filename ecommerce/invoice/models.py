from django_extensions.db.models import TimeStampedModel
from django.db import models
from django.utils.translation import ugettext_lazy as _
from simple_history.models import HistoricalRecords


class Invoice(TimeStampedModel):
    NOT_PAID, PAID = 'Not Paid', 'Paid'
    state_choices = (
        (NOT_PAID, _('Not Paid')),
        (PAID, _('Paid')),
    )
    basket = models.ForeignKey('basket.Basket', null=True, blank=True)
    order = models.ForeignKey('order.Order', null=True, blank=False)
    business_client = models.ForeignKey('core.BusinessClient', null=True, blank=False)
    state = models.CharField(max_length=255, default=NOT_PAID, choices=state_choices)

    history = HistoricalRecords()

    @property
    def total(self):
        """Total amount paid for this Invoice"""
        return self.order.total_incl_tax

    @property
    def client(self):
        """Client for this invoice"""
        return self.business_client
