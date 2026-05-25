from django.views.generic import TemplateView, CreateView, DetailView, UpdateView, View, ListView
from django.contrib.auth.views import LoginView
from .forms import SignUpForm, LogInForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import PayingQueueGroup, GroupMember
from .services import GroupService
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import EditUserForm, CustomSetPasswordForm, EditGroupForm
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, \
    PasswordResetCompleteView
from .forms import CustomPasswordResetForm
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from .exceptions import GroupCodeGenerationError, GroupClosed
from django.shortcuts import get_object_or_404
from .notifiers import GroupRealtimeNotifier


class SignUpView(CreateView):
    template_name = "auth/auth.html"
    form_class = SignUpForm
    success_url = reverse_lazy("groups")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Sign Up"
        return context


class LogInView(LoginView):
    template_name = "auth/auth.html"
    authentication_form = LogInForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Log In"
        return context


class CustomPasswordResetView(PasswordResetView):
    template_name = "auth/auth.html"
    form_class = CustomPasswordResetForm
    email_template_name = "registration/password-reset-email.html"
    html_email_template_name = "registration/password-reset-email-html.html"
    subject_template_name = "registration/password-reset-subject.txt"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Reset Password"
        context["back_url"] = reverse("login")
        return context


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "auth/simple-message.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = reverse("login")
        context["message"] = "Check your email for password reset instructions."
        return context


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = CustomSetPasswordForm

    def get_template_names(self):
        if self.validlink:
            return ["auth/auth.html"]
        return ["auth/simple-message.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = reverse("login")
        if self.validlink:
            context["title"] = "Set New Password"
        else:
            context["message"] = "This link has already been used or expired."
        return context


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "auth/simple-message.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = reverse("login")
        context["message"] = "Your password has been successfully changed. You can now return to the login page."
        return context


class GroupsView(LoginRequiredMixin, ListView):
    model = PayingQueueGroup
    template_name = "groups.html"
    context_object_name = "user_groups"

    def get_queryset(self):
        return PayingQueueGroup.objects.filter(members__user=self.request.user)


class GroupDetailView(LoginRequiredMixin, DetailView):
    model = PayingQueueGroup
    template_name = "group-detail.html"
    slug_field = "code"
    slug_url_kwarg = "code"

    def get_queryset(self):
        return (
            PayingQueueGroup.objects
            .filter(members__user=self.request.user)
            .select_related(
                "owner",
                "paying_state",
                "paying_state__current_paying_member",
            )
            .prefetch_related("members__user")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object

        context.update({
            "group": group,
            "members": group.members.all(),
            "current_payer_id": group.paying_state.current_paying_member.id,
            "current_user_member_id": group.members.get(user=self.request.user).id,
            "owner_member_id": group.members.get(user=group.owner).id,
        })
        return context


class CreateNewGroupView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        name = request.POST.get("name", "").strip()
        emoji = request.POST.get("emoji", "").strip()

        if not name:
            messages.error(request, "Group name cannot be blank.")
            return redirect("groups")
        try:
            GroupService.create_group(
                owner=request.user,
                name=name,
                emoji=emoji or None,
            )
        except GroupCodeGenerationError:
            messages.error(
                request,
                "Could not create group right now. Please try again."
            )

        return redirect("groups")


class JoinExistingGroupView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        code = request.POST.get("code", "").strip().upper()
        try:
            group = PayingQueueGroup.objects.get(code=code)
        except PayingQueueGroup.DoesNotExist:
            messages.error(request, "Group not found.")
            return redirect("groups")

        try:
            result = GroupService.join_group(group=group, user=request.user)
        except GroupClosed:
            messages.error(request, "Group was closed.")
            return redirect("groups")

        created = result.created
        new_member = result.member

        if not created:
            messages.error(request, "You are already a member.")
        else:
            GroupRealtimeNotifier.user_joined(
                code=code,
                new_member=new_member,
            )
        return redirect("groups")


class LeaveGroupView(LoginRequiredMixin, View):
    def post(self, request, code):
        group = get_object_or_404(
            PayingQueueGroup,
            code=code,
            members__user=self.request.user,
        )
        member = GroupMember.objects.get(group=group, user=request.user)
        member_id = member.id

        result = GroupService.leave_group(
            group=group,
            member=member,
        )

        if not result.group_deleted:
            GroupRealtimeNotifier.member_left(
                code=code,
                member_id=member_id,
                result=result,
            )

        return redirect("groups")


class EditGroupView(LoginRequiredMixin, UpdateView):
    model = PayingQueueGroup
    form_class = EditGroupForm
    template_name = "edit-group.html"
    slug_field = "code"
    slug_url_kwarg = "code"

    def get_queryset(self):
        return PayingQueueGroup.objects.filter(owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["group"] = self.object
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Group updated successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = reverse("group-detail", kwargs={'code': self.object.code})
        context["group"] = self.object
        return context

    def get_success_url(self):
        return reverse("group-detail", kwargs={"code": self.object.code})


class DeleteGroupView(LoginRequiredMixin, View):
    def post(self, request, code):
        group = get_object_or_404(
            PayingQueueGroup,
            code=code,
            members__user=request.user,
        )

        if group.owner != request.user:
            raise PermissionDenied

        GroupService.close_group(group)

        return redirect("groups")


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = "settings.html"


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
        user = request.user
        members = list(GroupMember.objects.select_related("group").filter(user=user))

        for member in members:
            GroupService.leave_group(
                group=member.group,
                member=member,
            )

        user.delete()

        return redirect("login")
