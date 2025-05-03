from django.shortcuts import redirect
from django.urls import reverse

class RoleBasedAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # URLs à exclure du middleware (login, admin, etc.)
        excluded_paths = [
            '/admin/',
            '/restaurant/login/',
            '/restaurant/client_register/',
        ]
        
        if any(request.path.startswith(path) for path in excluded_paths):
            return None  # Pas de redirection pour ces URLs

        # Redirige vers login si l'utilisateur n'est pas authentifié
        if not request.user.is_authenticated:
            return redirect('login')  # Utilise le nom de l'URL (pas le chemin)

        # Vérification des rôles (uniquement si l'utilisateur est connecté)
        user_type = request.user.user_type
        
        if '/pdg-dashboard/' in request.path and user_type != 'PDG':
            return redirect('login')
        elif '/manager-dashboard/' in request.path and user_type != 'MANAGER':
            return redirect('login')

        return None  # Aucune redirection