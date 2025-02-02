from django.contrib import admin
from .models import (
    FuneralPackage, PackageItem, PackageItemOption,
    PremiumLine, PremiumLineItem, AdditionalOption
)


class PackageItemOptionInline(admin.TabularInline):
    model = PackageItemOption
    extra = 1


class PackageItemInline(admin.TabularInline):
    model = PackageItem
    extra = 1


@admin.register(FuneralPackage)
class FuneralPackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_price', 'is_active']
    search_fields = ['name']
    list_filter = ['is_active']
    inlines = [PackageItemInline]


@admin.register(PackageItem)
class PackageItemAdmin(admin.ModelAdmin):
    list_display = ['package', 'category', 'default_item', 'is_required']
    list_filter = ['is_required', 'category']
    search_fields = ['package__name', 'category__name']
    inlines = [PackageItemOptionInline]


class PremiumLineItemInline(admin.TabularInline):
    model = PremiumLineItem
    extra = 1


@admin.register(PremiumLine)
class PremiumLineAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'is_active']
    search_fields = ['name']
    list_filter = ['is_active']
    inlines = [PremiumLineItemInline]


@admin.register(AdditionalOption)
class AdditionalOptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'is_active']
    search_fields = ['name']
    list_filter = ['is_active', 'category']
