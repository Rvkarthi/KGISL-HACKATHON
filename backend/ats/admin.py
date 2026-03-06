from django.contrib import admin

from ats.models import ATSResult, CandidateSubmission, JobDescription


class ATSAdmin(admin.ModelAdmin):
    pass


class CandiateSubAdmin(admin.ModelAdmin):
    pass


class JDAdmin(admin.ModelAdmin):
    pass


admin.site.register(ATSResult, ATSAdmin)
admin.site.register(CandidateSubmission, CandiateSubAdmin)
admin.site.register(JobDescription, JDAdmin)
