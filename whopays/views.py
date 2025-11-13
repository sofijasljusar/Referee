from django.views.generic import TemplateView
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView
from .forms import SignUpForm, LogInForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse
import json
from .models import UserProfile


class SignUpView(CreateView):
    template_name = "auth.html"
    form_class = SignUpForm
    success_url = reverse_lazy("groups")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Sign Up"
        return context


class LogInView(LoginView):
    template_name = "auth.html"
    authentication_form = LogInForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Log In"
        return context


class GroupsView(LoginRequiredMixin, TemplateView):
    template_name = "groups.html"


class GroupDetailView(TemplateView):
    template_name = "group-detail.html"


class SettingsView(TemplateView):
    template_name = "settings.html"


class UpdateThemeColorView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            color = data.get("theme_color")

            if color and color.startswith("#") and len(color) == 7:
                profile, _ = UserProfile.objects.get_or_create(user=request.user)
                profile.theme_color = color
                profile.save()
                return JsonResponse({"status": "ok"})
        except json.JSONDecodeError:
            pass

        return JsonResponse({"status": "error"}, status=400)
