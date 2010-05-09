from django.contrib import admin

import models


class IngredientMeasureInline(admin.TabularInline):
    model = models.IngredientMeasure
    extra = 10


class ConversionInline(admin.TabularInline):
    model = models.Conversion
    fk_name = 'from_unit'


admin.site.register(models.Meal,
                    list_display=('name', 'order', 'default'),
                    list_editable=('order',))
admin.site.register(models.MealChoice,
                    list_display=('meal', 'date', 'recipe'))
admin.site.register(models.Recipe,
                    inlines=(IngredientMeasureInline,),
                    list_display=('name', 'serves'),
                    list_editable=('serves',))
admin.site.register(models.Ingredient)
admin.site.register(models.Conversion,
                    list_display=('from_unit', 'factor', 'to_unit', 'is_exact'))
admin.site.register(models.Unit,
                    inlines=(ConversionInline,))
