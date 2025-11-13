from django.views.generic import TemplateView
from django.views.generic import CreateView, DetailView
from django.contrib.auth.views import LoginView
from .forms import SignUpForm, LogInForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse
import json
from .models import UserProfile, PayingQueueGroup


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_groups = PayingQueueGroup.objects.filter(members__user=user).distinct()
        context["user_groups"] = user_groups
        return context


class GroupDetailView(DetailView):
    model = PayingQueueGroup
    template_name = "group-detail.html"
    slug_field = "code"
    slug_url_kwarg = "code"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object
        members = group.members.all()
        current_payer = group.paying_state.current_paying_member
        context.update({
            "group": group,
            "members": members,
            "current_payer": current_payer
        })
        return context


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
