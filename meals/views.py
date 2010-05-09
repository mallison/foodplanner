import datetime
import time

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
        for days in range(days_ahead):
            for meal in meals:
                try:
                    meal_choice = models.MealChoice.objects.get(
                        date=date + datetime.timedelta(days),
                        meal=meal)
                except models.MealChoice.DoesNotExist:
                    initial.append({'meal': meal.pk,
                                    'recipe': meal.default and meal.default.pk})
                else:
                    initial.append({'meal': meal.pk,
                                    'recipe': meal_choice.recipe.pk})
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
         'weekdays': iter(weekdays),
         'grouped_forms': grouped_forms,
         'shopping_list': _get_shopping_list(
                date, 
                date + datetime.timedelta(days_ahead))})


class Amount(object):
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
