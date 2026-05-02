from django.db import models
from django.utils import timezone
from stores.models import Store


class Waybill(models.Model):
    store = models.ForeignKey(
        Store, on_delete=models.DO_NOTHING, null=False, verbose_name='Склад'
    )
    counteragent = models.ForeignKey(
        Store, on_delete=models.DO_NOTHING, null=False,
        verbose_name='Контрагент', related_name='counteragent'
    )
    comment = models.TextField(
        null=True, default=None, verbose_name='Комментарий'
    )
    status = models.CharField(max_length=16, null=False, default='Created')
    created_by = models.ForeignKey(
        'authentication.User', on_delete=models.DO_NOTHING, null=False
    )
    processed_by = models.ForeignKey(
        'authentication.User', on_delete=models.DO_NOTHING, null=True,
        related_name='processed_by', default=None
    )
    created_at = models.DateTimeField(null=False, default=timezone.now)
    processed_at = models.DateTimeField(null=True, default=None)

    class Meta:
        db_table = 'waybills'
        verbose_name = 'накладная'
        verbose_name_plural = 'накладные'
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['store', 'counteragent']),
            models.Index(fields=['created_by', 'created_at']),
            models.Index(fields=['processed_by', 'processed_at']),
        ]


class WaybillItem(models.Model):
    waybill = models.ForeignKey(Waybill, on_delete=models.CASCADE, null=False)
    product_id = models.UUIDField(null=False, db_index=True)
    amount = models.FloatField(null=False, default=0.0)

    class Meta:
        db_table = 'waybills_items'
        indexes = [
            models.Index(fields=['waybill', 'product_id']),
            models.Index(fields=['product_id', 'amount']),
        ]
