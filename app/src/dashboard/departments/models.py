from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=128, primary_key=True, null=False)
    iiko_name = models.CharField(max_length=128, null=True, default=None)
    iiko_id = models.UUIDField(null=True, default=None)

    objects = models.Manager()

    class Meta:
        db_table = 'departments'
        verbose_name = 'подразделение'
        verbose_name_plural = 'подразделения'

    def __str__(self):
        return self.name
