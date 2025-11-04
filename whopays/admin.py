from django.contrib import admin
from .models import PayingQueueGroup, GroupMember, PayingState

class GroupMemberInline(admin.TabularInline):
    model = GroupMember
    extra = 0


class PayingStateInline(admin.TabularInline):
    model = PayingState
    can_delete = False
    extra = 0


@admin.register(PayingQueueGroup)
class PayingQueueGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "owner")
    readonly_fields = ("code",)
    search_fields = ("name", "code", "owner__username")
    inlines = [GroupMemberInline]

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ("user", "group")


@admin.register(PayingState)
class PayingStateAdmin(admin.ModelAdmin):
    list_display = ("group", "current_paying_member")


