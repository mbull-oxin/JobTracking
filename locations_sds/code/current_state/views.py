from django.shortcuts import render
from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
import datetime
import time
from .models import JobState, Location
from .serializers import JobStateSerializer, LocationSerializer


class GetState(viewsets.ReadOnlyModelViewSet):
    serializer_class = JobStateSerializer

    def get_queryset(self):
        # Delete old entries in complete
        # This is not ideal - it should be replaced by a cron job for long running systems
        # but should be ok for small deployments
        if settings.DELETE_ON_COMPLETE:
            __dt = -1 * (time.timezone if (time.localtime().tm_isdst == 0) else time.altzone)
            tz = datetime.timezone(datetime.timedelta(seconds=__dt))

            today = datetime.datetime.combine(
                datetime.datetime.now(tz=tz), datetime.datetime.min.time(),tzinfo=tz
            )
            threshold = today - settings.DELETE_THRESHOLD + datetime.timedelta(days=1)
            delete_candidates = JobState.objects.filter(
                location__name__exact="Complete"
            ).filter(timestamp__lt=threshold)
            print(
                f"Today: {today.isoformat()}, threshold: {threshold.isoformat()}, settings: {settings.DELETE_THRESHOLD}"
            )
            candidate_entries = [
                {"id": entry.id, "timestamp": entry.timestamp}
                for entry in delete_candidates
            ]
            print(f"Candidates: {delete_candidates}")
            print(f"Candidate Details: {candidate_entries}")
            delete_candidates.delete()

        return JobState.objects.all()


class Locations(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

    def get_permissions(self):
        return [IsAuthenticatedOrReadOnly()]


class StateAtLocation(viewsets.ReadOnlyModelViewSet):
    serializer_class = JobStateSerializer

    def get_queryset(self):
        if '_' in self.kwargs['location']:
            self.kwargs['location']=self.kwargs['location'].replace('_',' ')
        return JobState.objects.filter(location__name=self.kwargs["location"])
