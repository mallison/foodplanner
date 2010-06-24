from django.db import models


class Meal(models.Model):
    order = models.PositiveIntegerField()
    name = models.CharField(max_length=20)
    default = models.ForeignKey('Recipe', null=True, blank=True)

    class Meta:
        ordering = ('order',)

    def __unicode__(self):
        return self.name


class MealChoice(models.Model):
    date = models.DateField()
    meal = models.ForeignKey(Meal, related_name="choices")
    recipe = models.ForeignKey('Recipe', related_name="choices")

    class Meta:
        unique_together = ('date', 'meal')


class Recipe(models.Model):
    name = models.CharField(max_length=100)
    preparation_time = models.PositiveIntegerField()
    cooking_time = models.PositiveIntegerField()
    method = models.TextField()
    serves = models.PositiveIntegerField()
    
    def __unicode__(self):
        return self.name

    def get_nutrition(self):
        #FIXME
        import views
        return views._get_total_nutrition([self])


class BasePluralizableModel(models.Model):
    plural_name = models.CharField(max_length=100, blank=True)

    class Meta:
        abstract = True

    def pluralize(self):
        return self.plural_name or self.name + 's'


class Ingredient(BasePluralizableModel):
    name = models.CharField(max_length=100)
    
    def __unicode__(self):
        return self.name


class IngredientMeasure(models.Model):
    recipe = models.ForeignKey(Recipe, related_name="ingredients")
    ingredient = models.ForeignKey(Ingredient, related_name="measures")
    amount = models.DecimalField(max_digits=10, decimal_places=4)
    unit = models.ForeignKey('Unit', null=True, blank=True)


class Unit(BasePluralizableModel):
    name = models.CharField(max_length=30)
    symbol = models.CharField(max_length=10, blank=True)

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.symbol)


class Conversion(models.Model):
    from_unit = models.ForeignKey(Unit, related_name="conversions_from")
    to_unit = models.ForeignKey(Unit, related_name="conversions_to")
    factor = models.DecimalField(decimal_places=2, max_digits=6)
    is_exact = models.BooleanField(default=True)
    
    def __unicode__(self):
        return u'1 %s = %s %s' % (self.from_unit, self.factor, self.to_unit)


class Nutrient(models.Model):
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name


class Nutrition(models.Model):
    nutrient = models.ForeignKey(Nutrient)
    ingredient = models.ForeignKey(Ingredient)
    ingredient_amount = models.DecimalField(decimal_places=2, max_digits=6)
    ingredient_unit = models.ForeignKey(Unit, null=True, related_name="nutrition_ingredients")
    nutrient_amount = models.DecimalField(decimal_places=2, max_digits=6)
    nutrient_unit = models.ForeignKey(Unit, null=True, related_name="nutrition_nutrients")
    
    class Meta:
        unique_together = ('nutrient', 'ingredient')
