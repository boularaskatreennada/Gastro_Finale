from django.contrib import admin
from .models import Offer
from django.utils.translation import gettext_lazy as _

class StatusFilter(admin.SimpleListFilter):
    title = _('status')
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return [
            ('active', _('Active')),
            ('upcoming', _('Upcoming')),
            ('expired', _('Expired')),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return [o for o in queryset if o.status == 'active']
        if self.value() == 'upcoming':
            return [o for o in queryset if o.status == 'upcoming']
        if self.value() == 'expired':
            return [o for o in queryset if o.status == 'expired']
        return queryset

class OfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'discount', 'status_display', 'uses')
    list_filter = (StatusFilter, 'start_date', 'end_date')
    search_fields = ('title', 'code')
    
    def status_display(self, obj):
        return obj.status
    status_display.short_description = 'Status'

admin.site.register(Offer, OfferAdmin)