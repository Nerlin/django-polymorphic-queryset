from django.db import models
from polymorphic_queryset import Queryable, query


class ProductQuerySet(Queryable, models.QuerySet):
    model_name = "Product"

    @query()
    def get_active(self):
        return models.Q(is_active=True)

    @query()
    def get_default_products(self):
        return query.all()


class Product(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    objects = ProductQuerySet.as_manager()


class ExpirableProductQuerySet(ProductQuerySet):
    model_name = "ExpirableProduct"

    @query()
    def get_active(self):
        return models.Q(is_active=True, is_expired=False)

    @query()
    def get_default_products(self):
        return query.none()


class ExpirableProduct(Product):
    is_expired = models.BooleanField(default=False)
    objects = ExpirableProductQuerySet.as_manager()


class ReportQuerySet(Queryable, models.QuerySet):
    model_name = "Report"

    @query()
    def get_deleted_reports(self):
        return models.Q(is_deleted=True)


class Report(models.Model):
    is_deleted = models.BooleanField(default=False)
    objects = ReportQuerySet.as_manager()


class IntermediateReportQuerySet(ReportQuerySet):
    model_name = "IntermediateReport"


class IntermediateReport(Report):
    objects = IntermediateReportQuerySet.as_manager()


class ArchiveReportQuerySet(IntermediateReportQuerySet):
    model_name = "ArchiveReport"

    @query()
    def get_deleted_reports(self):
        return models.Q(archived=True, is_deleted=False)


class ArchiveReport(IntermediateReport):
    archived = models.BooleanField(default=True)
    objects = ArchiveReportQuerySet.as_manager()
