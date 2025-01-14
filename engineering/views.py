import csv
import openpyxl
from api.views import BaseModelViewSet
from logistics.serializers import ProjectMaterialsSerializer
from .models import *
from .serializers import *
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class SupplyAdequanceViewSet(BaseModelViewSet):
    queryset = SupplyAdequance.objects.all()
    serializer_class = SupplyAdequanceSerializer


class ResquestTypeViewSet(BaseModelViewSet):
    queryset = ResquestType.objects.all()
    serializer_class = ResquestTypeSerializer
    
    
class SituationEnergyCompanyViewSet(BaseModelViewSet):
    queryset = SituationEnergyCompany.objects.all()
    serializer_class = SituationEnergyCompanySerializer


class EnergyCompanyViewSet(BaseModelViewSet):
    queryset = EnergyCompany.objects.all()
    serializer_class = EnergyCompanySerializer


class RequestsEnergyCompanyViewSet(BaseModelViewSet):
    queryset = RequestsEnergyCompany.objects.all()
    serializer_class = RequestsEnergyCompanySerializer
    

class UnitsViewSet(BaseModelViewSet):
    queryset = Units.objects.all()
    serializer_class = UnitsSerializer


class ProjectMaterialsCSVUploadAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [AllowAny]

    def post(self, request):
        file = request.FILES.get('file')
        project_id = request.data.get('project_id')

        if not project_id:
            return Response({"error": "Project ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not file:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Process the CSV file
        try:
            decoded_file = file.read().decode('utf-8')
            csv_reader = csv.reader(decoded_file.splitlines(), delimiter=';')

            # Skip the header row
            header = next(csv_reader)
            expected_headers = ['material_class', 'id_project', 'id_material', 'amount']
            if header != expected_headers:
                return Response(
                    {"error": f"Invalid headers. Expected: {expected_headers}, Got: {header}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Iterate through rows and save data
            for row in csv_reader:
                material_class, id_project, id_material, amount = row

                # Prepare the data for serialization
                data = {
                    "material_id": id_material,
                    "amount": amount,
                    "project_id": project_id
                }

                # Validate and save using the serializer
                serializer = ProjectMaterialsSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    return Response(
                        {"error": f"Error in row: {row}", "details": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            return Response({"message": "File processed successfully."}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
