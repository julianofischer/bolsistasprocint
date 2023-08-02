# myapp/views.py
from rest_framework import generics, permissions
from .models import Report
from .serializers import ReportSerializer


class ReportListView(generics.ListAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Report.objects.filter(user=user)
