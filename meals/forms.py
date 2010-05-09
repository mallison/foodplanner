from django import forms

import models


class MealChoiceForm(forms.Form):
    recipe = forms.ModelChoiceField(models.Recipe.objects, 
                                    required=False,
                                    label='')


MealChoiceFormSet = forms.formsets.formset_factory(MealChoiceForm, extra=0)
