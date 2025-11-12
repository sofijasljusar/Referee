from django.views.generic import TemplateView
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView
from .forms import SignUpForm, LogInForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin


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
