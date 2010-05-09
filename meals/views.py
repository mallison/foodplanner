import datetime
import time

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response


# local app imports
import forms
import models


def planner(request, year, month, day):
    date = datetime.date(*map(int, (year, month, day)))
    if request.method == 'POST':
        formset = forms.MealChoiceFormSet(request.POST)
        if formset.is_valid():
            for choice in formset.cleaned_data:
                if choice['recipe']:
                    meal_choice, created = models.MealChoice.objects.get_or_create(
                        date=date,
                        meal=choice['meal'],
                        defaults={'recipe': choice['recipe']})
                    if not created:
                        if meal_choice.recipe != choice['recipe']:
                            meal_choice.recipe = choice['recipe']
                            meal_choice.save()
            return HttpResponseRedirect(reverse('meals-planner',
                                                args=(year, month, day)))
    else:
        initial = []
        for meal in models.Meal.objects.order_by('order'):
            try:
                meal_choice = models.MealChoice.objects.get(
                    date=date,
                    meal=meal)
            except models.MealChoice.DoesNotExist:
                initial.append({'meal': meal.pk})
            else:
                initial.append({'meal': meal.pk,
                                'recipe': meal_choice.recipe.pk})
        formset = forms.MealChoiceFormSet(initial=initial)
    return render_to_response('meals/planner.html',
                              {'formset': formset,
                               'shopping_list': _get_shopping_list(date)})


class Amount(object):
    def __init__(self, ingredient, amount, unit):
        self.ingredient = ingredient
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


def _get_shopping_list(date):
    measures = models.IngredientMeasure.objects.filter(
        recipe__choices__date=date).order_by('ingredient')
    shopping_list = {}
    for measure in measures:
        ingredient = measure.ingredient
        if not shopping_list.has_key(ingredient):
            shopping_list[ingredient] = Amount(ingredient, 0, measure.unit)
        shopping_list[ingredient] += Amount(ingredient,
                                            measure.amount, 
                                            measure.unit)
    print shopping_list
    return shopping_list
