# ERP Resolve

ERP da REsolve.


### Método `form_invalid` sobreescrito:
```python
def form_invalid(self, form):
    """If the form is invalid, render the invalid form."""
    for field, errors in form.errors.items():
        for error in errors:
            messages.error(self.request, f"{field}: {error}")
    return self.render_to_response(self.get_context_data(form=form))
```