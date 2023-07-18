from django.shortcuts import get_object_or_404
from rest_framework.views import APIView, Response, Request, status
from groups.models import Group
from traits.models import Trait
from .serializers import PetSerializer
from .models import Pet
from rest_framework.pagination import PageNumberPagination


class PetsView(APIView, PageNumberPagination):
    def post(self, request: Request) -> Response:
        serializer = PetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # Separa os dados recebidos
        group_data = serializer.validated_data.pop("group")
        traits = serializer.validated_data.pop("traits")
        # Verifica se o grupo já existe
        group, _ = Group.objects.get_or_create(**group_data)
        # Cria o pet associado ao grupo
        pet = Pet.objects.create(group=group, **serializer.validated_data)
        # Crio traits
        for traits_dict in traits:
            trait_name = traits_dict["name"]
            trait_name_lower = trait_name.lower()

            try:
                trait_obj = Trait.objects.get(name__iexact=trait_name_lower)
            except Trait.DoesNotExist:
                trait_obj = Trait.objects.create(name=trait_name_lower)

            pet.traits.add(trait_obj)

        serializer = PetSerializer(instance=pet)

        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request: Request) -> Response:
        trait_query = request.query_params.get("trait")

        if trait_query:
            pets = Pet.objects.filter(traits__name=trait_query)
        else:
            pets = Pet.objects.all()

        result_page = self.paginate_queryset(pets, request)

        serializer = PetSerializer(instance=result_page, many=True)

        return self.get_paginated_response(serializer.data)


class PetsIdView(APIView):
    def get(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)
        serializer = PetSerializer(instance=pet)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)
        pet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request: Request, pet_id: int) -> Response:
        # Confere se dados recebidos estão corretos
        serializer = PetSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Atualizar o grupo do pet, se fornecido
        pet = get_object_or_404(Pet, id=pet_id)
        group_data = serializer.validated_data.get("group")
        if group_data:
            group_scientific_name = group_data.get("scientific_name")
            group, _ = Group.objects.get_or_create(
                scientific_name=group_scientific_name
            )
            pet.group = group

        # Atualizar as traits do pet, se fornecidas
        traits_data = serializer.validated_data.get("traits")
        if traits_data:
            traits = []
            for trait_data in traits_data:
                trait_name = trait_data.get("name")
                trait_name_lower = trait_name.lower()
                trait_obj = Trait.objects.filter(name__iexact=trait_name_lower).first()
                if not trait_obj:
                    trait_obj = Trait.objects.create(name=trait_name_lower)
                traits.append(trait_obj)
            pet.traits.set(traits)

        # Atualizar outros campos fornecidos
        for key, value in serializer.validated_data.items():
            if key not in ["group", "traits"]:
                setattr(pet, key, value)
        pet.save()
        serializer = PetSerializer(instance=pet)
        return Response(serializer.data, status=status.HTTP_200_OK)
