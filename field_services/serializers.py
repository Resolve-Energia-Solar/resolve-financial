import googlemaps
from field_services.models import *
from accounts.serializers import BaseSerializer
from rest_framework import serializers
from resolve_erp.settings import GMAPS_API_KEY

gmaps = googlemaps.Client(key=GMAPS_API_KEY)

class RoofTypeSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = RoofType
        fields = '__all__'


class CategorySerializer(BaseSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class DeadlineSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = Deadline
        fields = '__all__'


class ServiceSerializer(BaseSerializer):  
    class Meta(BaseSerializer.Meta):
        model = Service
        fields = '__all__'


class FormsSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = Forms
        fields = '__all__'
        
        
class ScheduleSerializer(BaseSerializer):
    # str = serializers.SerializerMethodField()
    
    class Meta(BaseSerializer.Meta):
        model = Schedule
        fields = '__all__'
    
    def create(self, validated_data):
        schedule_agent = validated_data.get("schedule_agent")
        schedule_date = validated_data.get("schedule_date")
        schedule_start_time = validated_data.get("schedule_start_time")
        schedule_end_time = validated_data.get("schedule_end_time")
        address = validated_data.get("address")

        disponibility = FreeTimeAgent.objects.filter(
            agent=schedule_agent,
            day_of_week=schedule_date.weekday(),
            is_deleted=False
        ).first()

        if not disponibility:
            raise serializers.ValidationError({
                "message": "O agente não possui disponibilidade cadastrada para este dia da semana.",
                "available_time": []
            })

        if schedule_start_time < disponibility.start_time or schedule_end_time > disponibility.end_time:
            raise serializers.ValidationError({
                "message": f"O horário do agendamento deve estar entre {disponibility.start_time} e {disponibility.end_time}",
                "available_time": [{
                    "start": disponibility.start_time.strftime("%H:%M"),
                    "end": disponibility.end_time.strftime("%H:%M")
                }]
            })

        existing_schedules = Schedule.objects.filter(
            schedule_agent=schedule_agent,
            schedule_date=schedule_date,
            is_deleted=False
        ).order_by('schedule_start_time')

        conflicting_schedules = existing_schedules.filter(
            models.Q(
                schedule_start_time__lt=schedule_end_time,
                schedule_end_time__gt=schedule_start_time
            )
        )

        if conflicting_schedules.exists():
            available_slots = []
            current_time = disponibility.start_time
            
            for existing in existing_schedules:
                if current_time < existing.schedule_start_time:
                    available_slots.append({
                        "start": current_time.strftime("%H:%M"),
                        "end": existing.schedule_start_time.strftime("%H:%M")
                    })
                current_time = existing.schedule_end_time
            
            if current_time < disponibility.end_time:
                available_slots.append({
                    "start": current_time.strftime("%H:%M"),
                    "end": disponibility.end_time.strftime("%H:%M")
                })
            
            raise serializers.ValidationError({
                "message": "Já existe um agendamento para este agente no horário selecionado.",
                "available_time": available_slots
            })

        # Check travel time feasibility
        try:
            available_slots = []
            all_schedules = list(existing_schedules)
            has_conflict = False
            travel_time_messages = []
            best_position = None
            min_travel_time = float('inf')

            # Find the best position to insert the new schedule
            for i in range(len(all_schedules) + 1):
                travel_time_previous = 0
                travel_time_next = 0
                total_travel_time = 0
                
                # Calculate travel time from previous schedule
                if i > 0:
                    origin = f"{all_schedules[i-1].address.latitude},{all_schedules[i-1].address.longitude}"
                    destination = f"{address.latitude},{address.longitude}"
                    route = gmaps.directions(origin, destination, mode="driving")
                    travel_time_previous = int(route[0]['legs'][0]['duration']['value'] / 60)
                    total_travel_time += travel_time_previous
                
                # Calculate travel time to next schedule
                if i < len(all_schedules):
                    origin = f"{address.latitude},{address.longitude}"
                    destination = f"{all_schedules[i].address.latitude},{all_schedules[i].address.longitude}"
                    route = gmaps.directions(origin, destination, mode="driving")
                    travel_time_next = int(route[0]['legs'][0]['duration']['value'] / 60)
                    total_travel_time += travel_time_next

                # Check if there's enough time for this position
                if i == 0:  # Before first schedule
                    if all_schedules:
                        first_schedule = all_schedules[0]
                        if first_schedule.schedule_start_time > disponibility.start_time:
                            latest_end = first_schedule.schedule_start_time.replace(
                                hour=(first_schedule.schedule_start_time.hour * 60 + first_schedule.schedule_start_time.minute - travel_time_next) // 60,
                                minute=(first_schedule.schedule_start_time.hour * 60 + first_schedule.schedule_start_time.minute - travel_time_next) % 60
                            )
                            if disponibility.start_time < latest_end:
                                available_slots.append({
                                    "start": disponibility.start_time.strftime("%H:%M"),
                                    "end": latest_end.strftime("%H:%M")
                                })
                                if (schedule_start_time >= disponibility.start_time and schedule_end_time <= latest_end):
                                    if total_travel_time < min_travel_time:
                                        min_travel_time = total_travel_time
                                        best_position = i
                    else:  # No existing schedules
                        available_slots.append({
                            "start": disponibility.start_time.strftime("%H:%M"),
                            "end": disponibility.end_time.strftime("%H:%M")
                        })
                        best_position = 0
                elif i == len(all_schedules):  # After last schedule
                    last_schedule = all_schedules[-1]
                    if last_schedule.schedule_end_time < disponibility.end_time:
                        earliest_start = last_schedule.schedule_end_time.replace(
                            hour=(last_schedule.schedule_end_time.hour * 60 + last_schedule.schedule_end_time.minute + travel_time_previous) // 60,
                            minute=(last_schedule.schedule_end_time.hour * 60 + last_schedule.schedule_end_time.minute + travel_time_previous) % 60
                        )
                        if earliest_start < disponibility.end_time:
                            available_slots.append({
                                "start": earliest_start.strftime("%H:%M"),
                                "end": disponibility.end_time.strftime("%H:%M")
                            })
                            if (schedule_start_time >= earliest_start and schedule_end_time <= disponibility.end_time):
                                if total_travel_time < min_travel_time:
                                    min_travel_time = total_travel_time
                                    best_position = i
                else:  # Between schedules
                    current_schedule = all_schedules[i-1]
                    next_schedule = all_schedules[i]
                    
                    earliest_start = current_schedule.schedule_end_time.replace(
                        hour=(current_schedule.schedule_end_time.hour * 60 + current_schedule.schedule_end_time.minute + travel_time_previous) // 60,
                        minute=(current_schedule.schedule_end_time.hour * 60 + current_schedule.schedule_end_time.minute + travel_time_previous) % 60
                    )
                    
                    latest_end = next_schedule.schedule_start_time.replace(
                        hour=(next_schedule.schedule_start_time.hour * 60 + next_schedule.schedule_start_time.minute - travel_time_next) // 60,
                        minute=(next_schedule.schedule_start_time.hour * 60 + next_schedule.schedule_start_time.minute - travel_time_next) % 60
                    )
                    
                    if earliest_start < latest_end:
                        available_slots.append({
                            "start": earliest_start.strftime("%H:%M"),
                            "end": latest_end.strftime("%H:%M")
                        })
                        if (schedule_start_time >= earliest_start and schedule_end_time <= latest_end):
                            if total_travel_time < min_travel_time:
                                min_travel_time = total_travel_time
                                best_position = i

            if best_position is None:
                if available_slots:
                    raise serializers.ValidationError({
                        "message": "Não há tempo suficiente para viajar entre os agendamentos.",
                        "available_time": available_slots
                    })
                else:
                    raise serializers.ValidationError({
                        "message": "Não há horários disponíveis para este agendamento.",
                        "available_time": []
                    })

        except Exception as e:
            if isinstance(e, serializers.ValidationError):
                raise e
            print("error: ", e)
            raise serializers.ValidationError({
                "message": "Erro ao calcular rotas. Por favor, tente novamente.",
                "available_time": []
            })

        schedule = super().create(validated_data)
        return schedule



    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     requested_fields = self.context.get('request').query_params.get('fields')
    #     if requested_fields:
    #         requested_fields = requested_fields.split(',')
    #         if 'str' not in requested_fields:
    #             self.fields.pop('str', None)
    #     else:
    #         self.fields.pop('str', None)

    # def get_str(self, obj):
    #     return str(obj)
    

class AnswerSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = Answer
        fields = '__all__'


class BlockTimeAgentSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = BlockTimeAgent
        fields = '__all__'

class FreeTimeAgentSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = FreeTimeAgent
        fields = '__all__'

class FormFileSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = FormFile
        fields = '__all__'

class ServiceOpinionSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = ServiceOpinion
        fields = '__all__'
class RouteSerializer(BaseSerializer):
    class Meta:
        model = Route
        fields = '__all__'