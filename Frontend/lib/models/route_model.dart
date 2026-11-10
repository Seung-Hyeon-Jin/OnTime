import 'arrival_model.dart';

class LocationModel {
  final String name;
  final double latitude;
  final double longitude;
  final String? cityCode;

  LocationModel({
    required this.name,
    required this.latitude,
    required this.longitude,
    this.cityCode,
  });

  factory LocationModel.fromJson(Map<String, dynamic> json) {
    return LocationModel(
      name: json['name'] ?? '',
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      cityCode: json['city_code'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'latitude': latitude,
      'longitude': longitude,
      'city_code': cityCode,
    };
  }
}

class RouteStopModel {
  final String name;
  final double latitude;
  final double longitude;
  final String odsayStationId;
  final String? stationId;
  final String? cityCode;
  final String? cityName;
  final List<ArrivalItem> arrivals;
  final String? arrivalError;

  RouteStopModel({
    required this.name,
    required this.latitude,
    required this.longitude,
    required this.odsayStationId,
    this.stationId,
    this.cityCode,
    this.cityName,
    this.arrivals = const [],
    this.arrivalError,
  });

  factory RouteStopModel.fromJson(Map<String, dynamic> json) {
    return RouteStopModel(
      name: json['name'] ?? '',
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      odsayStationId: json['odsay_station_id'] ?? '',
      stationId: json['station_id'],
      cityCode: json['city_code'],
      cityName: json['city_name'],
      arrivals: (json['arrivals'] as List<dynamic>?)
              ?.map((item) => ArrivalItem.fromJson(item))
              .toList() ??
          [],
      arrivalError: json['arrival_error'],
    );
  }
}

class RouteSegmentModel {
  final String transportType;
  final String? lineName;
  final String? departureStop;
  final String? arrivalStop;
  final int durationMinutes;
  final int? distanceMeters;
  final List<RouteStopModel> stops;

  RouteSegmentModel({
    required this.transportType,
    this.lineName,
    this.departureStop,
    this.arrivalStop,
    required this.durationMinutes,
    this.distanceMeters,
    this.stops = const [],
  });

  factory RouteSegmentModel.fromJson(Map<String, dynamic> json) {
    return RouteSegmentModel(
      transportType: json['transport_type'] ?? 'WALK',
      lineName: json['line_name'],
      departureStop: json['departure_stop'],
      arrivalStop: json['arrival_stop'],
      durationMinutes: json['duration_minutes'] ?? 0,
      distanceMeters: json['distance_meters'],
      stops: (json['stops'] as List<dynamic>?)
              ?.map((s) => RouteStopModel.fromJson(s))
              .toList() ??
          [],
    );
  }
}

class TransferDetailModel {
  final String transferStation;
  final String? previousArrivalAt;
  final int walkingSeconds;
  final String? nextVehicleArrivalAt;
  final int? waitingSeconds;
  final bool transferFeasible;

  TransferDetailModel({
    required this.transferStation,
    this.previousArrivalAt,
    required this.walkingSeconds,
    this.nextVehicleArrivalAt,
    this.waitingSeconds,
    required this.transferFeasible,
  });

  factory TransferDetailModel.fromJson(Map<String, dynamic> json) {
    return TransferDetailModel(
      transferStation: json['transfer_station'] ?? '',
      previousArrivalAt: json['previous_arrival_at'],
      walkingSeconds: json['walking_seconds'] ?? 0,
      nextVehicleArrivalAt: json['next_vehicle_arrival_at'],
      waitingSeconds: json['waiting_seconds'],
      transferFeasible: json['transfer_feasible'] ?? true,
    );
  }
}

class RouteResponseModel {
  final String provider;
  final int totalDurationMinutes;
  final int transferCount;
  final int? fare;
  final List<RouteSegmentModel> segments;
  final List<TransferDetailModel> transferDetails;
  final List<RouteResponseModel> alternatives;

  RouteResponseModel({
    required this.provider,
    required this.totalDurationMinutes,
    required this.transferCount,
    this.fare,
    this.segments = const [],
    this.transferDetails = const [],
    this.alternatives = const [],
  });

  factory RouteResponseModel.empty() {
    return RouteResponseModel(
      provider: '',
      totalDurationMinutes: 0,
      transferCount: 0,
    );
  }

  factory RouteResponseModel.fromJson(Map<String, dynamic> json) {
    return RouteResponseModel(
      provider: json['provider'] ?? '',
      totalDurationMinutes: json['total_duration_minutes'] ?? 0,
      transferCount: json['transfer_count'] ?? 0,
      fare: json['fare'],
      segments: (json['segments'] as List<dynamic>?)
              ?.map((s) => RouteSegmentModel.fromJson(s))
              .toList() ??
          [],
      transferDetails: (json['transfer_details'] as List<dynamic>?)
              ?.map((t) => TransferDetailModel.fromJson(t))
              .toList() ??
          [],
      alternatives: (json['alternatives'] as List<dynamic>?)
              ?.map((a) => RouteResponseModel.fromJson(a))
              .toList() ??
          [],
    );
  }
}
