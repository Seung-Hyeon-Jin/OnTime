import 'route_model.dart';

class RoutePlanModel {
  final String routePlanId;
  final String routineId;
  final String provider;
  final int totalDurationMinutes;
  final int transferCount;
  final int? fare;
  final RouteResponseModel route;

  RoutePlanModel({
    required this.routePlanId,
    required this.routineId,
    required this.provider,
    required this.totalDurationMinutes,
    required this.transferCount,
    this.fare,
    required this.route,
  });

  factory RoutePlanModel.fromJson(Map<String, dynamic> json) {
    return RoutePlanModel(
      routePlanId: json['route_plan_id'] ?? '',
      routineId: json['routine_id'] ?? '',
      provider: json['provider'] ?? '',
      totalDurationMinutes: json['total_duration_minutes'] ?? 0,
      transferCount: json['transfer_count'] ?? 0,
      fare: json['fare'],
      route: RouteResponseModel.fromJson(json['route'] ?? {}),
    );
  }
}

class RoutineModel {
  final String routineId;
  final String userId;
  final String name;
  final String departureStop;
  final String arrivalStop;
  final List<String> scheduledDays;
  final String departureTime; // "HH:MM:SS"
  final int notifyMinsBefore;
  final bool enabled;
  final bool excludeHolidays;
  final LocationModel? origin;
  final LocationModel? destination;
  final RoutePlanModel? routePlan;

  RoutineModel({
    required this.routineId,
    required this.userId,
    required this.name,
    required this.departureStop,
    required this.arrivalStop,
    required this.scheduledDays,
    required this.departureTime,
    required this.notifyMinsBefore,
    this.enabled = true,
    this.excludeHolidays = false,
    this.origin,
    this.destination,
    this.routePlan,
  });

  factory RoutineModel.fromJson(Map<String, dynamic> json) {
    return RoutineModel(
      routineId: json['routine_id'] ?? '',
      userId: json['user_id'] ?? '',
      name: json['name'] ?? '',
      departureStop: json['departure_stop'] ?? '',
      arrivalStop: json['arrival_stop'] ?? '',
      scheduledDays: (json['scheduled_days'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      departureTime: json['departure_time'] ?? '08:00:00',
      notifyMinsBefore: json['notify_mins_before'] ?? 10,
      enabled: json['enabled'] ?? true,
      excludeHolidays: json['exclude_holidays'] ?? false,
      origin: json['origin'] != null
          ? LocationModel.fromJson(json['origin'])
          : null,
      destination: json['destination'] != null
          ? LocationModel.fromJson(json['destination'])
          : null,
      routePlan: json['route_plan'] != null
          ? RoutePlanModel.fromJson(json['route_plan'])
          : null,
    );
  }

  String get formattedDepartureTime {
    final parts = departureTime.split(':');
    if (parts.length >= 2) {
      return '${parts[0]}:${parts[1]}';
    }
    return departureTime;
  }

  String get daysSummary {
    const dayMap = {
      'MON': '월',
      'TUE': '화',
      'WED': '수',
      'THU': '목',
      'FRI': '금',
      'SAT': '토',
      'SUN': '일',
    };
    if (scheduledDays.length == 5 &&
        scheduledDays.contains('MON') &&
        scheduledDays.contains('FRI')) {
      return '주중 (월~금)';
    }
    if (scheduledDays.length == 7) {
      return '매일';
    }
    return scheduledDays.map((d) => dayMap[d] ?? d).join(', ');
  }

  Map<String, dynamic> toJson() {
    return {
      'routine_id': routineId,
      'user_id': userId,
      'name': name,
      'departure_stop': departureStop,
      'arrival_stop': arrivalStop,
      'scheduled_days': scheduledDays,
      'departure_time': departureTime,
      'notify_mins_before': notifyMinsBefore,
      'enabled': enabled,
      'exclude_holidays': excludeHolidays,
      if (origin != null) 'origin': origin!.toJson(),
      if (destination != null) 'destination': destination!.toJson(),
    };
  }
}

class RoutineExecutionModel {
  final String executionId;
  final String routineId;
  final String executionDate;
  final String status;
  final RouteResponseModel route;
  final String lastCheckedAt;


  RoutineExecutionModel({
    required this.executionId,
    required this.routineId,
    required this.executionDate,
    required this.status,
    required this.route,
    required this.lastCheckedAt,
  });

  factory RoutineExecutionModel.fromJson(Map<String, dynamic> json) {
    return RoutineExecutionModel(
      executionId: json['execution_id'] ?? '',
      routineId: json['routine_id'] ?? '',
      executionDate: json['execution_date'] ?? '',
      status: json['status'] ?? '',
      route: RouteResponseModel.fromJson(json['route'] ?? {}),
      lastCheckedAt: json['last_checked_at'] ?? '',
    );
  }

}
