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
    class Meta(BaseSerializer.Meta):
        model = Schedule
        fields = '__all__'

    def validate_agent_availability(self, schedule_agent, schedule_date, schedule_start_time, schedule_end_time):
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

        # Check for blocked time slots
        blocked_time = BlockTimeAgent.objects.filter(
            agent=schedule_agent,
            start_date__lte=schedule_date,
            end_date__gte=schedule_date,
            is_deleted=False
        ).filter(
            models.Q(
                start_time__lt=schedule_end_time,
                end_time__gt=schedule_start_time
            )
        ).first()

        if blocked_time:
            raise serializers.ValidationError({
                "message": f"O agente possui um bloqueio de horário neste período.",
                "available_time": [{
                    "start": disponibility.start_time.strftime("%H:%M"),
                    "end": blocked_time.start_time.strftime("%H:%M")
                }, {
                    "start": blocked_time.end_time.strftime("%H:%M"),
                    "end": disponibility.end_time.strftime("%H:%M")
                }]
            })

        return disponibility

    def check_schedule_conflicts(self, schedule_agent, schedule_date, schedule_start_time, schedule_end_time, instance=None, disponibility=None):
        existing_schedules = Schedule.objects.filter(
            schedule_agent=schedule_agent,
            schedule_date=schedule_date,
            is_deleted=False
        ).order_by('schedule_start_time')

        if instance:
            existing_schedules = existing_schedules.exclude(pk=instance.pk)

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
        return existing_schedules

    def calculate_travel_times(self, address, all_schedules, position):
        travel_time_previous = 0
        travel_time_next = 0
        total_travel_time = 0
        
        try:
            if position > 0:
                origin = f"{all_schedules[position-1].address.latitude},{all_schedules[position-1].address.longitude}"
                destination = f"{address.latitude},{address.longitude}"
                route = gmaps.directions(origin, destination, mode="driving")
                travel_time_previous = int(route[0]['legs'][0]['duration']['value'] / 60)
                total_travel_time += travel_time_previous
            
            if position < len(all_schedules):
                origin = f"{address.latitude},{address.longitude}"
                destination = f"{all_schedules[position].address.latitude},{all_schedules[position].address.longitude}"
                route = gmaps.directions(origin, destination, mode="driving")
                travel_time_next = int(route[0]['legs'][0]['duration']['value'] / 60)
                total_travel_time += travel_time_next
        except Exception as e:
            print("error calculating travel times: ", e)
            raise serializers.ValidationError({
                "message": "Erro ao calcular rotas. Por favor, tente novamente.",
                "available_time": []
            })
        
        return travel_time_previous, travel_time_next, total_travel_time

    def find_available_slots(self, disponibility, all_schedules, schedule_start_time, schedule_end_time, address):
        available_slots = []
        best_position = None
        min_travel_time = float('inf')

        for i in range(len(all_schedules) + 1):
            travel_time_previous, travel_time_next, total_travel_time = self.calculate_travel_times(address, all_schedules, i)

            if i == 0:
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
                else:
                    available_slots.append({
                        "start": disponibility.start_time.strftime("%H:%M"),
                        "end": disponibility.end_time.strftime("%H:%M")
                    })
                    best_position = 0
            elif i == len(all_schedules):
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
            else:
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

        return best_position

    def create(self, validated_data):
        schedule_agent = validated_data.get("schedule_agent")
        schedule_date = validated_data.get("schedule_date")
        schedule_start_time = validated_data.get("schedule_start_time")
        schedule_end_time = validated_data.get("schedule_end_time")
        address = validated_data.get("address")

        disponibility = self.validate_agent_availability(
            schedule_agent, schedule_date, schedule_start_time, schedule_end_time
        )

        existing_schedules = self.check_schedule_conflicts(
            schedule_agent, schedule_date, schedule_start_time, schedule_end_time, disponibility=disponibility
        )

        self.find_available_slots(
            disponibility, list(existing_schedules), schedule_start_time, schedule_end_time, address
        )

        return super().create(validated_data)

    def update(self, instance, validated_data):
        schedule_agent = validated_data.get("schedule_agent", instance.schedule_agent)
        schedule_date = validated_data.get("schedule_date", instance.schedule_date)
        schedule_start_time = validated_data.get("schedule_start_time", instance.schedule_start_time)
        schedule_end_time = validated_data.get("schedule_end_time", instance.schedule_end_time)
        address = validated_data.get("address", instance.address)

        disponibility = self.validate_agent_availability(
            schedule_agent, schedule_date, schedule_start_time, schedule_end_time
        )

        existing_schedules = self.check_schedule_conflicts(
            schedule_agent, schedule_date, schedule_start_time, schedule_end_time, instance, disponibility=disponibility
        )

        self.find_available_slots(
            disponibility, list(existing_schedules), schedule_start_time, schedule_end_time, address
        )

        return super().update(instance, validated_data)


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