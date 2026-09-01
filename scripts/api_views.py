from collections import Counter

from django.db.models import Count
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from scripts import models


@extend_schema(
    responses={
        200: {
            "type": "object",
            "additionalProperties": {"type": "integer"},
            "description": "Character statistics with total count and individual character counts",
        }
    },
    summary="Get character statistics",
    description="Returns statistics for all characters including total count",
)
class StatisticsAPI(APIView):
    permission_classes = []

    def get(self, request, format=None):
        counter = Counter()
        # plain_objects, not objects: this endpoint only ever counts, so the default manager's
        # vote/favourite annotations are joins and a GROUP BY for data that is never read.
        if "all" in request.query_params:
            queryset = models.ScriptVersion.plain_objects.all()
        else:
            queryset = models.ScriptVersion.plain_objects.filter(latest=True)

        for param in request.query_params.lists():
            if param[0] == "character":
                for character in param[1]:
                    try:
                        character = models.ClocktowerCharacter.objects.get(character_id=character)
                        queryset = queryset.filter(content__contains=[{"id": character.character_id}])
                    except models.ClocktowerCharacter.DoesNotExist:
                        continue
            elif param[0] == "character_or":
                orig_queryset = queryset.all()
                queryset = models.ScriptVersion.plain_objects.none()
                for character in param[1]:
                    try:
                        character = models.ClocktowerCharacter.objects.get(character_id=character)
                        queryset = queryset | orig_queryset.filter(content__contains=[{"id": character.character_id}])
                    except models.ClocktowerCharacter.DoesNotExist:
                        continue
            elif param[0] == "exclude":
                for character in param[1]:
                    try:
                        character = models.ClocktowerCharacter.objects.get(character_id=character)
                        queryset = queryset.exclude(content__contains=[{"id": character.character_id}])
                    except models.ClocktowerCharacter.DoesNotExist:
                        continue

        # Seed every character to 0 so characters absent from the filtered scripts are still
        # reported, then overlay the counts from a single aggregate query.
        for character in models.ClocktowerCharacter.objects.all():
            counter[character.character_id] = 0

        character_counts = (
            models.ScriptVersionCharacter.objects.filter(script_version__in=queryset, character_id__in=list(counter))
            .values("character_id")
            .annotate(script_count=Count("script_version"))
        )
        for row in character_counts:
            counter[row["character_id"]] = row["script_count"]
        data = {}
        if "total" in request.query_params:
            data["total"] = queryset.count()
        for character in counter.most_common():
            data[character[0]] = character[1]
        return Response(data)


@extend_schema(
    responses={
        200: {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "edition": {"type": "integer"},
                    "character_type": {"type": "string"},
                },
            },
            "description": "List of all clocktower characters",
        }
    },
    summary="Get all clocktower characters",
    description="Returns all official Blood on the Clocktower characters",
)
class CharactersAPI(APIView):
    permission_classes = []

    def get(self, request, format=None):
        data = []
        for character in models.ClocktowerCharacter.objects.all():
            data.append(
                {
                    "id": character.character_id,
                    "name": character.character_name,
                    "edition": character.edition,
                    "character_type": character.character_type,
                }
            )
        return Response(data)
