from django.test import TransactionTestCase
from polymorphic_queryset.tests.models import (
    Product, ExpirableProduct, Report, IntermediateReport, ArchiveReport,
    Base, Intermediate, Derived,
)


class QueryTestCase(TransactionTestCase):
    def test_polymorphic_query(self):
        active_product = Product.objects.create(name="Test Product", is_active=True)
        non_active_product = Product.objects.create(name="Test Non-active Product", is_active=False)

        active_expirable_product = ExpirableProduct.objects.create(name="Test Expirable Product", is_active=True)
        active_expired_product = ExpirableProduct.objects.create(name="Test Expired Product", is_active=False, is_expired=True)
        non_active_expirable_product = ExpirableProduct.objects.create(name="Test Non-active Expirable Product", is_active=False)
        non_active_expired_product = ExpirableProduct.objects.create(name="Test Non-active Expired Product", is_active=False, is_expired=True)

        products = Product.objects.get_active().values_list("id", flat=True)
        self.assertListEqual(list(products), [
            active_product.id,
            active_expirable_product.id
        ])

    def test_intermediate_query_not_overriden(self):
        report = Report.objects.create()
        deleted_report = Report.objects.create(is_deleted=True)

        intermediate_report = IntermediateReport.objects.create()
        intermediate_deleted_report = IntermediateReport.objects.create(is_deleted=True)

        archived_report = ArchiveReport.objects.create(archived=True, is_deleted=False)
        archived_deleted_report = ArchiveReport.objects.create(archived=True, is_deleted=True)
        non_archived_report = ArchiveReport.objects.create(archived=False)
        non_archived_deleted_report = ArchiveReport.objects.create(archived=False, is_deleted=True)

        products = Report.objects.get_deleted_reports().values_list("id", flat=True)
        self.assertListEqual(list(products), [
            deleted_report.id,
            intermediate_deleted_report.id,
            archived_report.id
        ])

    def test_empty_results(self):
        product = Product.objects.create()
        expirable_product = ExpirableProduct.objects.create()

        products = Product.objects.get_default_products().values_list("id", flat=True)
        self.assertListEqual(list(products), [
            product.id
        ])

    def test_intermediate_queryset_not_implemented(self):
        base_model = Base.objects.create(name="Test Base")
        intermediate_model = Intermediate.objects.create(name="Test Intermediate")
        skip_intermediate_model = Derived.objects.create(
            name="Skip Intermediate",
            description="Test Description"
        )

        models = Base.objects.wildcard_search("test").values_list("id", flat=True)
        self.assertListEqual(list(models), [
            base_model.id,
            intermediate_model.id,
            skip_intermediate_model.id
        ])
