class ArrivalItem {
  final String transportType;
  final String stationOrStopName;
  final String? lineName;
  final String? direction;
  final int? arrivalSeconds;
  final String? arrivalMessage;
  final String? vehicleNumber;

  ArrivalItem({
    required this.transportType,
    required this.stationOrStopName,
    this.lineName,
    this.direction,
    this.arrivalSeconds,
    this.arrivalMessage,
    this.vehicleNumber,
  });

  factory ArrivalItem.fromJson(Map<String, dynamic> json) {
    final rawArrivalSeconds = json['arrival_seconds'];
    return ArrivalItem(
      transportType: json['transport_type'] ?? 'BUS',
      stationOrStopName: json['station_or_stop_name'] ?? '',
      lineName: json['line_name'],
      direction: json['direction'],
      arrivalSeconds: rawArrivalSeconds is num
          ? rawArrivalSeconds.toInt()
          : int.tryParse(rawArrivalSeconds?.toString() ?? ''),
      arrivalMessage: json['arrival_message'],
      vehicleNumber: json['vehicle_number'],
    );
  }

  String get formattedArrival {
    final rawMessage = arrivalMessage?.trim() ?? '';
    if (rawMessage.contains('운행종료') || rawMessage.contains('운행 종료')) {
      return '도착정보없음';
    }

    if (transportType.toUpperCase() == 'SUBWAY' &&
        rawMessage.isNotEmpty) {
      final cleanMsg = rawMessage.replaceAll('전역 후', '전역');
      final stationCount = RegExp(r'\[(\d+)\].*?전역(?:\s*\(([^)]*)\))?')
          .firstMatch(cleanMsg);
      if (stationCount != null) {
        final stationName = stationCount.group(2);
        return stationName == null
            ? '${stationCount.group(1)}전역'
            : '${stationCount.group(1)}전역 ($stationName)';
      }
      if (cleanMsg.contains('전역')) {
        return cleanMsg;
      }
      if (cleanMsg.contains('도착') || cleanMsg.contains('진입')) {
        return '곧 도착';
      }
      return cleanMsg;
    }

    final secondsUntilArrival = arrivalSeconds;
    if (secondsUntilArrival != null && secondsUntilArrival > 0) {
      if (secondsUntilArrival < 60) {
        return '곧 도착';
      }

      final minutes = secondsUntilArrival ~/ 60;
      final seconds = secondsUntilArrival % 60;
      if (seconds == 0) {
        return '$minutes분 후 도착';
      }
      return '$minutes분 $seconds초 후 도착';
    }

    if (arrivalMessage != null && arrivalMessage!.isNotEmpty) {
      return arrivalMessage!.replaceAll('전역 후', '전역');
    }

    if (secondsUntilArrival == null) return '정보 없음';
    final minutes = secondsUntilArrival ~/ 60;
    final seconds = secondsUntilArrival % 60;
    if (minutes == 0) {
      return '곧 도착';
    }
    return '$minutes분 $seconds초 후 도착';
  }
}

class ArrivalResponse {
  final String provider;
  final String queriedAt;
  final List<ArrivalItem> items;

  ArrivalResponse({
    required this.provider,
    required this.queriedAt,
    required this.items,
  });

  factory ArrivalResponse.fromJson(Map<String, dynamic> json) {
    return ArrivalResponse(
      provider: json['provider'] ?? '',
      queriedAt: json['queried_at'] ?? '',
      items: (json['items'] as List<dynamic>?)
              ?.map((item) => ArrivalItem.fromJson(item))
              .toList() ??
          [],
    );
  }
}
