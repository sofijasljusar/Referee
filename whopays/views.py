from django.views.generic import TemplateView


class SignupView(TemplateView):
    template_name = "signup.html"


class GroupsView(TemplateView):
    template_name = "groups.html"


class GroupDetailView(TemplateView):
    template_name = "group-detail.html"
