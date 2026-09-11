from django import forms
from unfold.widgets import UnfoldAdminSelectWidget as Select


class AnalyticsFilterForm(forms.Form):
    time_range = forms.ChoiceField(
        choices=[
            ('1d', 'Last 24 Hours'),
            ('3d', 'Last 3 Days'),
            ('7d', 'Last 7 Days'),
            ('30d', 'Last 30 Days'),
            ('90d', 'Last 90 Days'),
            ('180d', 'Last 180 Days'),
            ('365d', 'Last 365 Days'),
        ],
        widget=Select(attrs={'class': 'select select-bordered', 'onchange': 'this.form.submit();'})
    )

    business_profile = forms.ChoiceField(
        choices=[],  # To be populated dynamically in the view
        required=False,
        widget=Select(attrs={'class': 'select select-bordered', 'onchange': 'this.form.submit();'})
    )