from django import forms

import models


class MealChoiceForm(forms.Form):
    meal = forms.ModelChoiceField(
        models.Meal.objects, 
        #widget=forms.Select(attrs={'disabled': 'disabled'})
        )
    recipe = forms.ModelChoiceField(models.Recipe.objects, required=False)


MealChoiceFormSet = forms.formsets.formset_factory(MealChoiceForm, extra=0)
