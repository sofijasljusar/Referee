from django.views.generic import TemplateView, CreateView, DetailView, UpdateView, View
from django.contrib.auth.views import LoginView
from .forms import SignUpForm, LogInForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
import json
from .models import UserProfile, PayingQueueGroup, GroupMember
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import EditUserForm
from .utils import pass_ownership


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


class CreateNewGroupView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        name = request.POST.get("name", "").strip()
        emoji = request.POST.get("emoji", "").strip()

        if not name:
            messages.error(request, "Group name cannot be blank.")
            return redirect("groups")

        group_data = {"owner": request.user, "name": name}
        if emoji:
            group_data["emoji"] = emoji
        PayingQueueGroup.objects.create(**group_data)
        return redirect("groups")


class JoinExistingGroupView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        code = request.POST.get("code", "").strip().upper()
        try:
            group = PayingQueueGroup.objects.get(code=code)
        except PayingQueueGroup.DoesNotExist:
            messages.error(request, "Group not found.")
            return redirect("groups")
        user = request.user
        if not GroupMember.objects.filter(group=group, user=user).exists():
            GroupMember.objects.create(group=group, user=user)
        else:
            messages.error(request, "You are already a member.")
        return redirect("groups")


class LeaveGroupView(LoginRequiredMixin, View):
    def post(self, request, code):
        group = PayingQueueGroup.objects.get(code=code)
        user = request.user
        GroupMember.objects.filter(group=group, user=user).delete()

        if user == group.owner:
            pass_ownership(group)

        return redirect("groups")


class EditUserView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = EditUserForm
    template_name = "edit-user.html"

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Account updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return self.request.path


class DeleteUserView(LoginRequiredMixin, View):
    def post(self, request):
        request.user.delete()
        return redirect("login")
