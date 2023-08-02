# myapp/serializers.py
from rest_framework import serializers
from .models import Report, ReportEntry, ReportSubmission


class ReportEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportEntry
        fields = "__all__"


class ReportSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportSubmission
        fields = "__all__"


class ReportSerializer(serializers.ModelSerializer):
    entries = ReportEntrySerializer(many=True, read_only=True)
    submissions = ReportSubmissionSerializer(many=True, read_only=True)

    class Meta:
        model = Report
        fields = "__all__"
