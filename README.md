# Django Polymorphic QuerySet
Helps to implement filtering logic depended on model type.

*You should not confuse filtering and permission checking. If you need to get items based on user, you should probably
use Django Permissions.*

## Motivation

For example, your application have two models: `Product` and derived from it `PerishableProduct`:

```python
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=120)
    
    
class PerishableProduct(Product):
    is_perished = models.BooleanField(default=False)
    
    
class BrokenProduct(Product):
    repaired = models.BooleanField(default=False)

```

If you want to add a view that returns *active* products (products that are not perished and repaired) with 
this hierarchy you will probably end with a one function that contains all that conditions:

```python
from django.db import models

class ProductQuerySet(models.QuerySet):
    def get_active_products(self):
        return self.filter(
            perishableproduct__is_perished=False,
            brokenproduct__repaired=True
        )
```

In a big application with a lot of models and conditions this function can become complex and difficult to maintain.
Also, with this implementation base queryset will know about details of derived models.

QuerySet filter methods can be separated in a parallel hierarchy, so that derived QuerySets will add a custom logic 
to base methods or override them:

```python
# Not a real example, just the idea.

from django.db import models

class ProductQuerySet(models.QuerySet):
    def get_active_products(self):
        return self.all()


class PerishableProductQuerySet(ProductQuerySet):
    def get_active_products(self):
        return self.filter(is_perished=False)
        
        
class BrokenProductQuerySet(ProductQuerySet):
    def get_active_products(self):
        return self.filter(repaired=True)
``` 

But in this implementation `ProductQuerySet` will return all products including products that were saved
as `PerishableProduct` with `is_perished` equal to `True` and `BrokenProduct` with `repaired` equal to `False`. 

## Solution
This library allows you to create polymorphic querysets that takes into account all conditions in a queryset 
hierarchy:
```python
from polymorphic_queryset import Queryable, query
from django.db import models

class ProductQuerySet(Queryable, models.QuerySet):
    model_name = "Product"

    @query()
    def get_active_products(self):
        return query.all()
      
        
class PerishableProductQuerySet(ProductQuerySet):
    model_name = "PerishableProduct"

    @query()
    def get_active_products(self):
        return models.Q(is_perished=False)


class BrokenProductQuerySet(ProductQuerySet):
    model_name = "BrokenProduct"

    @query()
    def get_active_products(self):
        return models.Q(repaired=True)
```

This implementation separates query conditions between different QuerySets based on a specified model name.
`ProductQuerySet.get_active_products` will return any product that was saved as `Product`,
products that were saved as `PerishableProduct` if `is_perished` is *False* and `BrokenProduct` is `repaired` is *True*.
QuerySet will still return `Product` instances.

*You can use **django-polymorphic** library to return instances of derived classes instead.*

You can now use these querysets as a model manager:
```python
from django.db import models

class Product(models.Model):
    objects = ProductQuerySet.as_manager()
    
    
class PerishableProduct(Product):
    objects = PerishableProductQuerySet.as_manager()


class BrokenProduct(Product):
    objects = BrokenProductQuerySet.as_manager()
    

active_products = Product.objects.get_active_products()
```

To use conditions of base classes in your querysets you can call `conditions` function of your method decorated with `query`:
```python
from polymorphic_queryset import Queryable, query
from django.db import models
import datetime


class ProductQuerySet(Queryable, models.QuerySet):
    model_name = "Product"

    @query()
    def get_new_products(self):
        return models.Q(date_created__gte=datetime.datetime.now() - datetime.timedelta(weeks=1))
        

class PerishableProductQuerySet(ProductQuerySet):
    model_name = "PerishableProduct"
    
    @query()
    def get_new_products(self):
        return super().get_new_products.conditions(self) & models.Q(date_perished__lt=datetime.datetime.now())        
```

In this example `get_new_products` will return any `Product` that was created less than a week ago or 
`PerishableProduct` if it was created a week ago and won't perish today.