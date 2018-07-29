from django.db.models import Q
from django.utils.tree import Node
from functools import partial


class QueryableMeta(type):
    def __init__(cls, *args, **kwargs):
        type.__init__(cls, *args, **kwargs)

        root = True
        for inheritor_cls in cls.get_inheritor_classes():
            inheritor_cls.inheritors.append(cls)
            root = False

        cls.inheritors = []
        cls.bind_queries()

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

    def bind_queries(cls):
        for attr_name, attr in cls.__dict__.items():
            is_query = getattr(attr, "is_query", None)
            if is_query:
                attr.conditions = partial(attr.conditions, cls)


class Queryable(object, metaclass=QueryableMeta):
    inheritors = []
    model_name = None


class query:
    default_conditions = Q()

    @classmethod
    def all(cls):
        return cls.default_conditions

    @classmethod
    def none(cls):
        # Here we're trying to make a simple impossible condition that won't return any models
        return Q(pk=-1)

    def __init__(self, distinct=False):
        self.distinct = distinct

    def __call__(self, queryset_method):
        def query_decorator(queryset, *args, **kwargs):
            query_name = queryset_method.__name__

            def query_traverse(queryset_cls):
                conditions_method = getattr(queryset_cls, query_name)
                conditions = conditions_method.conditions(*args, **kwargs)
                distinct = conditions_method.distinct

                for inheritor_cls in queryset_cls.inheritors:
                    queryset_conditions, child_distinct = query_traverse(inheritor_cls)
                    if not queryset_conditions:
                        queryset_conditions = query.default_conditions
                    if child_distinct:
                        distinct = True

                    if not isinstance(queryset_conditions, Q):
                        raise ValueError(
                            "Filter '{query_name}' for '{inheritor_class_name}' returned not a Q object.".format(
                                query_name=query_name,
                                inheritor_class_name=inheritor_cls.__name__
                            )
                        )

                    query_model_name = inheritor_cls.model_name.lower()
                    rename_conditions(queryset_conditions, query_model_name)

                    if conditions is None:
                        conditions = query.default_conditions
                    if queryset_conditions != query.default_conditions:
                        inherited_model_cls_not_included = query_model_name + "__isnull"
                        conditions &= Q(**{inherited_model_cls_not_included: True})
                        conditions |= Q(**{inherited_model_cls_not_included: False}) & queryset_conditions
                return conditions, distinct

            query_conditions, distinct = query_traverse(queryset.__class__)
            queryset = queryset.filter(query_conditions)
            if distinct:
                queryset = queryset.distinct()
            return queryset

        query_decorator.conditions = queryset_method
        query_decorator.distinct = self.distinct
        query_decorator.is_query = True
        return query_decorator


def rename_conditions(conditions, model_name):
    for index, child in enumerate(conditions.children):
        if isinstance(child, Node):
            rename_conditions(child, model_name)
        else:
            param_name, param_value = child
            param_key = model_name + "__" + param_name
            conditions.children[index] = param_key, param_value
    return conditions
