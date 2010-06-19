import collections
import datetime
import time
from decimal import Decimal

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render_to_response


# local app imports
import forms
import models
import utils


def planner(request, year, month, day, scope):
    date = datetime.date(*map(int, (year, month, day)))
    if scope == 'week': 
        days_ahead = 7
    elif scope == 'month':
        # TODO: do a real month!
        days_ahead = 31
    else:
        raise Http404
    weekdays = [(date + datetime.timedelta(d)).strftime('%a') 
                for d in range(days_ahead)]
    meals = models.Meal.objects.order_by('order')
    if request.method == 'POST':
        formset = forms.MealChoiceFormSet(request.POST)
        if formset.is_valid():
            weekday = date
            for meals_for_day in utils.itergroup(formset.cleaned_data, 
                                                 meals.count()):
                for meal, choice in zip(meals, meals_for_day):
                    try:
                        meal_choice = models.MealChoice.objects.get(
                            date=weekday,
                            meal=meal)
                    except models.MealChoice.DoesNotExist:
                        if choice['recipe']:
                            meal_choice = models.MealChoice.objects.create(
                                date=weekday,
                                meal=meal,
                                recipe=choice['recipe'])
                    else:
                        if not choice['recipe']:
                            meal_choice.delete()
                        else:
                            if meal_choice.recipe != choice['recipe']:
                                meal_choice.recipe = choice['recipe']
                                meal_choice.save()
                weekday += datetime.timedelta(1)
            if not request.is_ajax():
                return HttpResponseRedirect(
                    reverse('meals-planner', args=(year, month, day, scope)))
    if request.method == 'GET' or request.is_ajax():
        initial = []
        meals = models.Meal.objects.order_by('order')
        daily_nutrition = []
        for days in range(days_ahead):
            days_recipes = []
            for meal in meals:
                try:
                    meal_choice = models.MealChoice.objects.get(
                        date=date + datetime.timedelta(days),
                        meal=meal)
                except models.MealChoice.DoesNotExist:
                    initial.append({'meal': meal.pk,
                                    'recipe': meal.default and meal.default.pk})
                else:
                    days_recipes.append(meal_choice.recipe)
                    initial.append({'meal': meal.pk,
                                    'recipe': meal_choice.recipe.pk})
            daily_nutrition.append(_get_total_nutrition(days_recipes))
        formset = forms.MealChoiceFormSet(initial=initial)
        grouped_forms = utils.itergroup(formset.forms, meals.count())
    if request.is_ajax():
        template = 'planner_inner'
    else:
        template = 'planner'
    return render_to_response(
        'meals/%s.html' % template,
        {'formset': formset,
         'meals': meals,
         'daily_nutrition': iter(daily_nutrition),
         'weekdays': iter(weekdays),
         'grouped_forms': grouped_forms,
         'shopping_list': _get_shopping_list(
                date, 
                date + datetime.timedelta(days_ahead))})


class Amount(object):
    # TODO: must be easier to store all amounts in the database in the same
    # unit, and just convert for presentation -- then no need for conversions
    # between units when doing calculations
    def __init__(self, ingredient, amount, unit):
        self.ingredient = ingredient
        #TODO: use decimals for amounts
        self.amount = amount
        self.unit = unit
    
    def __add__(self, other_amount):
        if self.unit == other_amount.unit:
            new_amount = self.__class__(self.ingredient,
                                        self.amount + other_amount.amount, 
                                        self.unit)
        else:
            try:
                conversion = models.Conversion.objects.get(
                    from_unit=self.unit,
                    to_unit=other_amount.unit)
            except models.Conversion.DoesNotExist:
                # TODO: check for conversion defined the other way round?
                raise TypeError("You can't add %s to %s" % (self.unit,
                                                            other_amount.unit))
            else:
                new_amount = self.__class__(
                    self.ingredient,
                    self.amount * conversion.factor + other_amount.amount,
                    conversion.to_unit)
        return new_amount

    def __div__(self, other_amount):
        # TODO: not sure I want to use __div__ as this function doesn't return
        # an Amount but a ratio of amounts ...
        other_amount = self._convert_amount(other_amount)
        # TODO: use decimals
        return self.amount / float(other_amount.amount)

    def divide(self, parts):
        return self.__class__(self.ingredient, 
                              self.amount / float(parts),
                              self.unit)

    def pluralize_ingredient(self):
        if not self.unit and self.amount > 1:
            return self.ingredient.pluralize()
        return self.ingredient.name

    def pluralize_unit(self):
        if not self.unit:
            return ''
        if self.amount > 1:
            return self.unit.pluralize()
        return self.unit.name
    
    def _convert_amount(self, other_amount):
        """Converts other amount to the same units as self if possible"""
        # TODO: check the substances are the same!
        if self.unit == other_amount.unit:
            return other_amount
        else:
            conversion = None
            try:
                conversion = models.Conversion.objects.get(
                    from_unit=other_amount.unit,
                    to_unit=self.unit)
            except models.Conversion.DoesNotExist:
                try:
                    conversion = models.Conversion.objects.get(
                        to_unit=other_amount.unit,
                        from_unit=self.unit)
                except:
                    raise TypeError("Can't convert %s to %s" % 
                                    (self.unit,
                                     other_amount.unit))
                else:
                    factor = 1 / conversion.factor
            else:
                factor = conversion.factor
            if conversion:
                new_amount = self.__class__(
                    self.ingredient,
                    other_amount.amount * factor,
                    self.unit)
        return new_amount


def _get_shopping_list(start_date, end_date):
    measures = models.IngredientMeasure.objects.filter(
        recipe__choices__date__gte=start_date,
        recipe__choices__date__lte=end_date).order_by('ingredient')
    shopping_list = {}
    for measure in measures:
        ingredient = measure.ingredient
        if not shopping_list.has_key(ingredient):
            shopping_list[ingredient] = Amount(ingredient, 0, measure.unit)
        shopping_list[ingredient] += Amount(
            ingredient,
            measure.amount, 
            measure.unit).divide(measure.recipe.serves)
    return shopping_list


def _get_total_nutrition(recipe_list):
    nutrition_totals = {}
    for recipe in recipe_list:
        for ingredient in recipe.ingredients.all():
            for nutrient in models.Nutrient.objects.all():
                try:
                    nutrition = ingredient.ingredient.nutrition_set.get(
                        nutrient=nutrient)
                except models.Nutrition.DoesNotExist:
                    pass
                else:
                    ratio = (Amount(ingredient.ingredient,
                                    ingredient.amount,
                                    ingredient.unit) / 
                             Amount(nutrition.ingredient,
                                    nutrition.ingredient_amount,
                                    nutrition.ingredient_unit))
                    nutrient_amount = Amount(
                        nutrition.nutrient,
                        nutrition.nutrient_amount * Decimal(str(ratio)),
                        nutrition.nutrient_unit)
                    if not nutrition_totals.has_key(nutrition.nutrient):
                        nutrition_totals[nutrition.nutrient] = Amount(
                            nutrition.nutrient,
                            0,
                            nutrition.nutrient_unit)
                    nutrition_totals[nutrition.nutrient] += nutrient_amount
    return nutrition_totals
