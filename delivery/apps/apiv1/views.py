# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from ..orders.models import Task, AvailableUserTypes, AvailableTaskStates


class TaskStateUpdateView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        payload = request.POST.dict()
        user = request.user
        uid = payload.get('task')
        state = payload.get('state')
        try:
            task = Task.objects.get(uid=uid)

        except Task.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        user_type = user.user_type

        if user_type == AvailableUserTypes.store_manager:
            if state == AvailableTaskStates.cancelled:
                task.state = state
                task.assigned_to = None
                task.save()
                return Response(status=status.HTTP_200_OK)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if user_type == AvailableUserTypes.delivery_person:
            if state in [AvailableTaskStates.accepted, AvailableTaskStates.completed]:
                task.state = state
                task.assigned_to = user
                task.save()
                return Response(status=status.HTTP_200_OK)
            if state == AvailableTaskStates.declined:
                task.state = state
                task.assigned_to = None
                task.save()
                return Response(status=status.HTTP_200_OK)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)
