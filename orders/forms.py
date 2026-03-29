from django import forms
from django.contrib.admin.widgets import AdminDateWidget


class ReportForm(forms.Form):
    REPORT_TYPES = [
        ("sales_by_month", "Продажи по месяцам"),
        ("average_check", "Средний чек"),
        ("top_products", "Популярные товары"),
    ]

    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        label="Тип отчёта",
        widget=forms.Select(attrs={"class": "vSelectField"}),
    )
    date_from = forms.DateField(
        label="От какой даты",
        widget=AdminDateWidget(attrs={"class": "vDateField"}),
    )
    date_to = forms.DateField(
        label="По какую дату",
        widget=AdminDateWidget(attrs={"class": "vDateField"}),
    )
    format = forms.CharField(
        label="Формат",
        widget=forms.HiddenInput(),
        initial="xlsx",
    )