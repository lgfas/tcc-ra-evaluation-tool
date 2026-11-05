from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok"})


def csrf_failure(request, reason=""):
    return JsonResponse({"detail": "Falha na proteção CSRF. Atualize a página e tente novamente."}, status=403)
