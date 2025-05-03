from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Récupère la valeur associée à une clé dans un dictionnaire.
    Si la clé n'existe pas ou si le dictionnaire est None, retourne une liste vide.
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, [])
    return []

@register.filter
def get_ingredient_data(selected_ingredients, ingredient_id):
    """
    Récupère les données d'un ingrédient à partir d'un queryset ou d'un dictionnaire
    de selected_ingredients.
    """
    if selected_ingredients is None:
        return None
    try:
        return selected_ingredients.get(ingredient__id=ingredient_id)
    except (AttributeError, KeyError, TypeError):
        return None
