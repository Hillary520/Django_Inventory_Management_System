from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.views import View


class CustomLoginView(LoginView):
    """
    CustomLoginView is a subclass of LoginView that customizes the login template
    for user authentication.

    This class specifies a custom template to be used for rendering the login
    view, allowing developers to manage and style the login page according to
    application needs. This is particularly useful when integrating specific
    design or layout requirements into the application’s authentication system.

    :ivar template_name: The path to the template used for rendering the login page.
    :type template_name: str
    """
    template_name = 'accounts/login.html'


class CustomLogoutView(View):
    """
    Handles user logout functionality.

    This view handles the process of logging out a user. It uses Django's
    `logout` function to terminate the user's session and then redirects
    them to the login page. This class-based view provides a structure
    for handling logout functionality in a clean and reusable manner.

    :ivar template_name: The name of the template associated with this
        view, if applicable.
    :type template_name: str
    """
    def get(self, request):
        logout(request)
        return redirect('login')

