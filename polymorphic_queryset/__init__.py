from django.db.models import Q
from django.utils.tree import Node


class QueryableMeta(type):
    def __init__(cls, *args, **kwargs):
        type.__init__(cls, *args, **kwargs)

        root = True
        for inheritor_cls in cls.get_inheritor_classes():
            inheritor_cls.inheritors.append(cls)
            root = False

        cls.inheritors = []

        if root:
            cls.check_model_name()
        else:
            assert hasattr(cls, "model_name") and cls.model_name, (
                "You must specify attribute 'model_name' for queryset {queryset_name}.".format(queryset_name=cls.__name__)
            )
    
    def get_inheritor_classes(cls):
        return (base_cls for base_cls in cls.__bases__ if isinstance(base_cls, QueryableMeta))

    def check_model_name(cls):
        for inheritor_cls in cls.get_inheritor_classes():
            parent_model_name = getattr(inheritor_cls, "model_name", None)
            assert parent_model_name and parent_model_name != cls.model_name, (
                "Model name in '{class_name}' is the same as in '{inherited_class_name}'.".format(
                    class_name=cls.__name__,
                    inherited_class_name=inheritor_cls.__name__
                )
            )
            

class Queryable(object, metaclass=QueryableMeta):
    inheritors = []
    model_name = None

    @classmethod
    def add_inheritor(cls, inheritor):
        if issubclass(inheritor, cls):
            cls.inheritors.append(cls)
        else:
            raise TypeError("Inheritor of this class must be the same class or subclass.")

    @classmethod
    def remove_inheritor(cls, inheritor):
        cls.inheritors.remove(inheritor)

    @classmethod
    def conditions(cls, query, *args, **kwargs):
        conditions = query(cls, *args, **kwargs)
        distinct = query.distinct

        for inheritor_cls in cls.inheritors:
            queryset_conditions = query.default_conditions
            query_name = query.__name__
            query_method = getattr(inheritor_cls, query_name, None)

            if query_method is not query:
                queryset_conditions, distinct = inheritor_cls.conditions(
                    query_method.conditions, *args, **kwargs
                )
                if not queryset_conditions:
                    queryset_conditions = query.default_conditions

                if not isinstance(queryset_conditions, Q):
                    raise ValueError(
                        "Filter '{query_name}' for '{inheritor_class_name}' returned not a Q object.".format(
                            query_name=query_name,
                            inheritor_class_name=inheritor_cls.__name__
                        )
                    )

            query_model_name = inheritor_cls.model_name.lower()
            cls.rename_conditions_to_inherited_model(queryset_conditions, query_model_name)

            if conditions is None:
                conditions = query.default_conditions
            if queryset_conditions != query.default_conditions:
                inherited_model_cls_not_included = query_model_name + "__isnull"
                conditions &= Q(**{inherited_model_cls_not_included: True})
                conditions |= (
                    Q(**{inherited_model_cls_not_included: False}) & queryset_conditions
                )
        return conditions, distinct

    @classmethod
    def rename_conditions_to_inherited_model(cls, queryset_conditions, query_model_name):
        for index, child in enumerate(queryset_conditions.children):
            if isinstance(child, Node):
                cls.rename_conditions_to_inherited_model(child, query_model_name)
            else:
                param_name, param_value = child
                param_key = query_model_name + "__" + param_name
                queryset_conditions.children[index] = param_key, param_value
        return queryset_conditions


class query(object):
    @staticmethod
    def none():
        return Q(pk=-1)

    @staticmethod
    def default_conditions():
        return Q()

    @staticmethod
    def all():
        return query.default_conditions()

    def __init__(self, distinct=False):
        self.distinct = distinct

    def __call__(self, base_method):
        def query_wrapper(queryset, *args, **kwargs):
            conditions, distinct = queryset.conditions(base_method, *args, **kwargs)

            results = queryset.filter(conditions)
            if distinct:
                results = results.distinct()
            return results

        base_method.distinct = self.distinct
        base_method.default_conditions = query.default_conditions
        query_wrapper.conditions = base_method
        return query_wrapper
