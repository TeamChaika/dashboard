from core.iiko import iiko_api
from stores.models import Store


def run():
    stores = Store.objects.all()
    stores_ids = set(map(str, stores.values_list('id', flat=True)))
    stores_names = set(map(str, stores.values_list('name', flat=True)))
    iiko_stores = iiko_api.get_stores()
    new = []
    for store in iiko_stores:
        if store['id'] not in stores_ids and store['name'] not in stores_names:
            new.append(Store(id=store['id'], name=store['name']))
    if new:
        Store.objects.bulk_create(new)
