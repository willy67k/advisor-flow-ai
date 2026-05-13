from django.urls import path

from app.approvals.views import ApprovalApproveView, ApprovalPendingListView, ApprovalRejectView

urlpatterns = [
    path("approvals/pending", ApprovalPendingListView.as_view()),
    path("approvals/<int:pk>/approve", ApprovalApproveView.as_view()),
    path("approvals/<int:pk>/reject", ApprovalRejectView.as_view()),
]
